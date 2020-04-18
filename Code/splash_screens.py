__author__ = 'Will Evans'

import pygame as pg
import gui
import local_settings
import local_database
import os


class StartScreen:
    def __init__(self, win, win_scale, user_id):
        """
        Displays the StartScreen and keeps track of all the objects on the screen and user interactions with them.
        :param win: The current window, all objects must be blitted to this window to be displayed.
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables).
        :param user_id: UserID if the user has signed in (they don't have to be signed in for the startscreen).
        """

        # Essential Information
        self.win = win
        self.win_scale = win_scale
        self.user_id = user_id
        self.clock = pg.time.Clock()
        self.program = 'StartScreen'
        self.sub_program_name = None
        self.sub_program = None
        self.sub_programs = {

            'loginscreen':  LoginScreen,
            'signupscreen': SignUpScreen,
            'settings':     Settings,
            'accounts':     Accounts

        }

        self.error_message = None

        # Pac-Man logo
        # Change this into a class
        pac_man_logo_path = os.path.join('resources', 'pac_man_logo.png')
        self.pac_title_scale = 80 * win_scale
        self.pac_title_size = (int(self.pac_title_scale * 3.8), self.pac_title_scale)
        self.pac_title = pg.transform.smoothscale(pg.image.load(pac_man_logo_path), self.pac_title_size)
        self.pac_title_rect = self.pac_title.get_rect(center=(168 * win_scale, 80 * win_scale))

        # Music
        theme_music_path = os.path.join('resources', 'sounds', 'startscreen', 'theme.mp3')
        pg.mixer.music.load(theme_music_path)

        # Icons
        self.icons = []

        #   Sound Icon
        sound_img_paths = [
                            os.path.join('resources', 'icons', 'unmute.png'),
                            os.path.join('resources', 'icons', 'mute.png')
                        ]
        self.icons.append(gui.Icon((326, 422), sound_img_paths, win_scale, sound=True, toggle=True))

        #   Settings Icon
        settings_img_path = [os.path.join('resources', 'icons', 'settings.png')]
        self.icons.append(gui.Icon((296, 422), settings_img_path, win_scale, target_program='settings'))

        #   Accounts Icon
        accounts_img_path = [os.path.join('resources', 'icons', 'accounts.png')]
        self.icons.append(gui.Icon((266, 422), accounts_img_path, win_scale, target_program='loginscreen'))

        self.y_spacing = 35
        self.font_size = 40

        # Choices
        self.__choices = self.get_choices(['Story', 'Classic', 'Multiplayer',  'Highscores'], win_scale)

        # Actions
        pg.mixer.music.play()

    def get_choices(self, string_choices, win_scale):
        """
        Returns a list of live word objects. One for each choice in the string choices parameter.
        :param string_choices: A list of strings with the names of the possible choices/options that the user can
        :param string_choices: A list of strings with the names of the possible choices/options that the user can
        choose.
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables).
        :return: List of options.
        """

        choices = []
        for num, content in enumerate(string_choices):
            y = 220 + num * self.y_spacing
            colour = (160, 205, 217) if num in [1, 3, 5] else (188, 47, 39)
            choices.append(gui.LiveWord(content, y, self.font_size, win_scale, colour))
        return choices

    def run(self, win, events):
        """
        Updates the screen with the text and icon objects.
        :param win: The current window, all objects must be blitted to this window to be displayed.
        :param events: Contains events from the pg.event.get() call containing all keyboard events.
        :return: None
        """

        if self.sub_program_name is not None:
            if self.sub_program is None or self.sub_program.error_message is not None:
                self.sub_program = self.sub_programs[self.sub_program_name](win,
                                                                            self.win_scale,
                                                                            self.user_id,
                                                                            self.icons)
            else:
                self.sub_program.run(win, events)

            self.error_message = self.sub_program.error_message
            self.user_id = self.sub_program.user_id
            program_name = self.sub_program.get_sub_program_name()

            if program_name is None:
                self.sub_program_name = None
                self.sub_program = None

            elif program_name != self.sub_program_name:
                self.sub_program_name = program_name
                self.sub_program = None

        else:
            for text in self.__choices:
                if text.check_mouse(*pg.mouse.get_pos()):
                    text.react()

            self.update_objects(events)

            win.blit(self.pac_title, self.pac_title_rect)

            for word in self.__choices:
                word.display(win)

            for icon in self.icons:
                icon.display(win)

    def update_objects(self, events):
        """
        Updates objects.
        :param events: Contains events from the pg.event.get() call containing all keyboard events.
        :return: None
        """

        pos = get_mouse_input(events)
        if pos is not None:
            for icon in self.icons:
                if pos is not None:
                    if icon.check_click(*pos):
                        icon.action()
                        if icon.has_target:
                            self.sub_program_name = icon.target_program

            for word in self.__choices:
                if word.check_click(*pos):
                    self.program = word.get_program()

    def get_program(self):
        return self.program

    def get_error(self):
        return self.error_message

    def quit(self):
        pg.mixer.music.stop()


class SubProgram:
    def __init__(self, win, win_scale, user_id, icons_list):
        """
        Program within the menu screen. This parent class contains the methods that run / update each sub menu as they
        are the same.
        :param win: The current window, all objects must be blitted to this window to be displayed.
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables).
        :param user_id: UserID if the user has signed in (they don't have to be signed in to play Classic).
        :param icons_list: List of icon objects from the StartScreen.
        """

        # Essential
        self.win = win
        self.win_scale = win_scale
        self.user_id = user_id
        self.icons = icons_list
        self.error_message = None

        # Defined in subclasses
        self.sub_program_name = None

        # Back button
        back_button_path = os.path.join('resources', 'icons', 'back_arrow.png')
        self.back_button = gui.Icon((35, 422), [back_button_path], win_scale, target_program=None)

    def run(self, win, events):

        # Events
        for event in events:
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    self.sub_program_name = None

        for icon in self.icons:
            icon.display(win)
        self.back_button.display(win)
        self.update_icons(events)

    def update_icons(self, events):
        icons = self.icons[::]
        icons.append(self.back_button)
        pos = get_mouse_input(events)
        if pos is not None:
            for icon in icons:
                if pos is not None:
                    if icon.check_click(*pos):
                        icon.action()
                        if icon.has_target:
                            self.sub_program_name = icon.target_program

    def get_sub_program_name(self):
        return self.sub_program_name


class SignUpScreen(SubProgram):
    def __init__(self, win, win_scale, user_id, icons):
        """
        Uses words and input boxes to display a sign up screen. It also updates the input boxes and calls the local
        database to check whether the details are valid, then (if they are) asks the local database to save the details.
        :param win: The current window, all objects must be blitted to this window to be displayed.
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables).
        :param user_id: UserID if the user has signed in (they don't have to be signed in to play Classic).
        :param icons: List of icon objects from the StartScreen.
        """

        super().__init__(win, win_scale, user_id, icons)

        self.sub_program_name = 'signupscreen'
        self.error_message = None

        self.enter_pressed = False

        # Sign Up Title
        self.signup_title = gui.Word('Sign Up!', (188, 90), (255, 255, 30), 80, win_scale, centre=True)

        # Username Input Box
        self.username_input_box = gui.InputBox(168, 206, 160, 30, 30, win_scale, 'Username', centre=True)

        # Password Input Box
        self.password_input_box = gui.InputBox(168, 246, 160, 30, 30, win_scale, 'Password', centre=True, private=True)

        # Password Confirm Box
        self.password_confirm_input_box = gui.InputBox(168, 286, 160, 30, 30,
                                                        win_scale,
                                                        'Password',
                                                        centre=True,
                                                        private=True)

        # Sign Up Button
        self.signup_button = gui.Button('Sign Up',
                                         (168, 326),
                                         (160, 30),
                                         30,
                                         (255, 255, 30),
                                         2,
                                         win_scale,
                                         centre=True)

        self.boxes = [
                      self.username_input_box,
                      self.password_input_box,
                      self.password_confirm_input_box,
                      self.signup_button
                ]

    def run(self, win, events):
        super().run(win, events)

        # Updates
        for box in self.boxes:
            box.update(events)

        #   Sign up
        self.signup_button.update(events)

        # Display
        self.signup_title.display(win)

        for box in self.boxes:
            box.display(win)

        self.signup_button.display(win)

        if self.signup_button.get_click() or self.enter_pressed:
            self.enter_pressed = False
            approved, self.error_message = local_database.check_sign_up(
                                                                        self.username_input_box.user_input.lower(),
                                                                        self.password_input_box.user_input,
                                                                        self.password_confirm_input_box.user_input
                                                                        )
            if approved:
                self.sub_program_name = 'loginscreen'
                local_database.save_user(self.username_input_box.user_input.lower(), self.password_input_box.user_input)

        # Events
        for event in events:
            if event.type == pg.KEYDOWN:
                # Allows the user to cycle through input boxes using tab
                if event.key == pg.K_TAB:
                    try:
                        active_box = [box for box in self.boxes if box.tab_active][0]
                        active_box_index = self.boxes.index(active_box)
                        active_box.tab_active = False
                        active_box.active = False
                        self.boxes[(active_box_index + 1) % len(self.boxes)].tab_active = True
                    except IndexError:
                        self.boxes[0].tab_active = True
                elif event.key == pg.K_RETURN:
                    self.enter_pressed = True


class LoginScreen(SubProgram):
    def __init__(self, win, win_scale, user_id, icons):
        """
        Class for the login screen.
        :param win: The current window, all objects must be blitted to this window to be displayed.
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables).
        :param user_id: UserID if the user has signed in (they don't have to be signed in to play Classic).
        :param icons: List of icon objects from the StartScreen.
        """

        # Essential
        super().__init__(win, win_scale, user_id, icons)
        self.sub_program_name = 'loginscreen' if user_id is None else 'accounts'

        self.enter_pressed = False

        # Login Title
        self.login_title = gui.Word('Login!', (188, 90), (255, 255, 30), 80, win_scale, centre=True)

        # Username Input Box
        self.username_input_box = gui.InputBox(168, 206, 150, 30, 30, win_scale, 'Username', centre=True)

        # Password Input Box
        self.password_input_box = gui.InputBox(168, 246, 150, 30, 30, win_scale, 'Password', centre=True, private=True)

        # Login Button
        self.login_button = gui.Button('Login', (168, 286), (160, 30), 30, (255, 255, 30), 2, win_scale, centre=True)

        # SignUp Button
        self.signup_button = gui.Button('SignUp', (168, 286), (160, 30), 30, (255, 255, 30), 2, win_scale, centre=True)

        self.boxes = [self.username_input_box, self.password_input_box, self.signup_button]

        # Remember me Buttons
        self.remember_me = False
        self.remember_me_green = gui.Button('Remember me',
                                             (168, 326),
                                             (160, 30),
                                             24,
                                             (0, 222, 222),
                                             2,
                                             win_scale,
                                             centre=True)

        self.remember_me_red = gui.Button('Remember me',
                                           (168, 326),
                                           (160, 30),
                                           24,
                                           (222, 0, 0),
                                           2,
                                           win_scale,
                                           centre=True)

        self.remember_me_buttons = [self.remember_me_red, self.remember_me_green]

    def run(self, win, events):
        super().run(win, events)

        # Updates
        for box in self.boxes:
            box.update(events)

        if self.password_input_box.text_entered:
            self.boxes = [self.username_input_box, self.password_input_box, self.login_button]

        else:
            self.boxes = [self.username_input_box, self.password_input_box, self.signup_button]

        #   Sign Up
        active = self.signup_button.active or self.signup_button.tab_active
        if self.signup_button.get_click() or (self.enter_pressed and active):
            self.sub_program_name = 'signupscreen'

        #   Login
        active = self.signup_button.active or self.signup_button.tab_active
        if self.login_button.get_click() or (self.enter_pressed and not active):
            user_name = self.username_input_box.user_input.lower()
            password = self.password_input_box.user_input
            self.user_id = local_database.login(user_name, password)
            if self.user_id is None:
                self.error_message = 'Incorrect login details'
            else:
                if self.remember_me:
                    local_settings.save_setting('user_name', user_name)
                    local_settings.save_setting('password', password)
                self.sub_program_name = 'accounts'

        #   Remember me buttons
        self.remember_me_buttons[0].update(events)
        if self.remember_me_buttons[0].get_click():
            self.remember_me = not self.remember_me
            self.remember_me_buttons.reverse()

        # Display
        self.login_title.display(win)

        for box in self.boxes:
            box.display(win)

        self.remember_me_buttons[0].display(win)

        # Events
        for event in events:
            if event.type == pg.KEYDOWN:

                # Tab moves the active box along in the list above (for ease of logging in)
                if event.key == pg.K_TAB:
                    try:
                        active_box = [box for box in self.boxes if (box.tab_active or box.active)][0]
                        active_box_index = self.boxes.index(active_box)
                        active_box.tab_active = False
                        active_box.active = False
                        self.boxes[(active_box_index + 1) % len(self.boxes)].tab_active = True
                    except IndexError:
                        self.boxes[0].tab_active = True
                elif event.key == pg.K_RETURN:
                    self.enter_pressed = True


class Settings(SubProgram):
    def __init__(self, win, win_scale, user_id, icons=None):
        """
        Class for settings menu. At the moment it only lets you change the win_scale and reloads the pygame window when
        this is done.
        :param win: Window Scale (How large the window is - must be multiplied by all size related variables).
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables).
        :param user_id: UserID if the user has signed in (they don't have to be signed in to play Classic).
        :param icons: List of icon objects from the StartScreen.
        """

        # Essential
        super().__init__(win, win_scale, user_id, icons)
        self.sub_program_name = 'settings'

        # Settings Title
        self.settings_title = gui.Word('Settings!', (178, 90), (255, 255, 30), 60, win_scale, centre=True)

        # Sliders
        self.music_slider = (gui.Slider('Music  ',
                                         168, 200, 200, 25,
                                         20, (255, 255, 30), 3,
                                         win_scale,
                                         level=int(local_settings.get_setting('music_volume')),
                                         centre=True))

        self.game_slider = (gui.Slider('Game Sound  ',
                                        168, 240, 200, 25,
                                        20, (255, 255, 30), 3,
                                        win_scale,
                                        level=int(local_settings.get_setting('game_volume')),
                                        centre=True))

        self.win_scale_slider = (gui.Slider('Win Scale  ',
                                             168, 280, 200, 25,
                                             20, (255, 255, 30), 3,
                                             win_scale,
                                             level=int(local_settings.get_setting('win_scale')),
                                             centre=True,
                                             levels=5))

    def run(self, win, events):
        super().run(win, events)

        # Events
        for event in events:
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    return None

        # Updates
        self.music_slider.update(events)
        pg.mixer.music.set_volume(self.music_slider.level_string/100)
        if local_settings.get_setting('music_volume') != self.music_slider.level_string:
            local_settings.save_setting('music_volume', self.music_slider.level_string)

        self.game_slider.update(events)
        if local_settings.get_setting('game_volume') != self.game_slider.level_string:
            local_settings.save_setting('game_volume', self.game_slider.level_string)

        self.win_scale_slider.update(events)
        for event in events:
            if event.type == pg.MOUSEBUTTONUP:
                if local_settings.get_setting('win_scale') != self.win_scale_slider.level_string:
                    local_settings.save_setting('win_scale', self.win_scale_slider.level_string)

        # Display
        self.settings_title.display(win)

        for icon in self.icons:
            icon.display(win)

        self.music_slider.display(win)
        self.game_slider.display(win)
        self.win_scale_slider.display(win)


class Accounts(SubProgram):
    def __init__(self, win, win_scale, user_id, icons):

        # Essential
        super().__init__(win, win_scale, user_id, icons)
        self.sub_program_name = 'accounts'

        # Login Title
        self.accounts_title = gui.Word('Accounts!', (180, 90), (255, 255, 30), 60, win_scale, centre=True)

        # Logged in as
        self.user_name = gui.Word(
                                    'Logged in as:       {}'.format(local_database.get_username(user_id)),
                                    (310, 120),
                                    (255, 255, 30),
                                    15,
                                    win_scale,

                                )

        # Statistics
        self.statistics = []
        colour = (255, 255, 30)
        stats_dict = local_database.get_statistics(user_id)
        if stats_dict is None:
            string_1 = 'Statistics will appear'
            string_2 = 'once you play a game'
            self.statistics.append(gui.Word(string_1, (336 / 2, 250), colour, 25, win_scale, centre=True))
            self.statistics.append(gui.Word(string_2, (336 / 2, 270), colour, 25, win_scale, centre=True))
        else:
            for num, (stat_name, stat) in enumerate(stats_dict.items()):
                self.statistics.append(gui.Word(stat_name.replace('_', ' '),
                                                 (20, 240 + 25 * num),
                                                 colour, 20, win_scale,
                                                 left=True))

                self.statistics.append(gui.Word(str(stat), (311, 240 + 25 * num), colour, 20, win_scale))

        # Log out button
        self.log_out_button = gui.Button('Log Out', (47, 400), (75, 20), 20, (255, 255, 30), 2, win_scale)

        # Stay logged in buttons
        self.remember_me = False
        self.remember_me_green = gui.Button('Remember me', (130, 400), (105, 20), 16, (0, 222, 222), 2, win_scale)
        self.remember_me_red = gui.Button('Remember me', (130, 400), (105, 20), 16, (222, 0, 0), 2, win_scale)
        self.remember_me_buttons = [self.remember_me_green, self.remember_me_red]
        if local_settings.get_setting('user_name') is None:
            self.remember_me_buttons.pop(0)

    def run(self, win, events):
        super().run(win, events)

        # Updates
        self.log_out_button.update(events)

        self.remember_me_buttons[0].update(events)
        if self.remember_me_buttons[0].get_click():
            if len(self.remember_me_buttons) is 2:
                local_settings.save_setting('user_name', None)
                local_settings.save_setting('password', None)
                self.remember_me_buttons.pop(0)

        # Display
        self.accounts_title.display(win)
        self.user_name.display(win)
        self.remember_me_buttons[0].display(win)

        for stat in self.statistics:
            stat.display(win)
        self.log_out_button.display(win)

        # Events
        if self.log_out_button.get_click():
            self.user_id = None
            self.sub_program_name = 'loginscreen'


class PauseScreen:
    def __init__(self, win, win_scale, user_id, icons):
        """
        Runs when a user selects the escape key during a game. Gives the user the option to resume or quit.
        :param win: The current window, all objects must be blitted to this window to be displayed.
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables).
        :param user_id: UserID if the user has signed in (they don't have to be signed in to play Classic).
        :param icons: List of icon objects from the StartScreen.
        """

        # Essential
        self.win = win
        self.win_scale = win_scale
        self.user_id = user_id
        self.icons = icons

    def run(self, win, events):

        # Events
        for event in events:
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    return None


def get_mouse_input(events):
    for event in events:
        if event.type == pg.MOUSEBUTTONUP:
            return event.pos


class Highscores:
    def __init__(self, win, win_scale, user_id):
        """
        Displays all the highscores that are saved in the database.
        :param win: The current window, all objects must be blitted to this window to be displayed.
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables).
        :param user_id: UserID if the user has signed in (they don't have to be signed in to play Classic).
        """

        # Essential Information
        self.win = win
        self.win_scale = win_scale
        self.user_id = user_id
        self.clock = pg.time.Clock()
        self.program = 'Highscores'
        self.error_message = None

        # Title
        self.title = gui.Word('Highscores!', (175, 90), (255, 255, 30), 45, win_scale, centre=True)
        self.text = gui.Word('Press any key to return...', (326, 417), (255, 255, 30), 15, win_scale)

        # Highscores
        colour = (255, 255, 30)
        rank_word = gui.Word('Rank', (20, 140), colour, 20, win_scale, left=True)
        score_word = gui.Word('Score', (120, 140), colour, 20, win_scale, left=True)
        name_word = gui.Word('Name', (311, 140), colour, 20, win_scale)
        self.highscore_titles = [rank_word, score_word, name_word]

        self.highscores = []
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
                }
        }

        for num, (score, name) in enumerate(local_database.get_highscores()):
            if num <= 2:
                place_string = place_details[num]['string']
                colour = place_details[num]['colour']
            else:
                place_string = '{}th'.format(num + 1)
                colour = (169, 169, 169)

            self.highscores.append(gui.Word(place_string, (20, 160 + 25 * num), colour, 20, win_scale, left=True))
            self.highscores.append(gui.Word(str(score), (120, 160 + 25 * num), colour, 20, win_scale, left=True))
            self.highscores.append(gui.Word(name, (311, 160 + 25 * num), colour, 20, win_scale))

            if num is 9:
                break

    def run(self, win, events):

        # Events
        for event in events:
            if event.type in [pg.KEYDOWN, pg.MOUSEBUTTONUP]:
                self.program = 'StartScreen'

        # Display
        self.title.display(win)

        for title in self.highscore_titles:
            title.display(win)

        for word in self.highscores:
            word.display(win)

        self.text.display(win)

    def get_program(self):
        return self.program

    def get_error(self):
        return self.error_message

    def quit(self):
        pass


if __name__ == '__main__':
    pass
