import pygame
from enum import Enum
import random
import math
import logging
import datetime
import sys
from screeninfo import get_monitors, Monitor

SCALE = (0.5, 0.5)

class COLORS():
	BLACK = (0, 0, 0)
	WHITE = (255, 255, 255)
	GREY = (127, 127, 127)
	GRAY = GREY
	RED = (255, 0, 0)
	GREEN = (0, 255, 0)
	BLUE = (0, 0, 255)

POSITION = Enum("POSITION", ["LEFT", "RIGHT"])
PADDLE_DIRECTION = Enum("PADDLE_DIRECTION", ["UP", "DOWN", "NONE"])
WALL_COLLISION_SIDE = Enum("COLLISION_SIDE", ["VERTICALLY", "HORIZONTICALLY", "NONE"])

class Player():
	paddle_speed = 6
	paddle_width = 4
	paddle_height = 30
	def __init__(self, window: pygame.Surface, width: int, height: int, dimensions: (int, int), position: POSITION, buttons: (int, int)):
		self.window = window
		self.width = width
		self.height = height
		self.y_offset = 0
		self.dimensions = dimensions
		self.position = position
		self.buttons = buttons
		self.direction = PADDLE_DIRECTION.NONE
		self.score = 0
	
	def update(self):
		if self.direction is PADDLE_DIRECTION.UP and self.y_offset<self.dimensions[1]/2-self.paddle_height/2:
			self.y_offset += self.paddle_speed
		elif self.direction is PADDLE_DIRECTION.DOWN and -self.y_offset<self.dimensions[1]/2-self.paddle_height/2:
			self.y_offset -= self.paddle_speed

	def get_x_position(self) -> int:
		x = self.dimensions[0]/2-30
		if self.position is POSITION.LEFT:
			x *= -1
		return x

	def draw(self):
		x = self.get_x_position()

		# Begin by drawing the score
		score_font = pygame.font.SysFont('freesanbold.ttf', 50)
		score = score_font.render(str(self.score), True, COLORS.GRAY)
		self.window.blit(score, center_coords(x-self.paddle_width*2, self.dimensions[1]/2-75, self.dimensions))

		paddle = pygame.Rect(center_coords(x-self.paddle_width/2, self.y_offset+self.paddle_height/2, self.dimensions), (self.paddle_width, self.paddle_height))
		# Draw the main paddle
		pygame.draw.rect(self.window, COLORS.WHITE, paddle)
		# And 2 circles in the corners so that it is easier to understand if the ball has collided with the paddle
		pygame.draw.circle(self.window, COLORS.WHITE, center_coords(x, self.y_offset+self.paddle_height/2, self.dimensions), self.paddle_width/2)
		pygame.draw.circle(self.window, COLORS.WHITE, center_coords(x, self.y_offset-self.paddle_height/2, self.dimensions), self.paddle_width/2)

		pygame.draw.circle(self.window, COLORS.RED, center_coords(x, self.y_offset, self.dimensions), 1)
	
	def process_keydown(self, key: int):
		if key in self.buttons:
			self.direction = PADDLE_DIRECTION.UP if self.buttons.index(key) == 0 else PADDLE_DIRECTION.DOWN

	def process_keyup(self, key: int):
		if key in self.buttons:
			self.direction = PADDLE_DIRECTION.NONE


class Ball:
	ball_speed = 5
	ball_radius = 7
	accuracy = 30 # The higher the accuracy, the more accurate the collisions will be, but will take more time to compute
	def __init__(self, window: pygame.Surface, dimensions: (int, int), players: [Player]):
		self.window = window
		self.dimensions = dimensions
		self.x_offset = 0
		self.y_offset = 0
		self.angle = 0
		self.angle = random.randrange(20, 180)*random.choice([1, -1])
		self.players = players
		self.replace_self = False

	def collides_border(self) -> WALL_COLLISION_SIDE:
		if abs(self.x_offset)>=self.dimensions[0]/2-self.ball_radius:
			return WALL_COLLISION_SIDE.VERTICALLY
		elif abs(self.y_offset)>=self.dimensions[1]/2-self.ball_radius:
			return WALL_COLLISION_SIDE.HORIZONTICALLY
		else:
			return WALL_COLLISION_SIDE.NONE
	
	def collides_paddle(self) -> bool:
		for player in self.players:
			if abs(self.y_offset - player.y_offset) <= (player.paddle_height+player.paddle_width+self.ball_radius)/2 and abs(self.x_offset - player.get_x_position()) <= (player.paddle_width+self.ball_radius)/2:
				self.angle = random.randrange(20, 180)
				if player.position is POSITION.RIGHT:
					self.angle *= -1
				logging.debug(f"Collision with paddle. New angle is {self.angle}")
				return True
		return False

	def update(self):
		has_already_collided = False
		for i in range(self.accuracy):
			border_collision_status = self.collides_border()
			if border_collision_status is not WALL_COLLISION_SIDE.NONE:
				logging.debug(f"Collided with border: {border_collision_status}")
				if border_collision_status is WALL_COLLISION_SIDE.VERTICALLY:
					for player in self.players:
						if player.position is POSITION.LEFT and self.x_offset > 0:
							player.score += 1
							logging.info(f"Left score: {player.score}")
							self.replace_self = True
							return
						elif player.position is POSITION.RIGHT and self.x_offset < 0:
							player.score += 1
							logging.info(f"Right score: {player.score}")
							self.replace_self = True
							return
				elif border_collision_status is WALL_COLLISION_SIDE.HORIZONTICALLY:
					self.angle = (self.angle+90)*-1-90
			speed_x = math.sin(math.radians(self.angle))*self.ball_speed/self.accuracy
			speed_y = math.cos(math.radians(self.angle))*self.ball_speed/self.accuracy
			self.x_offset += speed_x
			self.y_offset += speed_y

			if not has_already_collided:
				has_already_collided = self.collides_paddle()

	def draw(self):
		pygame.draw.circle(self.window, COLORS.WHITE, center_coords(self.x_offset, self.y_offset, self.dimensions), self.ball_radius)
		pygame.draw.circle(self.window, COLORS.RED, center_coords(self.x_offset, self.y_offset, self.dimensions), 1)


def get_active_monitor() -> Monitor or None:
	for m in get_monitors():
		if m.is_primary:
			return m
	raise Exception("Expected at least one monitor to be primary")

def center_coords(x: int, y: int, dimensions: (int, int)) -> (int, int):
	return (x+dimensions[0]/2, -y+dimensions[1]/2)

def main():
	# initialize pygame submodules
	pygame.init()
	pygame.font.init()

	#set a basicconfig for logging
	logging.basicConfig(level=logging.DEBUG, filename=f'logs/{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.log', filemode='w',
						format='%(asctime)s - %(levelname)s - %(message)s')

	custom_handler = logging.StreamHandler(sys.stdout)
	custom_handler.setLevel(level=logging.INFO)
	logging.getLogger().addHandler(custom_handler)

	active_monitor = get_active_monitor()
	run = True
	clock = pygame.time.Clock()
	dimensions = (SCALE[0]*active_monitor.width, SCALE[1]*active_monitor.height)
	logging.info(f"Screen width: {dimensions[0]}px, screen height: {dimensions[1]}px")
	window = pygame.display.set_mode(dimensions)

	players = (
		Player(window, 4, 30, dimensions, POSITION.LEFT, (pygame.K_w, pygame.K_s)),
		Player(window, 4, 30, dimensions, POSITION.RIGHT, (pygame.K_UP, pygame.K_DOWN))
	)

	ball = Ball(window, dimensions, players)

	while run:
		clock.tick(60)
		window.fill(COLORS.BLACK)
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				run = False
			elif event.type == pygame.KEYDOWN:
				if event.key == pygame.K_q:
					run = False
				else:
					for player in players:
						player.process_keydown(event.key)
			elif event.type == pygame.KEYUP:
				for player in players:
					player.process_keyup(event.key)
		for player in players:
			player.update()
			player.draw()

		ball.update()
		if ball.replace_self:
			ball = Ball(window, dimensions, players)
		ball.draw()
		
		pygame.display.update()
	
	#when loop is interrupted, close the program
	logging.debug('Closing program...\n')
	pygame.quit()

if __name__ == "__main__":
	try:
		main()
	#if an Exception a raisen, log it
	except Exception as e:
		logging.exception('An exception has occured', exc_info=True)