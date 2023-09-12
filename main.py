#!/usr/bin/python3

import pygame
from enum import Enum
import random
import math
import logging
import datetime
import sys
import os
import typing
import argparse
from dotenv import load_dotenv

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
BUTTON_EVENT = Enum("BUTTON_EVENT", ["PRESSED", "RELEASED"])

class Player():
	PADDLE_SPEED = 6
	PADDLE_WIDTH = 5
	PADDLE_HEIGHT = 30
	def __init__(self, window: pygame.Surface, width: int, height: int, dimensions: typing.Tuple[int, int], position: POSITION, buttons: typing.Tuple[int, int]):
		# define some class variables
		self.window = window
		self.width = width
		self.height = height
		self.y_offset = 0
		self.dimensions = dimensions
		self.ratio = dimensions[0]/1000
		self.position = position
		self.buttons = buttons
		self.direction = PADDLE_DIRECTION.NONE
		self.score = 0

		# and multiple class "constants" with self.ratio
		self.paddle_speed = self.PADDLE_SPEED * self.ratio
		self.paddle_width = self.PADDLE_WIDTH * self.ratio
		self.paddle_height = self.PADDLE_HEIGHT * self.ratio
	
	def sync_dimensions(self, new_dimensions: typing.Tuple[int, int]):
		self.dimensions = new_dimensions
		self.ratio = new_dimensions[0]/1000

		self.paddle_speed = self.PADDLE_SPEED * self.ratio
		self.paddle_width = self.PADDLE_WIDTH * self.ratio
		self.paddle_height = self.PADDLE_HEIGHT * self.ratio

	def update(self, fps):
		self.paddle_speed = self.PADDLE_SPEED * 60 / fps
		if self.direction is PADDLE_DIRECTION.UP and self.y_offset<self.dimensions[1]/2-self.paddle_height/2:
			self.y_offset += self.paddle_speed
		elif self.direction is PADDLE_DIRECTION.DOWN and -self.y_offset<self.dimensions[1]/2-self.paddle_height/2:
			self.y_offset -= self.paddle_speed

	def get_x_position(self) -> int:
		x = self.dimensions[0]/2-35*self.ratio
		if self.position is POSITION.LEFT:
			x *= -1
		return x

	def draw(self):
		x = self.get_x_position()

		# Begin by drawing the score
		score_font = pygame.font.SysFont('freesanbold.ttf', round(50*self.ratio))
		score = score_font.render(str(self.score), True, COLORS.GRAY)
		self.window.blit(score, center_coords(x-self.paddle_width*2, self.dimensions[1]/2-75*self.ratio, self.dimensions))

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
	BALL_SPEED = 5
	BALL_RADIUS = 7
	accuracy = 30 # The higher the accuracy, the more accurate the collisions will be, but will take more time to compute
	def __init__(self, window: pygame.Surface, dimensions: typing.Tuple[int, int], players: typing.List[Player]):
		# define some class variables
		self.window = window
		self.dimensions = dimensions
		self.ratio = dimensions[0]/1000
		self.x_offset = 0
		self.y_offset = 0
		self.angle = 0
		self.angle = random.randrange(20, 160)*random.choice([1, -1])
		self.players = players
		self.replace_self = False
		# and multiple class "constants" with self.ratio
		self.ball_speed = self.BALL_SPEED * self.ratio
		self.ball_radius = self.BALL_RADIUS * self.ratio

	def sync_dimensions(self, new_dimensions: typing.Tuple[int, int]):
		self.dimensions = new_dimensions
		self.ratio = new_dimensions[0]/1000

		self.ball_speed = self.BALL_SPEED * self.ratio
		self.ball_radius = self.BALL_RADIUS * self.ratio

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
				self.angle = random.randrange(20, 160)
				if player.position is POSITION.RIGHT:
					self.angle *= -1
				logging.debug(f"Collision with paddle. New angle is {self.angle}")
				return True
		return False

	def update(self, fps):
		self.ball_speed = self.BALL_SPEED * 60 / fps
		has_already_collided = False

		speed_x = math.sin(math.radians(self.angle))*self.ball_speed
		speed_y = math.cos(math.radians(self.angle))*self.ball_speed
		self.x_offset += speed_x
		self.y_offset += speed_y

		border_collision_status = self.collides_border()

		if border_collision_status is not WALL_COLLISION_SIDE.NONE:
			logging.debug(f"Collided with border: {border_collision_status}")

		if border_collision_status is WALL_COLLISION_SIDE.HORIZONTICALLY:
			self.y_offset -= speed_y
			self.angle = -(self.angle+90)-90

		border_collision_status = self.collides_border()
		if border_collision_status is WALL_COLLISION_SIDE.VERTICALLY:
			for player in self.players:
				if player.position is POSITION.LEFT and self.x_offset > 0:
					player.score += 1
					logging.info(f"Right score: {player.score}")
					self.replace_self = True
					return
				elif player.position is POSITION.RIGHT and self.y_offset < 0:
					player.score += 1
					logging.info(f"Left score: {player.score}")
					self.replace_self = True
					return

		if not has_already_collided:
			has_already_collided = self.collides_paddle()


	def draw(self):
		pygame.draw.circle(self.window, COLORS.WHITE, center_coords(self.x_offset, self.y_offset, self.dimensions), self.ball_radius)
		pygame.draw.circle(self.window, COLORS.RED, center_coords(self.x_offset, self.y_offset, self.dimensions), 1)


def center_coords(x: int, y: int, dimensions: typing.Tuple[int, int]) -> typing.Tuple[int, int]:
	return (x+dimensions[0]/2, -y+dimensions[1]/2)

def main():
	# define some (local) functions
	def sync_dimensions():
		dimensions = possible_dimensions[dimension_index]
		pygame.display.set_mode(dimensions)

		for player in players:
			player.sync_dimensions(dimensions)
		ball.sync_dimensions(dimensions)
		
		if dimension_index == 0:
			pygame.display.toggle_fullscreen()
	
	def emulate_keypress(key: int, players: typing.Tuple[Player], state: BUTTON_EVENT):
		for player in players:
			if state is BUTTON_EVENT.PRESSED:
				player.process_keydown(key)
			elif state is BUTTON_EVENT.RELEASED:
				player.process_keyup(key)

	# initialize pygame submodules
	pygame.init()
	pygame.font.init()

	#set a basicconfig for logging
	logging.basicConfig(level=logging.DEBUG, filename=f'logs/{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.log', filemode='w',
						format='%(asctime)s - %(levelname)s - %(message)s')

	custom_handler = logging.StreamHandler(sys.stdout)
	custom_handler.setLevel(level=logging.INFO)
	logging.getLogger().addHandler(custom_handler)
	
	parser = argparse.ArgumentParser()
	parser.add_argument("--rpi-gpio", help="Uses some pins of the Raspberry Pi GPIO to control the paddles (only available when running on a Raspberry Pi or having Remote GPIO set up)", action="store_true")
	args = parser.parse_args()
	gpio_enabled = False
	if args.rpi_gpio:
		import gpiozero
		logging.info("Succesfully imported the \"gpiozero\" library")
		gpio_enabled = True

	run = True
	clock = pygame.time.Clock()

	possible_dimensions = pygame.display.list_modes()
	# filter the dimensions for a screen ratio of 16/9
	possible_dimensions = [*filter(lambda element: element[0]/element[1]==16/9, possible_dimensions)]
	# and set the dimensions to the highest value
	dimension_index = 0
	dimensions = possible_dimensions[dimension_index]

	logging.info(f"Screen width: {dimensions[0]}px, screen height: {dimensions[1]}px")
	window = pygame.display.set_mode(dimensions, pygame.FULLSCREEN)

	players = (
		Player(window, 4, 30, dimensions, POSITION.LEFT, (pygame.K_w, pygame.K_s)),
		Player(window, 4, 30, dimensions, POSITION.RIGHT, (pygame.K_UP, pygame.K_DOWN))
	)
	
	load_dotenv()

	if gpio_enabled:
		left_up_button = gpiozero.Button(os.getenv('LEFT_UP', "22"))
		left_up_button.when_pressed = lambda: emulate_keypress(pygame.K_w, players, BUTTON_EVENT.PRESSED)
		left_up_button.when_released = lambda: emulate_keypress(pygame.K_w, players, BUTTON_EVENT.RELEASED)
		
		left_bottom_button = gpiozero.Button(os.getenv('LEFT_DOWN', "24"))
		left_bottom_button.when_pressed = lambda: emulate_keypress(pygame.K_s, players, BUTTON_EVENT.PRESSED)
		left_bottom_button.when_released = lambda: emulate_keypress(pygame.K_s, players, BUTTON_EVENT.RELEASED)
		
		right_up_button = gpiozero.Button(os.getenv('RIGHT_UP', "27"))
		right_up_button.when_pressed = lambda: emulate_keypress(pygame.K_UP, players, BUTTON_EVENT.PRESSED)
		right_up_button.when_released = lambda: emulate_keypress(pygame.K_UP, players, BUTTON_EVENT.RELEASED)
		
		right_bottom_button = gpiozero.Button(os.getenv('RIGHT_DOWN', "23"))
		right_bottom_button.when_pressed = lambda: emulate_keypress(pygame.K_DOWN, players, BUTTON_EVENT.PRESSED)
		right_bottom_button.when_released = lambda: emulate_keypress(pygame.K_DOWN, players, BUTTON_EVENT.RELEASED)
	

	ball = Ball(window, dimensions, players)

	while run:
		clock.tick(60)
		last_fps = clock.get_fps() if clock.get_fps() != 0 else 30
		window.fill(COLORS.BLACK)
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				run = False
			elif event.type == pygame.KEYDOWN:
				if event.key == pygame.K_q:
					run = False
				elif event.key == pygame.K_MINUS or event.key == pygame.K_MINUS:
					if dimension_index != len(possible_dimensions)-1:
						dimension_index += 1
						sync_dimensions()
				elif event.key == pygame.K_PLUS or event.key == pygame.K_KP_PLUS or (event.key == pygame.K_EQUALS and pygame.key.get_mods() & pygame.KMOD_SHIFT):
					if dimension_index != 0:
						dimension_index -= 1
						sync_dimensions()
				else:
					for player in players:
						player.process_keydown(event.key)
			elif event.type == pygame.KEYUP:
				for player in players:
					player.process_keyup(event.key)
		for player in players:
			player.update(last_fps)
			player.draw()

		ball.update(last_fps)
		if ball.replace_self:
			ball = Ball(window, possible_dimensions[dimension_index], players)
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
