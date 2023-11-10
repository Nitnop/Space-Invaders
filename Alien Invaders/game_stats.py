import pickle

class GameStats:
	"""Track statistics for Alien Invasion"""

	def __init__(self, ai_game):
		"""Initialize statistics."""
		self.settings = ai_game.settings
		self.reset_stats()
		# Start alien Invasion in an inactive state
		self.game_active = False
		#highscore should never be reset
		self.high_score = pickle.load(open("ai_saved.dat", "rb"))
	def reset_stats(self):
		"""Initalize statistics that change during the game."""
		self.ships_left = self.settings.ship_limit
		self.score = 0
		self.level = 1