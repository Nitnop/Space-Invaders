import sys
import pickle
from time import sleep

import pygame

from settings import Settings
from game_stats import GameStats
from scoreboard import Scoreboard
from button import Button
from ship import Ship
from bullet import Bullet
from alien import Alien

class AlienInvasion:
	"""Overall class to manage game assets and behavior."""

	def __init__(self):
		"""Initialize the game, and create game resourses."""
		pygame.init()
		self.settings = Settings()

		self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
		self.settings.screen_width = self.screen.get_rect().width
		self.settings.screen_height = self.screen.get_rect().height
		pygame.display.set_caption("Alien Invasion")

		# Create an instance to store game statistics and create a scoreboard
		self.stats = GameStats(self)
		self.sb = Scoreboard(self)

		self.ship = Ship(self)
		self.bullets = pygame.sprite.Group()
		self.aliens = pygame.sprite.Group()

		self. _create_fleet()

		# Make the play button
		self.play_button = Button(self, "Play")

		# Set the backround color.
		self.bg_color = (230, 230, 230)

	def run_game(self):
		"""Start the main loop for the game."""
		while True:
			self._check_events()
			if self.stats.game_active:
				self.ship.update()
				self._update_bullets()
				self._update_aliens()
			
			self._update_screen()

	def _check_events(self):
		"""Respond to keypresses and mouse events."""
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				sys.exit()
			elif event.type == pygame.KEYDOWN:
				self._check_keydown_events(event)
			elif event.type == pygame.KEYUP: #Stop the ship
				self._check_keyup_events(event)
			elif event.type == pygame.MOUSEBUTTONDOWN:
				mouse_pos = pygame.mouse.get_pos()
				self._check_play_button(mouse_pos)

	def _check_play_button(self, mouse_pos):
		"""Start new game when the player clicks Play"""
		button_clicked = self.play_button.rect.collidepoint(mouse_pos)
		if button_clicked and not self.stats.game_active:
			self._start_game()

	def _start_game(self):
		"""everything needed to start a new game"""
		# Hide mouse cursor.
		pygame.mouse.set_visible(False)

		# Reset the game stats
		self.stats.reset_stats()
		self.settings.initialize_dynamic_settings()
		self.sb.prep_score()
		self.stats.game_active = True
		self.sb.prep_level()
		self.sb.prep_ships()

		# Reset screen
		self.aliens.empty()
		self.bullets.empty()

		 #create new fleet
		self._create_fleet()
		self.ship.center_ship()
		
	def _check_keydown_events(self, event):
		"""respond to keypress"""
		if event.key == pygame.K_RIGHT: #Move the ship to the right
			self.ship.moving_right = True
		if event.key == pygame.K_LEFT: #Move the ship to the left
			self.ship.moving_left = True
		if event.key == pygame.K_q:
			pickle.dump(self.stats.high_score, open("ai_saved.dat", "wb"))
			sys.exit()
		if event.key == pygame.K_SPACE:
			self._fire_bullet()
		if event.key == pygame.K_p:
			if not self.stats.game_active:
				self._start_game()

	def _check_keyup_events(self, event):
		"""respond to key release"""
		if event.key == pygame.K_RIGHT:
			self.ship.moving_right = False
		if event.key == pygame.K_LEFT:
			self.ship.moving_left = False

	def _fire_bullet(self):
		"""Create a new bullet and add it to the bullets group."""
		if len(self.bullets) < self.settings.bullets_allowed:
			new_bullet = Bullet(self)
			self.bullets.add(new_bullet)

	def _update_bullets(self):
		"""Update position of bullets and get rid of old bullets."""
		#Update bullet positions
		self.bullets.update()
		#Delete old bullets
		for bullet in self.bullets.copy():
			if bullet.rect.bottom <=0:
				self.bullets.remove(bullet)
		self._check_bullet_alien_collisions()

	def _check_bullet_alien_collisions(self):
		"""Respond to bullet alien collisions."""
		#Remove any bullets and aliens that collide
		collisions = pygame.sprite.groupcollide(self.bullets, self.aliens, True, True)
		if not self.aliens:
			# Destroy existing bullets and create new fleet
			self.bullets.empty()
			self._create_fleet()
			self.settings.increase_speed()
			# Level up
			self.stats.level += 1
			self.sb.prep_level()
		if collisions:
			for aliens in collisions.values():
				self.stats.score += self.settings.alien_points * len(aliens)
			self.sb.prep_score()
			self.sb.check_high_score()

	def _update_aliens(self):
		"""update the position of all the aliens in the fleet"""
		self._check_fleet_edges()
		self.aliens.update()
		# Look for alien-shp collisions.
		if pygame.sprite.spritecollideany(self.ship, self.aliens):
			self._ship_hit()

		# Look for aliens hitting the bottm of the screen
		self._check_aliens_bottom()

	def _ship_hit(self):
		"""Respond to the ship being hit by and alien."""
		if self.stats.ships_left > 0:
			# Lose a life. remove ship from screen
			self.stats.ships_left -= 1
			self.sb.prep_ships()
			# Clear screen and prepfor new fleet
			self.aliens.empty()
			self.bullets.empty()
			# Create new fleet and recenter.
			self._create_fleet()
			self.ship.center_ship()

			# Pause
			sleep(1.0)
		else:
			self.stats.game_active = False
			pygame.mouse.set_visible(True)

	def _check_fleet_edges(self):
		"""Respond appropriately if an aliens have reached an edge"""
		for alien in self.aliens.sprites():
			if alien.check_edges():
				self._change_fleet_direction()
				break

	def _change_fleet_direction(self):
		"""Drop the entire fleet and change direction"""
		for alien in self.aliens.sprites():
			alien.rect.y += self.settings.fleet_drop_speed
		self.settings.fleet_direction *= -1

	def _create_fleet(self):
		"""create the fleet of aliens"""
		#make an alien
		alien = Alien(self)
		alien_width, alien_height = alien.rect.size
		alien_width = alien.rect.width
		available_space_x = self.settings.screen_width - (2 * alien_width)
		number_aliens_x = available_space_x // (2 * alien_width)
		#determine the number of rows that will fit on a screen
		ship_height = self.ship.rect.height
		available_space_y = (self.settings.screen_height - (3 * alien_height) - ship_height)
		number_rows = available_space_y // (2 * alien_height)

		# Create the full fleet of aliens
		for row_number in range(number_rows):
			for alien_number in range(number_aliens_x):
				self._create_alien(alien_number, row_number)

	def _create_alien(self, alien_number, row_number):
		"""create and alien and place it in the row"""
		alien = Alien(self)
		alien_width, alien_height = alien.rect.size
		alien.x = alien_width + 2 * alien_width * alien_number
		alien.rect.x = alien.x
		alien.rect.y = alien.rect.height + 2 * alien.rect.height * row_number
		self.aliens.add(alien)

	def _check_aliens_bottom(self):
		"""check if any aliens have reached the bottom of the screen."""
		screen_rect = self.screen.get_rect()
		for alien in self.aliens.sprites():
			if alien.rect.bottom >= screen_rect.bottom:
				# Treat this the same as ship got hit
				self._ship_hit()
				break
	def _update_screen(self):		
		"""update images on the screen, and flip to the new screen."""
		self.screen.fill(self.settings.bg_color)
		self.ship.blitme()
		for bullet in self.bullets.sprites():
			bullet.draw_bullet()
		self.aliens.draw(self.screen)
		#Draw the score information
		self.sb.show_score()

		# Draw Play button if the game is inactive
		if not self.stats.game_active:
			self.play_button.draw_button()
		
		pygame.display.flip()

if __name__ == '__main__':
	# Make a game instance, and run the game
	ai = AlienInvasion()
	ai.run_game()
	