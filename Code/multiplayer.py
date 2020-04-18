__author__ = 'Will Evans'

import os
import pygame as pg
import networking
import local_database

from sprites import *
from multiplayer_sprites import *
from datastructures import Maze
from gui import *


class Multiplayer:
    def __init__(self, win, win_scale, user_id):
        """
        Menu for multiplayer (contains method for creating avatars that is used in sub menus). It controls the
        multiplayer menu screen. It simply prompts the user to choose either 'create game' or 'join game'. They will
        then be taken to the appropriate pages.
        :param win: The current window, all objects must be blitted to this window to be displayed.
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables).
        :param user_id: Unique to each user, required to play online.
        """

        # Essential Information
        self.win = win
        self.win_scale = win_scale
        self.clock = pg.time.Clock()
        self.program = 'Multiplayer'
        self.error_message = None
        self.finished = False
        self.user_id = user_id

        # Data
        self.players = None

        # Player Boxes
        self.boxes, self.large_box = get_boxes(win_scale)

        # Player Avatars
        #   Avatar Skins
        self.avatar_skins = get_avatar_skins()
        self.avatars, self.names, self.scores, self.ready, self.places = get_avatars(self.players,
                                                                                     self.finished,
                                                                                     self.avatar_skins,
                                                                                     self.boxes,
                                                                                     self.large_box,
                                                                                     win_scale
                                                                                     )

        # Choices
        self.font_size = 32
        self.choices = []
        self.choices.append(LiveWord('Create Game', 350, self.font_size, win_scale))

        self.choices.append(LiveWord('Join Game', 380, self.font_size, win_scale))

        # Check user_id
        if user_id is None:
            self.program = 'StartScreen'
            self.error_message = 'Login Required'
        else:
            self.user_id = user_id

    def run(self, win, events):
        """
        Main method, called from main loop.
        :param win: The current window, all objects must be blitted to this window to be displayed.
        :param events: Contains events from the pg.event.get() call containing all keyboard events.
        :return: None
        """

        # Events
        for event in events:
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    self.program = 'StartScreen'

        # Updating text reactions (i.e. highlighting)
        self.check_inputs(events)
        self.update_text()

        # Displaying all objects
        for choice in self.choices:
            choice.display(win)

        for box in self.boxes:
            box.display(win)
        self.large_box.display(win)

        for avatar in self.avatars:
            avatar.display(win)

        pg.display.update()

    def check_inputs(self, events):
        """
        Checks whether any of the choices have been clicked.
        :param events: Contains events from the pg.event.get() call containing all keyboard events.
        :return: Target program of the word clicked or the current program.
        """

        pos = get_mouse_input(events)
        if pos is not None:
            for choice in self.choices:
                if choice.check_click(*pos):
                    self.program = choice.get_program()

    def update_text(self):
        """
        Updates the choices (highlights when mouse passes over).
        :return: None
        """

        for choice in self.choices:
            if choice.check_mouse(*pg.mouse.get_pos()):
                choice.react()

    def get_program(self):
        return self.program

    def get_error(self):
        return self.error_message

    def quit(self):
        pass


class HostMenu:
    def __init__(self, win, win_scale, user_id):
        """
        Host menu screen. Pac-Man will be coloured in and the hosts local IP address will be displayed in the bottom.
        This can then be used by other players to connect to the host.
        :param win:
        :param win_scale:
        :param user_id:
        """

        # Essential Information
        self.win = win
        self.win_scale = win_scale
        self.clock = pg.time.Clock()
        self.program = 'Create Game'
        self.error_message = None
        self.start_countdown = False
        self.finished = False
        self.match_started = False
        self.level = None
        self.winner_id = None
        self.user_id = user_id

        # Host Data
        self.name = local_database.get_username(user_id)

        self.client_id = 0

        # Instantiate Server
        self.server = networking.Server(self.name)
        self.ip = self.server.get_ip()

        self.players = self.server.get_players()

        # Thread that handles connecting clients
        self.server.searching_for_clients = True

        # Player Boxes
        self.boxes, self.large_box = get_boxes(win_scale)

        # Player Avatars
        #   Avatar skins
        self.avatar_skins = get_avatar_skins()
        self.avatars, self.names, self.scores, self.ready_indicators, self.places = get_avatars(self.players,
                                                                                                self.finished,
                                                                                                self.avatar_skins,
                                                                                                self.boxes,
                                                                                                self.large_box,
                                                                                                win_scale,
                                                                                                self.client_id
                                                                                                )

        # Input Box
        self.game_id_box = InputBox(x=120,
                                    y=400,
                                    w=100,
                                    h=20,
                                    font_size=20,
                                    win_scale=win_scale,
                                    name=self.ip,
                                    interactive=False
                                    )

        # Start Button
        self.start_button = Button(content='Start',
                                   pos=(265, 400),
                                   dimensions=(60, 20),
                                   font_size=20,
                                   text_colour=(255, 255, 30),
                                   width=2,
                                   win_scale=win_scale
                                   )

        # Cancel Button
        self.cancel_button = Button(content='Cancel',
                                    pos=(250, 400),
                                    dimensions=(75, 20),
                                    font_size=20,
                                    text_colour=(255, 0, 0),
                                    width=2,
                                    win_scale=win_scale
                                    )

        # Number
        self.number = Word(None, (180, 400), (255, 255, 30), 48, win_scale)

        # Clock
        self.start_countdown_clock = 0

    def run(self, win, events):
        """
        This method is run directly from the main script. It updates and displays all of the components on the screen.
        It also calls the server object to ensure all the data is up to date.
        :param win: The current window, all objects must be blitted to this window to be displayed.
        :type win: Surface.
        :param events: Contains events from the pg.event.get() call containing all keyboard events.
        :type events: list.
        :return: None
        """

        # Events
        for event in events:
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    self.program = 'Multiplayer'
                    self.server.quit()

        if self.level is None:
            pg.mixer.stop()

            players = self.server.get_players()

            # Check Score
            for player_id, player_data in players.items():
                if player_data['score'] > 20000:
                    self.finished = True
            if self.finished:
                places = []
                for id, data in players.items():
                    places.append({'id': id, 'score': data['score']})
                places = sorted(places, key=lambda k: k['score'], reverse=True)
                for place, data in enumerate(places):
                    self.server.update_data(data['id'], 'place', place)

            # Updating avatars as per how many people are connected
            self.avatars, self.names, self.scores, self.ready_indicators, self.places = get_avatars(

                                                                                                players,
                                                                                                self.finished,
                                                                                                self.avatar_skins,
                                                                                                self.boxes,
                                                                                                self.large_box,
                                                                                                self.win_scale,
                                                                                                self.client_id
                                                                                            )

            # Displaying boxes and avatars
            for box in self.boxes:
                box.display(win)
            self.large_box.display(win)

            for avatar in self.avatars:
                avatar.display(win)

            for name in self.names:
                name.display(win)

            for score in self.scores:
                score.display(win)

            for ready in self.ready_indicators:
                ready.display(win)

            for place in self.places:
                place.display(win)

            if not self.finished:
                if self.start_countdown:
                    # Start button related objects / countdown
                    if not self.server.has_ai:
                        self.server.add_ai()
                    self.start_countdown_clock += 1 / 60
                    self.number.content = str(5 - int(self.start_countdown_clock))
                    self.number.render()

                    if self.start_countdown_clock > 3:
                        if self.winner_id is not None:
                            self.server.swap(self.winner_id)

                    if self.start_countdown_clock > 4.8:
                        self.start_countdown_clock = 0
                        self.server.reset()
                        self.server.send_data()

                        game_maze = Maze(1, self.win_scale)

                        score = [data['score'] for data in self.server.get_players().values() if data['skin'] == 'pac-man'][0]

                        self.level = HostLevel(self.win_scale, 5, game_maze, score, self.server)
                        self.match_started = True

                        self.start_countdown = False

                    self.number.display(win)
                    self.cancel_button.update(events)
                    self.start_countdown = not self.cancel_button.get_click()
                    self.cancel_button.display(win)
                else:
                    self.start_countdown_clock = 0
                    self.number.content = None

                    if self.server.has_ai and not self.match_started:
                        self.server.remove_ai()

                    self.start_button.update(events)
                    self.start_countdown = self.start_button.get_click()
                    self.start_button.display(win)

                    if not self.match_started:
                        self.game_id_box.update(events)
                        self.game_id_box.display(win)

        else:
            self.level.run(win, events)
            if self.level.finished:
                self.winner_id = self.level.winner_id
                score = self.server.get_data(self.winner_id, 'score')
                self.server.update_data(self.winner_id, 'score', score + 1600)
                self.level = None

        self.server.update_data(0, 'countdown', self.number.content)
        self.server.update_data(0, 'start', False if self.level is None else True)
        self.server.update_data(0, 'finished', self.finished)
        self.server.send_data()

    def get_program(self):
        return self.program

    def get_error(self):
        return self.error_message

    def quit(self):
        self.server.quit()
        pg.mixer.stop()


class ClientMenu:
    def __init__(self, win, win_scale, user_id):
        """
        This is very similar to the host menu in that there will be colour avatars when players join the lobby, but
        there will be a ghost in the centre instead of Pac-Man. They will also have the option to ready up instead of
        starting the game.
        :param win: The current window, all objects must be blitted to this window to be displayed.
        :type win: Surface.
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables).
        :type win_scale: Integer.
        :param user_id: UserID if the user has signed in. This is used (at this stage) just to get the client's name
        from the database.
        """

        # Essentials
        self.win = win
        self.win_scale = win_scale
        self.user_id = user_id
        self.game_id = None
        self.game_id_buffer = None
        self.program = 'Join Game'
        self.error_message = None
        self.clock = pg.time.Clock()
        self.client = None
        self.connected = False
        self.start_level = False
        self.finished = False
        self.level = None
        self.winner_id = None

        # Client Data

        self.name = local_database.get_username(user_id)
        self.client_id = None
        self.players = None
        self.ready = False

        # Player Boxes
        self.boxes, self.large_box = get_boxes(win_scale)

        # Player Avatars
        #   Avatar skins
        self.avatar_skins = get_avatar_skins()
        self.avatars, self.names, self.scores, self.ready_indicators, self.places = get_avatars(
                                                                                                self.players,
                                                                                                self.finished,
                                                                                                self.avatar_skins,
                                                                                                self.boxes,
                                                                                                self.large_box,
                                                                                                self.win_scale,
                                                                                                )

        # Input Box
        self.input_box = InputBox(120, 380, 100, 20, 20, win_scale, 'Game ID')

        # Ready Buttons
        self.ready_button = Button(content='Ready',
                                   pos=(265, 400),
                                   dimensions=(60, 20),
                                   font_size= 20,
                                   text_colour=(255, 255, 30),
                                   width=2,
                                   win_scale=win_scale
                                   )

        self.unready_button = Button(content='Un ready',
                                     pos=(240, 400),
                                     dimensions=(85, 20),
                                     font_size=20,
                                     text_colour=(255, 255, 30),
                                     width=2,
                                     win_scale=win_scale
                                     )

        # Countdown number
        self.number = Word(None, (180, 400), (255, 255, 30), 48, win_scale)

    def run(self, win, events):
        """
        This method is run directly from the main script. It updates and displays all of the components on the screen.
        It also calls the client object to ensure all the data is up to date.
        :param win: The current window, all objects must be blitted to this window to be displayed.
        :type win: Surface.
        :param events: Contains events from the pg.event.get() call containing all keyboard events.
        :type events: list.
        :return: None
        """

        # Events
        for event in events:
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    try:
                        self.client.end()
                    except Exception as e:
                        print("Client escape {}".format(e))
                    self.program = 'Multiplayer'

        # Avatars
        if self.level is None:
            self.avatars, self.names, self.scores, self.ready_indicators, self.places = get_avatars(self.players,
                                                                                                    self.finished,
                                                                                                    self.avatar_skins,
                                                                                                    self.boxes,
                                                                                                    self.large_box,
                                                                                                    self.win_scale,
                                                                                                    self.client_id
                                                                                                    )

            for box in self.boxes:
                box.display(win)
            self.large_box.display(win)

            for avatar in self.avatars:
                avatar.display(win)

            for name in self.names:
                name.display(win)

            for score in self.scores:
                score.display(win)

            for ready in self.ready_indicators:
                ready.display(win)

            for place in self.places:
                place.display(win)

        if not self.connected:
            # Input Box
            self.game_id_buffer = self.input_box.update(events)
            if self.game_id_buffer != self.game_id:
                self.game_id = self.game_id_buffer

                self.client = networking.Client(self.game_id, self.name)
                self.connected = self.client.connected

                if self.connected:
                    self.client_id = self.client.get_client_id()
                else:
                    self.error_message = 'Invalid IP'
                    self.program = 'Multiplayer'
            self.input_box.display(win)

        else:
            if not self.client.connected:
                self.client.end()
                self.program = 'Multiplayer'
                self.error_message = 'Connection Lost'

            if not self.finished:
                if not self.start_level:
                    self.level = None

                    # Buttons
                    if self.ready:
                        self.unready_button.update(events)
                        self.ready = not self.unready_button.get_click()
                        self.unready_button.display(win)
                    else:
                        self.ready_button.update(events)
                        self.ready = self.ready_button.get_click()
                        self.ready_button.display(win)

                        self.client.update_data('ready', self.ready)
                        self.client.send_player_data()

                    self.number.render()
                    self.number.display(win)
                else:
                    if self.level is None:
                        game_maze = Maze(1, self.win_scale)
                        score = self.client.get_data(self.client_id, 'score')
                        self.level = ClientLevel(self.win_scale, 5, game_maze, score, self.client)

                    self.level.run(win, events)
            else:
                if not self.start_level:
                    self.level = None

            self.start_level = self.client.get_data(0, 'start')
            self.number.content = self.client.get_data(0, 'countdown')
            self.finished = self.client.get_data(0, 'finished')
            self.players = self.client.get_players()

    def get_program(self):
        return self.program

    def get_error(self):
        return self.error_message

    def quit(self):
        try:
            self.client.end()
        except AttributeError:
            pass
        except Exception as e:
            print(e)

        pg.mixer.stop()


class ClientLevel:
    def __init__(self, win_scale, level_num, game_maze, score, client):
        """
        Responsible for running each level by calling sprite objects and handling their updates. The class
        also controls other things, such as score, displaying maze etc.
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables).
        :type win_scale: Integer.
        :param level_num: This controls difficulty of the ghosts. The larger the level number, the more levels Pac-Man
        has completed and the harder the ghosts become.
        :type level_num: Integer.
        :param game_maze: 2D list of maze.
        :type game_maze: 2D list.
        :param score: Current score that should be displayed at the top.
        :type score: Integer.
        :param client: Object used to send and receive data.
        :type client: Server.
        """

        # Essential
        self.client = client
        self.client_id = self.client.get_client_id()
        self.players = self.client.get_players()
        self.score = score
        self.clock = pg.time.Clock()
        self.game_maze = game_maze
        self.win_scale = win_scale
        self.level_num = level_num
        self.program = 'Classic'
        self.error_message = None
        self.finished = False
        self.winner_id = None

        # Music
        self.music_channel = pg.mixer.Channel(5)
        self.music_channel.set_volume(0.5 * (local_settings.get_setting('game_volume') / 100))
        intro_music_path = os.path.join('Resources', 'sounds', 'intro_music.wav')
        self.music_channel.play(pg.mixer.Sound(intro_music_path))

        # Indicators
        self.score_position = (7 * 12, 2 * 12)
        self.score_indicator = Word('{}'.format(self.score), self.score_position, (234, 234, 234), 24, win_scale)

        self.ready_text = Word('ready!', (17.5 * 12, 20.5 * 12), (255, 255, 30), 23, win_scale, italic=True)
        self.game_over_text = Word('game over', (18 * 12, 20.5 * 12), (255, 0, 0), 21, win_scale)

        self.points_text = {}
        for text in os.listdir('Resources\\sprites\\{}'.format('points')):
            # noinspection PyUnresolvedReferences
            self.points_text.update({text: pg.transform.scale(
                pg.image.load('Resources\\sprites\\{}\\{}'.format('points', text)),
                ((24 * win_scale), (10 * win_scale)))})

        # Sprites
        self.pac_man, self.ghosts = self.get_players(self.players, self.game_maze, win_scale, self.client)
        self.ghosts_copy = self.ghosts[::]

        #   Pellets
        self.pellets = []
        self.power_pellets = []
        pellet_skin_path = os.path.join('Resources', 'sprites', 'pellets', 'pellet.png')
        pellet_skin = pg.transform.scale(pg.image.load(pellet_skin_path), (4 * win_scale, 4 * win_scale))
        power_pellet_skin_path = os.path.join('Resources', 'sprites', 'pellets', 'power_pellet.png')
        power_pellet_skin = pg.transform.scale(pg.image.load(power_pellet_skin_path), (12 * win_scale, 12 * win_scale))
        pellet_sound_channel = pg.mixer.Channel(2)
        pellet_sound_channel.set_volume(0.5 * (local_settings.get_setting('game_volume') / 100))

        power_pellet_death_sound_path = os.path.join('Resources', 'sounds', 'pellet', 'death.wav')
        pellet_death_sound = pg.mixer.Sound(power_pellet_death_sound_path)

        for row in self.game_maze.tiles:
            for tile in row:
                if tile.type == 'pellet':
                    self.pellets.append(
                                        Pellet(pellet_skin,
                                               tile,
                                               self.pac_man,
                                               win_scale,
                                               pellet_death_sound,
                                               pellet_sound_channel)
                                    )

                elif tile.type == 'power_pellet':
                    self.power_pellets.append(
                                        Pellet(power_pellet_skin,
                                               tile,
                                               self.pac_man,
                                               win_scale,
                                               pellet_death_sound,
                                               pellet_sound_channel,
                                               power_pellet=True)
                                        )

        self.large_pellet_channel = pg.mixer.Channel(3)
        self.large_pellet_channel.set_volume(0.5 * (local_settings.get_setting('game_volume') / 100))
        self.large_pellet_sound_path = os.path.join('Resources', 'sounds', 'large_pellet_loop.wav')
        self.large_pellet_sound = pg.mixer.Sound(self.large_pellet_sound_path)

        # Misc
        self.death_sound_playing = False
        self.started = False

        # Clocks and counts
        self.flashing_map_clock = 0
        self.flashing_map_count = 0

    def run(self, win, events):
        """
        This method is run from the Client menu class (as it needs to be able to transfer data form level object to
        level object which can't be done when running directly from main. It controls the updates and displaying of all
        objects.
        :param win: The current window, all objects must be blitted to this window to be displayed.
        :type win: Surface.
        :param events: Contains events from the pg.event.get() call containing all keyboard events.
        :type events: Tuple.
        :return: None
        """

        # Intro Music
        if self.music_channel.get_busy():

            # Display (only)
            self.game_maze.display(win)

            for pellet in self.pellets:
                pellet.display(win)
            for power_pellet in self.power_pellets:
                power_pellet.display(win)

            self.pac_man.display(win)

            for ghost in self.ghosts:
                ghost.display(win)

            self.score_indicator.display(win)

            self.ready_text.display(win)

        # Check if Pac-Man has won
        elif len(self.pellets) == 0:
            # Causes map to flash
            self.flashing_map_clock += 1 / 60

            if self.flashing_map_clock > 0.25:
                self.flashing_map_clock = 0
                self.flashing_map_count += 1
                self.game_maze.change_skin()

            # If map has finished flashing
            if self.flashing_map_count == 7:
                self.finished = True
                self.winner_id = self.pac_man.client_id

            # Display (only and selective)
            self.game_maze.display(win)
            self.score_indicator.display(win)
            self.pac_man.display(win)

        # Mainloop
        else:
            self.game_maze.display(win)
            # Updates and display
            for pellet in self.pellets:
                pellet.update()
                pellet.display(win)
                if pellet.eaten:
                    self.score += 10
                    self.pellets.remove(pellet)

            for power_pellet in self.power_pellets:
                power_pellet.update()
                power_pellet.display(win)

                # When power pellet eaten
                if power_pellet.eaten:
                    self.score += 50

                    # Play sound on loop
                    if not self.large_pellet_channel.get_busy():
                        self.large_pellet_channel.play(self.large_pellet_sound, loops=-1)

                    # Scare ghosts
                    for ghost in self.ghosts:
                        ghost.scare()
                        self.ghosts_copy = [ghost for ghost in self.ghosts if not ghost.dead]
                    self.power_pellets.remove(power_pellet)

            # If all ghosts are not scared (i.e all pac_man_dead or scared timer ended) stop playing sound
            if all([not ghost.scared for ghost in self.ghosts]):
                self.large_pellet_channel.stop()

            # Calculate how many points each ghost should give when eaten
            for ghost in self.ghosts_copy:
                if ghost.dead:
                    self.ghosts_copy.remove(ghost)
                    for ghost_ in self.ghosts_copy:
                        ghost_.display(win)
                    points = 200 * 2 ** (3 - len(self.ghosts_copy))
                    self.score += points

                    win.blit(self.points_text['{}.png'.format(str(points))],
                             (self.pac_man.x, self.pac_man.y - 8 * self.win_scale))
                    pg.display.update()
                    sleep(1)

            # Update and display Pac-Man
            self.pac_man.display(win)
            self.pac_man.update(events)

            if self.pac_man.dead:
                if self.death_sound_playing:
                    pass
                else:
                    pg.mixer.stop()
                    self.death_sound_playing = True

            # Dead is None when death-animation has finished
            if self.pac_man.death_animation_finished:
                self.game_over_text.display(win)
                client_id = [ghost.client_id for ghost in self.ghosts if ghost.won][0]
                pg.display.update()
                sleep(2)
                self.finished = True
                self.winner_id = client_id

            # If Pac-Man is alive
            if not self.pac_man.dead:

                # Update and display ghosts
                for ghost in self.ghosts:
                    ghost.update(events)
                    ghost.display(win)

            self.score_indicator = Word('{}'.format(self.client.get_data(self.client.get_client_id(), 'score')),
                                        self.score_position, (234, 234, 234), 24, self.win_scale)
            self.score_indicator.display(win)

        return True, None

    def get_players(self, players, game_maze, win_scale, client):
        """
        This takes the list of players and assigns each of them the appropriate multiplayer sprite based on whether they
        are Pac-Man or a ghost and based on whether they are a client or server.
        :param players: Dictionary of players and their various attributes.
        :type players: 2D dictionary.
        :param game_maze: 2D list of maze.
        :type game_maze: 2D list.
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables).
        :type win_scale: Integer.
        :param client: Object that is passed through to all the sprites in order for them to send and receive player
        data.
        :type client: Server.
        :return: Pac-Man object and list of ghost objects.
        """

        # Sprites
        ghosts = []

        # Pac-Man
        for client_id, player in players.items():
            skin = player['skin']
            if skin is None:
                continue
            # Pac-Man
            if skin == 'pac-man':
                if client_id == self.client_id:
                    pac_man = ClientPlayerPacMan(skin, game_maze, win_scale, client, client_id)
                else:
                    pac_man = ClientPacMan(skin, game_maze, win_scale, client, client_id)

        # Blinky
        for client_id, player in players.items():
            skin = player['skin']

            if skin == 'blinky':
                continue

            if skin == 'blinky':
                if client_id == self.client_id:
                    blinky = ClientPlayerGhost(skin,
                                               player['pos'],
                                               pac_man,
                                               game_maze,
                                               win_scale,
                                               self.level_num,
                                               client,
                                               client_id
                                               )

                elif skin == 'AI':
                    blinky = ClientBlinky(skin,
                                          pac_man,
                                          game_maze,
                                          win_scale,
                                          self.level_num,
                                          client,
                                          client_id
                                          )
                else:
                    blinky = ClientGhost(skin,
                                         player['pos'],
                                         pac_man,
                                         game_maze,
                                         win_scale,
                                         self.level_num,
                                         client,
                                         client_id
                                         )
                ghosts.append(blinky)

        # Ghosts
        for client_id, player in players.items():
            skin = player['skin']
            if skin != 'pac-man':
                # Ghosts
                if client_id == self.client_id:
                    ghosts.insert(0,
                                  ClientPlayerGhost(skin,
                                                    player['pos'],
                                                    pac_man,
                                                    game_maze,
                                                    win_scale,
                                                    self.level_num,
                                                    client,
                                                    client_id)
                                  )

                else:
                    ghosts.append(
                        ClientGhost(skin,
                                    player['pos'],
                                    pac_man,
                                    game_maze,
                                    win_scale,
                                    self.level_num,
                                    client,
                                    client_id
                                    )
                    )

        return pac_man, ghosts


class HostLevel(ClientLevel):
    def __init__(self, win_scale, level_num, game_maze, score, server):
        """
        Responsible for running each level by calling sprite objects and handling their updates. The class also
        controls other things, such as score, displaying maze etc.
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables).
        :type win_scale: Integer.
        :param level_num: This controls difficulty of the ghosts. The larger the level number, the more levels Pac-Man
        has completed and the harder the ghosts become.
        :type level_num: Integer.
        :param game_maze: 2D list of maze.
        :type game_maze: 2D list.
        :param score: Current score that should be displayed at the top.
        :type score: Integer.
        :param server: Object used to send and receive data.
        :type server: Server.
        """

        super().__init__(win_scale, level_num, game_maze, score, server)

        # Clock
        self.score_update_clock = 0

    def get_players(self, players, game_maze, win_scale, server):
        """
        This takes the list of players and assigns each of them the appropriate multiplayer sprite based on whether they
        are Pac-Man or a ghost.
        :param players: Dictionary of players and their various attributes.
        :type players: 2D dictionary.
        :param game_maze: 2D list of maze.
        :type game_maze: 2D list.
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables).
        :type win_scale: Integer.
        :param server: Object that is passed through to all the sprites in order for them to send and receive player
        data.
        :type server: Server.
        :return: Pac-Man object and list of ghost objects.
        """

        ghost_sprites = {

            'pinky': ServerPinky,
            'clyde': ServerClyde

        }
        # Sprites
        ghosts = []

        # Pac-Man
        for client_id, player in players.items():
            skin = player['skin']
            if skin is None:
                continue
            # Pac-Man
            if skin == 'pac-man':
                if client_id is 0:
                    pac_man = ServerPlayerPacMan(skin, game_maze, win_scale, server)
                elif player['name'] == 'AI':
                    pac_man = ServerPacManAI(skin, game_maze, win_scale, server, client_id)
                else:
                    pac_man = ServerPacMan(skin, game_maze, win_scale, server, client_id)

        # Blinky
        for client_id, player in players.items():
            skin = player['skin']
            if skin == 'blinky':
                if client_id is 0:
                    blinky = ServerPlayerGhost(skin, player['pos'], pac_man, game_maze, win_scale, self.level_num, server)
                elif player['name'] == 'AI':
                    blinky = ServerBlinky(skin, pac_man, game_maze, win_scale, self.level_num, server, client_id)
                else:
                    blinky = ServerGhost(skin, player['pos'], pac_man, game_maze, win_scale, self.level_num, server,
                                         client_id)
                ghosts.append(blinky)

        # Ghosts
        for client_id, player in players.items():
            skin = player['skin']

            if skin == 'blinky':
                continue

            if player['name'] != 'AI' and skin != 'pac-man':
                # Ghosts
                if client_id is 0:
                    ghosts.append(
                        ServerPlayerGhost(skin,
                                          player['pos'],
                                          pac_man,
                                          game_maze,
                                          win_scale,
                                          self.level_num,
                                          server)
                            )
                else:
                    ghosts.append(
                        ServerGhost(skin,
                                    player['pos'],
                                    pac_man,
                                    game_maze,
                                    win_scale,
                                    self.level_num,
                                    server,
                                    client_id)
                            )

            elif player['name'] == 'AI' and skin != 'pac-man':
                if skin == 'inky':
                    ghosts.append(ServerInky(player['skin'],
                                             pac_man,
                                             game_maze,
                                             win_scale,
                                             self.level_num,
                                             blinky,
                                             server,
                                             client_id)
                                  )
                else:
                    ghosts.append(ghost_sprites[skin](player['skin'],
                                                      pac_man,
                                                      game_maze,
                                                      win_scale,
                                                      self.level_num,
                                                      server,
                                                      client_id)
                                  )

        return pac_man, ghosts

    def run(self, win, events):
        """
        Does the same as client level except it also keeps track of each players score.
        :param win: The current window, all objects must be blitted to this window to be displayed.
        :type win: Surface.
        :param events: Contains events from the pg.event.get() call containing all keyboard events.
        :type events: Tuple.
        :return: None
        """

        # Scores
        self.pac_man.update_score(self.score)
        if self.score_update_clock > 1:
            self.score_update_clock = 0
            for ghost in self.ghosts:
                points = get_distance_points(ghost, self.pac_man)
                ghost.add_points(points)
        else:
            self.score_update_clock += 1 / 60
        super().run(win, events)


def get_avatar_skins():
    """
    Gets skins for each avatar from resources folder. Chooses between grey and coloured depending on whether the player is
    connected.
    :return: Dictionary of skins.
    """

    avatar_skins = {}

    # Adding grey avatars
    for skin in os.listdir('Resources\\sprites\\{}'.format('grey_avatars')):
        avatar_skins.update(
            {skin[:-4]: pg.image.load('Resources\\sprites\\{}\\{}'.format('grey_avatars', skin))})

    # Adding coloured skins for when a connection to a client is made
    for skin in os.listdir('Resources\\sprites\\{}'.format('coloured_avatars')):
        avatar_skins.update(
            {skin[:-4]: pg.image.load('Resources\\sprites\\{}\\{}'.format('coloured_avatars', skin))})

    return avatar_skins


def get_boxes(win_scale):
    """
    Returns box objects for the menu screens. These are just the 4 empty boxes across the top of the screen and
    the large central box that are displayed before there are any sprites in them.
    :param win_scale: 
    :return: Small boxes and the large box.
    """

    boxes = []
    y = 30
    w = 74
    h = 74
    x_spacing = 8
    line_width = 3
    colour = (200, 200, 200)
    for num in range(4):
        x = x_spacing + (x_spacing + w) * num
        boxes.append(Box((x, y), (w, h), colour, line_width, win_scale))

    large_box_rect = ((95, 170), (150, 150))
    large_box = Box(*large_box_rect, colour, line_width, win_scale)

    return boxes, large_box


def get_avatars(players, finished, avatar_skins, boxes, large_box, win_scale, client_id=None):
    """
    This class returns all the graphical attributes of each player within the many screen (also known as the
    avatars). It will add sprites, names, the current score, ready indicators and places (when the game has
    finished) into lists that can then be stored in the menu classes below.
    :param players: List of players and all attributes, used to generate all the objects.
    :param finished: Boolean, whether or not the game has finished (whether to display the places).
    :param avatar_skins:
    :param boxes:
    :param large_box:
    :param win_scale:
    :param client_id:
    :return: Lists: avatars, names, scores, ready_indicators and places.
    """
    avatars = []
    names = []
    scores = []
    ready_indicators = []
    places = []

    colours = {

        'pac-man': (255, 255, 30),
        'blinky': (222, 0, 0),
        'pinky': (255, 181, 255),
        'inky': (0, 222, 222),
        'clyde': (255, 181, 33),

    }

    place_details = {
        0:
            {
                'string': '1st',
                'colour': (255, 215, 0)
            },

        1:
            {
                'string': '2nd',
                'colour': (220, 220, 220)
            },

        2:
            {
                'string': '3rd',
                'colour': (205, 127, 50)
            },

        3:
            {
                'string': '4th',
                'colour': (169, 169, 169)
            },

        4:
            {
                'string': '5th',
                'colour': (169, 169, 169)
            }

    }

    large_box_boolean = False
    if players is not None:
        for num, box in enumerate(boxes):
            if num == client_id or (num == 3 and not large_box_boolean):

                x, y = large_box.rect.center
                x /= win_scale
                y /= win_scale
                colour = colours[players[client_id]['skin']]

                # Large Avatar
                skin = pg.transform.scale(avatar_skins[players[client_id]['skin']],
                                          (132 * win_scale, 132 * win_scale))
                skin_rect = skin.get_rect(center=large_box.rect.center)
                avatars.append(StaticSprite([skin], skin_rect))

                # Large Name
                name = players[client_id]['name']
                names.append(Word(name, (x, y + 95), colour, 26, win_scale, centre=True))

                # Score
                if players[num]['score'] is not None:
                    score = str(players[client_id]['score'])

                    scores.append(Word(content=score, pos=(x, y + 115), colour=colour,
                                       font_size=26, win_scale=win_scale, italic=True, centre=True))

                # Large Ready
                if players[client_id]['ready'] and not finished:
                    ready_indicators.append(
                        Word(content='Ready!', pos=(x, y + 132), colour=(255, 255, 30),
                             font_size=26, win_scale=win_scale, italic=True, centre=True))

                # Place
                if finished:
                    places.append(Word(content=place_details[players[client_id]['place']]['string'],
                                       pos=(x, y + 132),
                                       colour=place_details[players[client_id]['place']]['colour'],
                                       font_size=26,
                                       win_scale=win_scale,
                                       italic=True,
                                       centre=True)
                                  )

                large_box_boolean = True

            if large_box_boolean:
                num += 1

            # Avatar
            if players[num]['name'] is None:
                skin = pg.transform.scale(avatar_skins['grey_{}'.format(players[client_id]['skin'])],
                                          (66 * win_scale, 66 * win_scale))

            else:
                skin = pg.transform.scale(avatar_skins[players[num]['skin']],
                                          (66 * win_scale, 66 * win_scale))

                x, y = box.rect.center
                x /= win_scale
                y /= win_scale

                colour = colours[players[num]['skin']]

                # Name
                name = players[num]['name']
                names.append(Word(name, (x, y + 50), colour, 16, win_scale, centre=True))

                # Score
                if players[num]['score'] is not None:
                    score = str(players[num]['score'])
                    scores.append(
                        Word(score, (x, y + 62), colour, 16, win_scale, centre=True))

                # Ready
                if players[num]['ready'] and not finished:
                    ready_indicators.append(
                        Word(content='Ready!', pos=(x, y + 75), colour=(255, 255, 30),
                             font_size=16, win_scale=win_scale, italic=True, centre=True))

                # Place
                if finished:
                    places.append(Word(content=place_details[players[num]['place']]['string'],
                                       pos=(x, y + 75),
                                       colour=place_details[players[num]['place']]['colour'],
                                       font_size=16,
                                       win_scale=win_scale,
                                       centre=True)
                                  )

            rect = skin.get_rect(center=box.rect.center)
            avatars.append(StaticSprite([skin], rect))

    else:
        skin = pg.transform.scale(avatar_skins['grey_{}'.format('blinky')],
                                  (66 * win_scale, 66 * win_scale))
        for box in boxes:
            rect = skin.get_rect(center=box.rect.center)
            avatars.append(StaticSprite([skin], rect))

        skin = pg.transform.scale(avatar_skins['grey_pac-man'],
                                  (132 * win_scale, 132 * win_scale))
        rect = skin.get_rect(center=large_box.rect.center)
        avatars.append(StaticSprite([skin], rect))

    return avatars, names, scores, ready_indicators, places


def get_distance_points(ghost, pac_man):
    """
    Works out the euclidean distance between the ghost and Pac-Man objects and returns an amount of points to give the
    ghost based on how far it is.
    :param ghost: Ghost object.
    :param pac_man: Pac-Man object.
    :return: Points.
    """

    # Gets manhattan distance from pac_man to ghost
    distance = abs(ghost.tile.x - pac_man.tile.x) + abs(ghost.tile.y - pac_man.tile.y)

    # Subtracts distance from 13 so the closer to pac_man the more points you get
    points = (13 - distance) * 4

    # Ensures points are not negative
    return max(0, points)


def get_mouse_input(events):
    for event in events:
        if event.type == pg.MOUSEBUTTONDOWN:
            return event.pos
