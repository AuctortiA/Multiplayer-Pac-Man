__author__ = 'Will Evans'
import os

import gui
import local_database
import local_settings
import multiplayer
import pygame as pg
import single_player
import splash_screens
import tutorial


def create_window(win_scale):
    x = int(28 * 12 * win_scale)
    y = int(36 * 12 * win_scale)

    win = pg.display.set_mode((x, y))
    # noinspection PyUnresolvedReferences
    icon_path = os.path.join('Resources', 'pacman.gif')
    icon = pg.image.load(icon_path)
    pg.display.set_icon(icon)
    pg.display.set_caption('Pac Man')

    return win


if __name__ == '__main__':

    os.environ['SDL_VIDEO_CENTERED'] = '1'

    # Gets settings
    win_scale = local_settings.get_setting('win_scale')
    music_volume = local_settings.get_setting('music_volume')

    # PyGame set up
    pg.mixer.pre_init(44100, -16, 1, 512)  # Sets up sounds to play with very little latency.
    pg.init()
    pg.mixer_music.set_volume(music_volume / 100)
    
    clock = pg.time.Clock()

    # Creates window
    win = create_window(win_scale)

    # Creates database
    local_database.create_db()

    run = True

    # List of programmes that can be run directly from this script
    programmes = {

                  'StartScreen':    splash_screens.StartScreen,
                  'Story':          tutorial.Story,
                  'Classic':        single_player.Classic,
                  'Multiplayer':    multiplayer.Multiplayer,
                  'Create Game':    multiplayer.HostMenu,
                  'Join Game':      multiplayer.ClientMenu,
                  'Highscores':     splash_screens.Highscores

                  }

    # Attempt to login from file
    username = local_settings.get_setting('user_name')
    password = local_settings.get_setting('password')
    user_id = local_database.login(username, password)

    # Essential information for starting the game
    program_name = 'StartScreen'
    program = programmes[program_name]
    running_program = program(win, win_scale, user_id)

    # Information on error messages (these must be stored in the main script).
    error_message = None
    error_box = None
    buffer = program

    # Mainloop
    while run:

        # Change window scale
        if win_scale != local_settings.get_setting('win_scale'):
            win_scale = local_settings.get_setting('win_scale')
            running_program.quit()
            running_program = program(win, win_scale, user_id)
            running_program.sub_program_name = 'settings'
            running_program.sub_program = splash_screens.Settings(win, win_scale, user_id, running_program.icons)
            win = create_window(win_scale)

        # Hand control to another program
        if buffer != program:
            buffer = program
            running_program.quit()
            pg.mixer.stop()
            running_program = program(win, win_scale, user_id)

        # See if the user wants to close the application
        events = pg.event.get()
        for event in events:
            if event.type == pg.QUIT:
                run = False
                running_program.quit()

        # Error message
        if error_message is not None and error_box is None:
            error_box = gui.ErrorBox(error_message, win_scale)
            error_box.display(win)

        if error_box is None:
            running_program.run(win, events)
        else:
            if not error_box.update(events):
                error_box = None
                error_message = None
                running_program.error_message = None

        # Get information for next cycle
        try:
            program = programmes[running_program.get_program()]
            error_message = running_program.get_error()
            user_id = running_program.user_id
        except KeyError:
            error_message = 'Not found'
            program = programmes['StartScreen']
            buffer = None

        # PyGame Essential
        clock.tick(60)
        pg.display.update()

        if error_box is None and error_message is None:
            win.fill((0, 0, 0))

    pg.quit()
    quit()
