__author__ = 'Will Evans'

import pygame as pg
import threading
import os
import gui
import sprites
import datastructures
import local_database
import local_settings
from time import sleep
import json


class Story:
    def __init__(self, win, win_scale, user_id):
        """
        Controls the running of each level and database queries.
        :param win: The current window, all objects must be blitted to this window to be displayed.
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables).
        :param user_id: UserID if the user has signed in (they don't have to be signed in to play Classic).
        """

        # Essential
        self.win_scale = win_scale
        self.program = 'Story'
        self.user_id = user_id
        self.error_message = None
        self.game_finished = False
        self.win = win

        # Maze
        self.maze_id = 1

        # Variables
        self.score = 0

        #   Database
        self.game_id = local_database.get_game_id(self.user_id, self.maze_id)
        self.pellets_eaten = 0

        # Level Info
        self.level_num = 2

        # Tutorial Messages

        tutorial_prompts_file_path = os.path.join('data', 'tutorial.json')
        with open(tutorial_prompts_file_path, 'r') as file:
            self.tutorial_prompts = json.load(file)

        # Boxes for the first level
        self.tutorial_boxes = []
        for prompt in self.tutorial_prompts[str(self.level_num)]:
            self.tutorial_boxes.append(gui.TutorialTextBox(prompt, (255, 255, 30), win_scale, add_mspacman=True))
        # Level
        self.level_names = {

                             1:    Level1,
                             2:    Level2,
                             3:    Level3,
                             4:    Level4,
                             5:    Level5,
                             6:    Level6,

                        }

        self.level = self.level_names[self.level_num](
                            self.win_scale,
                            self.game_id, self.level_num,
                            self.maze_id,
                            [],
                            [],
                            self.score,
                            self.tutorial_boxes,
                        )

    def run(self, win, events):
        """
        This method is run directly from the main script.
        :param win: The current window, all objects must be blitted to this window to be displayed.
        :param events: Contains events from the pg.event.get() call containing all keyboard events.
        :return: None
        """

        # Essential
        self.level.run(win, events)

        # Variables
        self.score = self.level.score
        self.pellets_eaten = self.level.pellets_eaten

        # Events
        for event in events:
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    self.program = 'StartScreen'

        # If all the pellets have been eaten
        if self.level.finished and self.level.won:
            self.level_num += 1
            self.level.quit()

            # Tutorial Messages
            self.tutorial_boxes = []
            for prompt in self.tutorial_prompts[str(self.level_num)]:
                self.tutorial_boxes.append(gui.TutorialTextBox(prompt,
                                                                (255, 255, 30),
                                                                self.win_scale,
                                                                add_mspacman=True)
                                           )

            self.level = self.level_names[self.level_num](
                               self.win_scale,
                               self.game_id,
                               self.level_num,
                               self.maze_id,
                               [],
                               [],
                               self.score,
                               self.tutorial_boxes,
                            )

        # If Pac-Man has died
        elif self.level.finished:
            self.score = self.level.score
            self.tutorial_boxes = self.level.tutorial_boxes
            self.level.quit()

            self.level = self.level_names[self.level_num](
                                self.win_scale,
                                self.game_id,
                                self.level_num,
                                self.maze_id,
                                self.level.pellets,
                                self.level.power_pellets,
                                self.score,
                                self.tutorial_boxes,
                            )

    def get_program(self):
        return self.program

    def get_error(self):
        return self.error_message

    def quit(self):
        self.level.quit()
        pg.mixer.music.stop()


class Level:
    def __init__(self, win_scale, game_id, level_num, maze_id, pellets, power_pellets, score, tutorial_boxes):
        """
        Responsible for running each level by calling sprite objects and handling their updates. The class
        also controls other things, such as score, displaying maze etc.
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
        :param score: Current score that should be displayed at the top.
        :type score: Integer.
        """

        # Essential
        self._run = True
        self.win_scale = win_scale
        self.program = 'Story'
        self.finished = False
        self.won = False
        self.start = False

        # Variables
        #   Level
        self.score = score

        self.game_maze = datastructures.Maze(maze_id, win_scale)

        #   Database
        self.level_num = level_num
        self.game_id = game_id
        self.level_score = 0
        self.length = 0
        self.pellets_eaten = 0
        self.power_pellets_eaten = 0
        self.ghosts_eaten = 0

        # Tutorial Variables
        #   Messages
        self.tutorial_boxes = tutorial_boxes
        self.paused = False

        #   Paths
        self.show_paths = False

        # Length counting thread
        threading.Thread(target=self.second_count).start()

        # Indicators
        self.score_position = (7 * 12, 2 * 12)
        self.score_indicator = gui.Word('{}'.format(self.score), self.score_position, (234, 234, 234), 24, win_scale)

        # Start and ready text
        self.ready_text = gui.Word('ready!', (17.5 * 12, 20.5 * 12), (255, 255, 30), 23, win_scale, italic=True)
        self.game_over_text = gui.Word('game over', (18 * 12, 20.5 * 12), (255, 0, 0), 21, win_scale)

        # Points (displayed when Pac-Man eats a ghost).
        self.points_texts = {}
        for point_text in os.listdir(os.path.join('Resources', 'sprites', 'points')):
            # noinspection PyUnresolvedReferences
            self.points_texts.update({point_text: pg.transform.scale(
                pg.image.load(
                    os.path.join('Resources', 'sprites', 'points', point_text)),
                    (
                        (24 * win_scale), (10 * win_scale)
                    )
                            )
            })

        # Pac-Man
        self.pac_man = sprites.PacMan('pac-man', self.game_maze, win_scale)

        # Ghosts
        self.ghosts = []
        self.ghosts_copy = self.ghosts[::]
        blinky = sprites.Blinky('blinky', self.pac_man, self.game_maze, win_scale, level_num)
        pinky = sprites.Pinky('pinky', self.pac_man, self.game_maze, win_scale, level_num)
        clyde = sprites.Clyde('clyde', self.pac_man, self.game_maze, win_scale, level_num)
        inky = sprites.Inky('inky', self.pac_man, self.game_maze, win_scale, level_num, blinky)

        if level_num == 1:
            pass
        elif level_num == 2:
            self.ghosts.append(clyde)
        elif level_num == 3:
            self.ghosts.append(pinky)
        elif level_num == 4:
            self.ghosts.append(blinky)
        elif level_num == 5:
            self.ghosts.append(blinky)
            self.ghosts.append(inky)
        elif level_num == 6:
            self.ghosts.append(blinky)
            self.ghosts.append(inky)
        else:
            self.ghosts.append(blinky)
            self.ghosts.append(pinky)
            self.ghosts.append(inky)
            self.ghosts.append(clyde)

        # Pellets
        self.pellets = pellets
        self.power_pellets = power_pellets

        if pellets == [] and power_pellets == []:
            pellet_skin_path = os.path.join('Resources', 'sprites', 'pellets', 'pellet.png')
            pellet_skin = pg.transform.scale(pg.image.load(pellet_skin_path), (4 * win_scale, 4 * win_scale))
            power_pellet_skin_path = os.path.join('Resources', 'sprites', 'pellets', 'power_pellet.png')
            power_pellet_skin = pg.transform.scale(pg.image.load(power_pellet_skin_path),
                                                   (12 * win_scale, 12 * win_scale)
                                                   )

            pellet_sound_channel = pg.mixer.Channel(2)
            pellet_sound_channel.set_volume(0.5 * (local_settings.get_setting('game_volume')/100))

            power_pellet_death_sound_path = os.path.join('Resources', 'sounds', 'pellet', 'death.wav')
            pellet_death_sound = pg.mixer.Sound(power_pellet_death_sound_path)

            for row in self.game_maze.tiles:
                for tile in row:
                    if tile.type == 'pellet':
                        self.pellets.append(sprites.Pellet(pellet_skin,
                                                           tile,
                                                           self.pac_man,
                                                           win_scale,
                                                           pellet_death_sound,
                                                           pellet_sound_channel)
                                            )

                    elif tile.type == 'power_pellet':
                        if level_num >= 5:
                            self.power_pellets.append(sprites.Pellet(power_pellet_skin,
                                                                     tile,
                                                                     self.pac_man,
                                                                     win_scale,
                                                                     pellet_death_sound,
                                                                     pellet_sound_channel,
                                                                     power_pellet=True)
                                                      )

                        else:
                            self.pellets.append(sprites.Pellet(pellet_skin,
                                                               tile,
                                                               self.pac_man,
                                                               win_scale,
                                                               pellet_death_sound,
                                                               pellet_sound_channel)
                                                )

        else:
            for pellet in self.pellets:
                pellet.predator = self.pac_man
            for power_pellet in self.power_pellets:
                power_pellet.predator = self.pac_man

        # Sound
        self.large_pellet_channel = pg.mixer.Channel(3)
        self.large_pellet_channel.set_volume(0.5 * (local_settings.get_setting('game_volume')/100))
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
        This method is run from the Tutorial class and updates and displays by one frame.
        :param win: The current window, all objects must be blitted to this window to be displayed.
        :type win: Surface.
        :param events: Contains events from the pg.event.get() call containing all keyboard events.
        :type events: Tuple.
        :return: Boolean returns True if level is won, False if level is lost, None otherwise
        """

        # Change to make sure there is a delay when there are no text boxes.
        if not self.start:

            # Score Indicators
            self.score_indicator.display(win)

            # Maze
            self.game_maze.display(win)

            self.ready_text.display(win)

            # Pellets
            for pellet in self.pellets:
                pellet.display(win)

            #  Power pellets
            for power_pellet in self.power_pellets:
                power_pellet.display(win)

            # Ghosts
            for ghost in self.ghosts:
                ghost.display(win)

            # Pac-Man
            self.pac_man.display(win)

        elif self.paused:
            self.score_indicator.display(win)
            self.game_maze.display(win)

            for pellet in self.pellets:
                pellet.display(win)
            for power_pellet in self.power_pellets:
                power_pellet.display(win)
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

            self.score_indicator.display(win)
            self.pac_man.display(win)

        # Mainloop of the level
        else:

            # Score Indicators
            self.score_indicator = gui.Word('{}'.format(self.score),
                                             self.score_position,
                                             (234, 234, 234),
                                             24,
                                             self.win_scale
                                             )

            self.score_indicator.display(win)

            # Maze
            self.game_maze.display(win)

            # Ghost Paths
            if self.show_paths:
                for ghost in self.ghosts:
                    ghost.draw_path(win)

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
                if not self.death_sound_playing:
                    pg.mixer.stop()
                    self.death_sound_playing = True

            if self.pac_man.death_animation_finished and not self.finished:
                self.finished = True

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
                    self.level_score += points
                    self.score += points

                    win.blit(self.points_texts['{}.png'.format(str(points))],
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
        Quits the level. Stops music playing and saves that level to the database.
        :return: None
        """

        local_database.save_level(
                                    self.level_num,
                                    self.game_id,
                                    None,
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


class Level1(Level):
    """
    In level one, the user is introduced to the movement mechanics (using arrow keys). They are also introduced to
    the first and least threatening ghost: clyde. They are shown the behaviours that all ghosts have and the
    behaviour of clyde. This is shown through the paths that are displayed.
    """

    def __init__(self, win_scale, game_id, level_num, maze_id, pellets, power_pellets, score, tutorial_prompts):
        super().__init__(win_scale, game_id, level_num, maze_id, pellets, power_pellets, score, tutorial_prompts)

    def run(self, win, events):
        super().run(win, events)

        # Tutorial Events
        #self.pellets = self.pellets[-30:]

        if not self.start:
            if self.tutorial_boxes[0].finished:
                self.start = True
            else:
                self.tutorial_boxes[0].update(events)
                self.tutorial_boxes[0].display(win)

        if len(self.pellets) == 0 and not self.tutorial_boxes[1].finished:
            self.paused = True
            self.tutorial_boxes[1].update(events)
            self.tutorial_boxes[1].display(win)
            if self.tutorial_boxes[1].finished:
                self.paused = False


class Level2(Level):
    """

    """

    def __init__(self, win_scale, game_id, level_num, maze_id, pellets, power_pellets, score, tutorial_prompts):
        super().__init__(win_scale, game_id, level_num, maze_id, pellets, power_pellets, score, tutorial_prompts)

    def run(self, win, events):

        super().run(win, events)

        # Tutorial Events
        #self.pellets = self.pellets[-30:]
        if not self.start:
            if self.tutorial_boxes[0].finished:
                self.start = True
                self.show_paths = True
            else:
                self.tutorial_boxes[0].update(events)
                self.tutorial_boxes[0].display(win)

        if len(self.pellets) == 100 and not self.tutorial_boxes[1].finished:
            self.paused = True
            self.tutorial_boxes[1].update(events)
            self.tutorial_boxes[1].display(win)
            if self.tutorial_boxes[1].finished:
                self.paused = False

        if len(self.pellets) == 0 and not self.tutorial_boxes[2].finished:
            self.paused = True
            self.tutorial_boxes[2].update(events)
            self.tutorial_boxes[2].display(win)
            if self.tutorial_boxes[2].finished:
                self.paused = False


class Level3(Level):
    """

    """

    def __init__(self, win_scale, game_id, level_num, maze_id, pellets, power_pellets, score, tutorial_prompts):
        super().__init__(win_scale, game_id, level_num, maze_id, pellets, power_pellets, score, tutorial_prompts)

    def run(self, win, events):
        super().run(win, events)

        # Tutorial Events
        #self.pellets = self.pellets[-30:]
        if not self.start:
            if self.tutorial_boxes[0].finished:
                self.start = True
                self.show_paths = True
            else:
                self.tutorial_boxes[0].update(events)
                self.tutorial_boxes[0].display(win)

        if len(self.pellets) == 20 and not self.tutorial_boxes[1].finished:
            self.paused = True
            self.tutorial_boxes[1].update(events)
            self.tutorial_boxes[1].display(win)
            if self.tutorial_boxes[1].finished:
                self.paused = False

        if len(self.pellets) == 0 and not self.tutorial_boxes[2].finished:
            self.paused = True
            self.tutorial_boxes[2].update(events)
            self.tutorial_boxes[2].display(win)
            if self.tutorial_boxes[2].finished:
                self.paused = False


class Level4(Level):
    """

    """

    def __init__(self, win_scale, game_id, level_num, maze_id, pellets, power_pellets, score, tutorial_prompts):
        super().__init__(win_scale, game_id, level_num, maze_id, pellets, power_pellets, score, tutorial_prompts)

    def run(self, win, events):
        super().run(win, events)

        # Tutorial Events
        #self.pellets = self.pellets[-30:]
        if not self.start:
            if self.tutorial_boxes[0].finished:
                self.start = True
                self.show_paths = True
            else:
                self.tutorial_boxes[0].update(events)
                self.tutorial_boxes[0].display(win)

        if len(self.pellets) == 20 and not self.tutorial_boxes[1].finished:
            self.paused = True
            self.tutorial_boxes[1].update(events)
            self.tutorial_boxes[1].display(win)
            if self.tutorial_boxes[1].finished:
                self.paused = False

        if len(self.pellets) == 0 and not self.tutorial_boxes[2].finished:
            self.paused = True
            self.tutorial_boxes[2].update(events)
            self.tutorial_boxes[2].display(win)
            if self.tutorial_boxes[2].finished:
                self.paused = False


class Level5(Level):
    """

    """

    def __init__(self, win_scale, game_id, level_num, maze_id, pellets, power_pellets, score, tutorial_prompts):
        super().__init__(win_scale, game_id, level_num, maze_id, pellets, power_pellets, score, tutorial_prompts)

    def run(self, win, events):
        super().run(win, events)


class Level6(Level):
    """

    """

    def __init__(self, win_scale, game_id, level_num, maze_id, pellets, power_pellets, score, tutorial_prompts):
        super().__init__(win_scale, game_id, level_num, maze_id, pellets, power_pellets, score, tutorial_prompts)

    def run(self, win, events):
        super().run(win, events)
