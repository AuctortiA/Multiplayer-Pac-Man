__author__ = 'Will Evans'

import os
import pygame as pg
from datastructures import Maze
from sprites import *
from time import sleep
import local_database
import threading
import local_settings
import gui


class Classic:
    def __init__(self, win, win_scale, user_id):
        """
        Controls the running of each level and database queries.
        :param win: The current window, all objects must be blitted to this window to be displayed.
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables).
        :param user_id: UserID if the user has signed in (they don't have to be signed in to play Classic).
        """

        # Essential
        self.win_scale = win_scale
        self.win = win
        self.program = 'Classic'
        self.user_id = user_id
        self.error_message = None
        self.game_finished = False

        # Music
        intro_music_channel = pg.mixer.Channel(7)
        intro_music_channel.set_volume(0.5 * local_settings.get_setting('game_volume')/100)
        intro_music_channel.play(pg.mixer.Sound('Resources\\sounds\\intro_music.wav'))

        # Highscore
        self.highscore = local_database.get_highscore()
        if self.highscore is None:
            self.highscore = 0

        # Maze
        self.maze_id = 1

        # Variables
        self.score = 0
        self.pellets_eaten = 0
        self.level_num = 1
        self.lives = 3

        #   Database
        self.game_id = local_database.get_game_id(self.user_id, self.maze_id)

        # Level Info
        self.level_num = 1
        self.extra_life_claimed = False

        # Level
        self.level = Level(
                            self.win_scale,
                            self.game_id, 1,
                            self.maze_id,
                            [],
                            [],
                            self.lives,
                            self.score,
                            self.highscore,
                            start_cap=4
                         )
        # Initials Input Box
        self.initials_input_box = gui.TransparentInputBox(100, 30, 20, win_scale, 'Initials')
        self.word_1 = gui.Word('Enter 3 initials', (168, 180), (255, 255, 30), 20, win_scale, centre=True)
        self.word_2 = gui.Word('to save highscore', (168, 195), (255, 255, 30), 20, win_scale, centre=True)

    def run(self, win, events):
        """
        This method is run directly from the main script.
        :param win: The current window, all objects must be blitted to this window to be displayed.
        :param events: Contains events from the pg.event.get() call containing all keyboard events.
        :return: None
        """

        # Essential
        self.level.run(win, events)  # bool -: True if level won, false if pac-man dead and None if neither

        # Variables
        self.score = self.level.score
        self.pellets_eaten = self.level.pellets_eaten
        self.lives = self.level.lives

        self.extra_life_claimed = self.level.extra_life_claimed

        # Events
        for event in events:
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    self.program = 'StartScreen'

        # If all the pellets have been eaten
        if self.level.finished and self.level.won:
            self.level_num += 1
            self.level.quit()
            self.level = Level(
                               self.win_scale,
                               self.game_id,
                               self.level_num,
                               self.maze_id,
                               [],
                               [],
                               self.lives,
                               self.score,
                               self.highscore,
                               extra_life_claimed=self.extra_life_claimed
                               )

        # If Pac-Man has died, but he still has lives
        elif self.level.finished and self.lives > 1:
            self.lives -= 1
            self.score = self.level.score
            self.level.quit()
            self.level = Level(
                                self.win_scale,
                                self.game_id,
                                self.level_num,
                                self.maze_id,
                                self.level.pellets,
                                self.level.power_pellets,
                                self.lives,
                                self.score,
                                self.highscore,
                                extra_life_claimed=self.extra_life_claimed
                                )

        elif self.lives == 0 and self.level.finished and not self.game_finished:
            self.level.quit()
            self.game_finished = True

        if self.game_finished:
            for event in events:
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_RETURN:
                        local_database.save_initials(self.game_id, self.initials_input_box.get_input())
                        self.program = 'Highscores'

            self.initials_input_box.update(events)
            self.initials_input_box.display(win)
            self.word_1.display(win)
            self.word_2.display(win)

    def get_program(self):
        return self.program

    def get_error(self):
        return self.error_message

    def quit(self):
        pg.mixer.music.stop()
        self.level.quit()


class Level:
    def __init__(self, win_scale, game_id, level_num, maze_id, pellets, power_pellets, lives, score, highscore,
                 start_cap=2, extra_life_claimed=False):
        """
        Responsible for storing information about sprite objects. The class stores other things, such as score, maze
        etc.
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables).
        :type win_scale: Integer.
        :param game_id: GameID given to the game by the database.
        :type game_id: Integer.
        :param level_num: This controls difficulty of the ghosts. The larger the level number, the more levels Pac-Man
        has completed and the harder the ghosts become.
        :type level_num: Integer.
        :param maze_id: ID given to each maze. This can be used by the database to return the 2D list associated with
        the ID.
        :type maze_id: Integer.
        :param pellets: A list of pellets. This is if Pac-Man dies and the level starts over. The pellets must be the
        same as the previous level instance so they are saved by the classic class.
        :type pellets: List.
        :param power_pellets: A list of power pellets. This is if Pac-Man dies and the level starts over. The power
        pellets must be the same as the previous level instance so they are saved by the classic class.
        :type power_pellets: List.
        :param lives: Number of lives remaining.
        :type lives: Integer.
        :param score: Current score that should be displayed at the top.
        :type score: Integer.
        :param highscore: Highscore that should be displayed at the top.
        :type highscore: Integer.
        :param start_cap: How long the level should wait to start.
        :type start_cap: Integer.
        :param extra_life_claimed: Whether or not the extra life has been given to the player.
        :type extra_life_claimed: Boolean.
        """

        # Essential
        self._run = True
        self.win_scale = win_scale
        self.program = 'Classic'
        self.finished = False
        self.won = False

        # Variables
        #   Level
        self.score = score
        self.highscore = highscore

        self.game_maze = Maze(maze_id, win_scale)

        self.lives = lives

        self.start_cap = start_cap

        self.extra_life_claimed = extra_life_claimed

        #   Database
        self.level_num = level_num
        self.game_id = game_id
        self.level_score = 0
        self.length = 0
        self.pellets_eaten = 0
        self.power_pellets_eaten = 0
        self.ghosts_eaten = 0

        # Length counting thread
        threading.Thread(target=self.second_count).start()

        # Indicators
        self.one_up = gui.Word('1UP', (6 * 12, 0.8 * 12), (234, 234, 234), 24, win_scale)
        self.score_position = (7 * 12, 2 * 12)
        self.score_indicator = gui.Word('{}'.format(self.score), self.score_position, (234, 234, 234), 24, win_scale)

        self.highscore_text_position = (19 * 12, 0.8 * 12)
        self.highscore_position = (17 * 12, 2 * 12)

        self.highscore_text = gui.Word('high score', self.highscore_text_position, (234, 234, 234), 24, win_scale)

        if self.score > self.highscore:
            self.highscore_indicator = gui.Word('{}'.format(self.score),
                                                 self.highscore_position,
                                                 (234, 234, 234),
                                                 24,
                                                 win_scale
                                                 )
        else:
            self.highscore_indicator = gui.Word('{}'.format(self.highscore),
                                                 self.highscore_position,
                                                 (234, 234, 234),
                                                 24,
                                                 win_scale
                                                 )

        self.life_indicators = []
        skin = pg.transform.scale(pg.image.load('Resources\\sprites\\pac-man\\w_0.png'),
                                  (22 * win_scale, 22 * win_scale))

        for num in range(lives - 1):
            rect = skin.get_rect(center=((num * 24 * win_scale + 18 * win_scale), (35 * 12 * win_scale)))
            self.life_indicators.append(StaticSprite([skin], rect))

        # Start and ready text
        self.ready_text = gui.Word('ready!', (17.5 * 12, 20.5 * 12), (255, 255, 30), 23, win_scale, italic=True)
        self.game_over_text = gui.Word('game over', (18 * 12, 20.5 * 12), (255, 0, 0), 21, win_scale)

        # Points (displayed when Pac-Man eats a ghost).
        self.points_text = {}
        for text in os.listdir('Resources\\sprites\\{}'.format('points')):
            # noinspection PyUnresolvedReferences
            self.points_text.update({text: pg.transform.scale(
                pg.image.load('Resources\\sprites\\{}\\{}'.format('points', text)),
                ((24 * win_scale), (10 * win_scale)))})

        # Pac-Man
        self.pac_man = PacMan('pac-man', self.game_maze, win_scale)

        # Ghosts
        self.ghosts = []
        self.ghosts_copy = self.ghosts[::]
        blinky = Blinky('blinky', self.pac_man, self.game_maze, win_scale, level_num)
        self.ghosts.append(blinky)
        self.ghosts.append(Pinky('pinky', self.pac_man, self.game_maze, win_scale, level_num))
        self.ghosts.append(Clyde('clyde', self.pac_man, self.game_maze, win_scale, level_num))
        self.ghosts.append(Inky('inky', self.pac_man, self.game_maze, win_scale, level_num, blinky))

        # Pellets
        self.pellets = pellets
        self.power_pellets = power_pellets

        if pellets == [] and power_pellets == []:
            pellet_skin_path = os.path.join('Resources', 'sprites', 'pellets', 'pellet.png')
            pellet_skin = pg.transform.scale(pg.image.load(pellet_skin_path), (4 * win_scale, 4 * win_scale))

            power_pellet_skin_path = os.path.join('Resources', 'sprites', 'pellets', 'power_pellet.png')
            power_pellet_skin = pg.transform.scale(pg.image.load(power_pellet_skin_path),
                                                   (12 * win_scale, 12 * win_scale))

            pellet_sound_channel = pg.mixer.Channel(2)
            pellet_sound_channel.set_volume(0.5 * (local_settings.get_setting('game_volume') / 100))

            power_pellet_death_sound_path = os.path.join('Resources', 'sounds', 'pellet', 'death.wav')
            pellet_death_sound = pg.mixer.Sound(power_pellet_death_sound_path)

            for row in self.game_maze.tiles:
                for tile in row:
                    if tile.type == 'pellet':
                        self.pellets.append(Pellet(pellet_skin,
                                                   tile,
                                                   self.pac_man,
                                                   win_scale,
                                                   pellet_death_sound,
                                                   pellet_sound_channel)
                                            )

                    elif tile.type == 'power_pellet':
                        self.power_pellets.append(Pellet(power_pellet_skin,
                                                         tile,
                                                         self.pac_man,
                                                         win_scale,
                                                         pellet_death_sound,
                                                         pellet_sound_channel,
                                                         power_pellet=True)
                                                  )
        else:
            for pellet in self.pellets:
                pellet.predator = self.pac_man
            for power_pellet in self.power_pellets:
                power_pellet.predator = self.pac_man

        # Sound
        self.large_pellet_channel = pg.mixer.Channel(3)
        self.large_pellet_channel.set_volume(0.5 * (local_settings.get_setting('game_volume') / 100))

        large_pellet_sound_path = os.path.join('Resources', 'sounds', 'large_pellet_loop.wav')
        self.large_pellet_sound = pg.mixer.Sound(large_pellet_sound_path)

        self.death_sound_playing = False
        self.started = False

        # Clocks and counts
        self.start_clock = 0
        self.one_up_clock = 0
        self.flashing_map_clock = 0
        self.flashing_map_count = 0

    def run(self, win, events):
        """
        Responsible for running each level by calling sprite objects and handling their updates.
        The class also controls other things, such as score, displaying maze etc.
        :param win: The current window, all objects must be blitted to this window to be displayed.
        :type win: Surface.
        :param events: Contains events from the pg.event.get() call containing all keyboard events.
        :type events: Tuple.
        :return: Boolean returns True if level is won, False if level is lost, None otherwise
        """

        # Before the game starts (music)
        if self.start_clock < self.start_cap:
            self.start_clock += 1 / 60
            self.one_up.display(win)
            self.score_indicator.display(win)
            self.highscore_text.display(win)
            self.highscore_indicator.display(win)
            self.game_maze.display(win)

            self.ready_text.display(win)
            for pellet in self.pellets:
                pellet.display(win)
            for power_pellet in self.power_pellets:
                power_pellet.display(win)
            for life_indicator in self.life_indicators:
                life_indicator.display(win)
            for ghost in self.ghosts:
                ghost.display(win)
            self.pac_man.display(win)

        # If there are no pellets the maze will flash
        elif len(self.pellets) == 0:
            self.flashing_map_clock += 1/60
            if self.flashing_map_clock > 0.25:
                self.flashing_map_clock = 0
                self.flashing_map_count += 1
                self.game_maze.change_skin()
            if self.flashing_map_count == 7:
                self.finished = True
                self.won = True

            self.game_maze.display(win)

            self.one_up.display(win)
            self.score_indicator.display(win)
            self.highscore_text.display(win)
            self.highscore_indicator.display(win)
            for life_indicator in self.life_indicators:
                life_indicator.display(win)
            self.pac_man.display(win)

        # Mainloop of the level
        else:
            # Score Indicators
            #   Controls flashing of one up
            self.one_up_clock += 1 / 60
            if 0.4 > self.one_up_clock > 0.2:
                self.one_up.display(win)
            elif 0.4 < self.one_up_clock:
                self.one_up_clock = 0

            self.score_indicator = gui.Word('{}'.format(self.score),
                                             self.score_position,
                                             (234, 234, 234),
                                             24,
                                             self.win_scale
                                             )

            self.score_indicator.display(win)
            if self.score > self.highscore:
                self.highscore_indicator = gui.Word('{}'.format(self.score),
                                                     self.highscore_position,
                                                     (234, 234, 234),
                                                     24,
                                                     self.win_scale)

            if not self.extra_life_claimed:
                if self.score > 10000:
                    self.lives += 1
                    skin = pg.transform.scale(pg.image.load('Resources\\sprites\\pac-man\\w_0.png'),
                                              (22 * self.win_scale, 22 * self.win_scale))
                    for num in range(self.lives - 1):
                        rect = skin.get_rect(center=(
                                                    (num * 24 * self.win_scale + 18 * self.win_scale),
                                                    (35 * 12 * self.win_scale)
                                                     )
                                             )

                        self.life_indicators.append(StaticSprite([skin], rect))
                    self.extra_life_claimed = True

            self.highscore_text.display(win)
            self.highscore_indicator.display(win)

            #   Life indicators
            for life_indicator in self.life_indicators:
                life_indicator.display(win)

            # Maze
            self.game_maze.display(win)
            self.game_maze.display(win)

            # Pellets
            for pellet in self.pellets:
                pellet.update()
                pellet.display(win)
                if pellet.eaten:
                    self.score += 10
                    self.level_score += 10
                    self.pellets_eaten += 1
                    self.pellets.remove(pellet)

            #  Power pellets
            for power_pellet in self.power_pellets:
                power_pellet.update()
                power_pellet.display(win)
                if power_pellet.eaten:
                    self.score += 50
                    self.level_score += 50
                    self.power_pellets_eaten += 1
                    if not self.large_pellet_channel.get_busy():
                        self.large_pellet_channel.play(self.large_pellet_sound, loops=-1)
                    for ghost in self.ghosts:
                        ghost.scare()
                        self.ghosts_copy = [ghost for ghost in self.ghosts if not ghost.dead]
                    self.power_pellets.remove(power_pellet)

            # Pac-Man
            self.pac_man.update(events)
            self.pac_man.display(win)

            # Checks whether the level has ended
            if self.pac_man.dead:
                if self.death_sound_playing:
                    pass
                else:
                    pg.mixer.stop()
                    self.death_sound_playing = True

            if self.pac_man.death_animation_finished and not self.finished:
                self.finished = True
                if self.lives == 1:
                    self.lives -= 1
                    self.game_over_text.display(win)
                    pg.display.update()
                    sleep(2)

            # Ghosts
            if all([not ghost.scared for ghost in self.ghosts]):
                self.large_pellet_channel.stop()

            for ghost in self.ghosts_copy:

                if ghost.dead:
                    self.ghosts_eaten += 1
                    self.ghosts_copy.remove(ghost)
                    for ghost_ in self.ghosts_copy:
                        ghost_.display(win)
                    points = 200 * 2 ** ((len(self.ghosts) - 1) - len(self.ghosts_copy))
                    self.score += points
                    self.level_score += points

                    win.blit(self.points_text['{}.png'.format(str(points))],
                             (self.pac_man.x, self.pac_man.y - 8 * self.win_scale))
                    pg.display.update()
                    sleep(1)

            if not self.pac_man.dead:
                for ghost in self.ghosts:
                    if ghost.__class__.__name__ == 'Blinky':
                        if len(self.pellets) < 20 + 2 * self.level_num:
                            ghost.make_elroy()
                        if len(self.pellets) < 10 + 2 * self.level_num:
                            ghost.elroy_upgrade()

                    ghost.update(events)
                    ghost.display(win)

    def quit(self):
        """
        Quits the level. Stops music playing and saves that level to the databse.
        :return: None
        """

        local_database.save_level(
                                    self.level_num,
                                    self.game_id,
                                    self.lives,
                                    self.level_score,
                                    self.length,
                                    self.pellets_eaten,
                                    self.power_pellets_eaten,
                                    self.ghosts_eaten
                                )

        self._run = False
        pg.mixer.stop()

    def second_count(self):
        """
        Counts seconds, so that the time can be recorded in the database.
        :return: None
        """

        while self._run:
            sleep(1)
            self.length += 1
