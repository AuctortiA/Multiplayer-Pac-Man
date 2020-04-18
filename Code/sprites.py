__author__ = 'Will Evans'

import os
from pathfinding import Manhattan as Search
import pygame as pg
import random
import local_settings
from threading import Thread
from time import sleep


class Sprite:
    def __init__(self, resource_pack, position, maze, win_scale):
        """
        Template for sub-classes: 'Pac-Man' and 'Ghost'.
        :param resource_pack: Contains the path to the folder containing the skins for the sprite.
        :param position: x, y co-ords for the position of the sprite on the screen.
        :param maze: Two dimensional list representation of the maze.
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables).
        """

        # Essential
        self.win_scale = win_scale
        self.maze = maze

        #
        self.dead = False
        self.visible = False

        # Position
        x, y = position
        self.x = x * win_scale
        self.y = y * win_scale

        # Speed
        self._speed = 1.5
        self.speed_count = 0

        self.skin = '0'
        self.facing = 'e'
        self.move = 'e'
        self.online_move = 'e'
        self.buffer_move = 'e'

        # Skins
        self.skin = '0'
        self.skin_cap = 4

        #   Normal Skins
        self.normal_skins = {}
        for skin in os.listdir('resources\\sprites\\{}'.format(resource_pack)):
            # noinspection PyUnresolvedReferences
            self.normal_skins.update({skin: pg.transform.scale(
                pg.image.load('resources\\sprites\\{}\\{}'.format(resource_pack, skin)),
                ((22 * win_scale), (22 * win_scale)))})

        self.skins = self.normal_skins

        # Tiles
        tilex = int(self.x / (12 * self.win_scale))
        tiley = int(self.y / (12 * self.win_scale))

        self.tile = self.maze.tiles[tiley - 3][tilex]
        self.previous_tile = self.tile

        # Rects
        self.skin_rect = self.skins['e_0.png'].get_rect(center=(self.x, self.y))
        self.rect = pg.Rect(self.x - int(8 * win_scale),
                            self.y - int(8 * win_scale),
                            17 * win_scale,
                            17 * win_scale)

        # Movement booleans
        self.get_new_move = True
        self.wall_defence_delay = True
        self.return_None = False

        # Sound
        self.sound_channel = pg.mixer.Channel(0)
        self.sound_channel.set_volume(0.5 * local_settings.get_setting('game_volume') / 100)

        # Clocks
        self.skin_clock = 0
        self.stop_clock = 0
        self.death_animation_clock = 0

    def update(self, move):
        """
        Contains all the calls needed to update any sprite once called (60 times a second).
        :param move: Sprite's checked move.
        :return: None
        """

        self.correct_pos()
        self.correct_tunnel()
        self.facing, self.skin = self.get_skin(move)
        self.update_tile()
        self.update_pos(move)

    def get_input(self, events):
        """
        Default input method for the object using keyboard events (arrow keys).
        :param events: Contains events from the pg.event.get() call containing all keyboard events.
        :return: Returns a move ('n', 'e', 's', 'w').
        """

        move = self.move
        for event in events:
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_UP:
                    move = 'n'
                elif event.key == pg.K_RIGHT:
                    move = 'e'
                elif event.key == pg.K_DOWN:
                    move = 's'
                elif event.key == pg.K_LEFT:
                    move = 'w'

        return move

    def set_speed(self, speed):
        """
        Sets private attribute speed.
        :param speed: Speed value that will be stored in the private attribute speed.
        :return: None.
        """

        self._speed = speed

    def get_pos(self):
        """
        Returns position of the sprite.
        :return: Position of sprite (x,y).
        """

        return self.x, self.y

    def kill(self):
        """
        Kills the sprite by setting the dead attribute to True.
        :return: None.
        """

        self.dead = True

    def get_skin(self, move):
        """
        Returns the skin reference (direction and number) based on how and if the sprite is moving.
        These correspond to image files.
        :param move: Sprite's move.
        :return: Skin reference (direction, number).
        """

        if move is None:  # Stops the sprite changing skin number when it is not moving.
            move = self.facing
        if self.skin_clock == self.skin_cap:  # Allows the amount of frames between every skin change to be changed.
            num = abs(int(self.skin) - 1)  # If self.skin is 1 num will become 0. If it is 0 it will become 1.
            self.skin_clock = 0
        else:
            num = self.skin
        return move, str(num)

    def get_move(self, events):
        """
        Gets move from input then checks to see if that move is valid.
        :param events: Contains events from the pg.event.get() call containing all keyboard events.
        :return: Output from self.check_move(move).
        """

        move = self.get_input(events)
        return self.check_move(move)

    def check_move(self, move):
        """
        Performs checks on the move argument and returns a valid move.
        :param move: Move that the sprite wants to use.
        :return: A valid move (usually the user input unless it was invalid).
        """

        self.move = move  # Saves the move

        # Sets return_None to false when Pac-man hits a wall so that Pac-Man can change direction once he has hit a
        # wall.
        if self.get_next_tile(self.validate_move(self.move)).type != 'wall':
            self.return_None = False

        if self.return_None:
            return None

        # get_new_move is set to True after a tile change is detected to stop the direction from changing too many
        # times.
        if self.get_new_move:
            move = self.validate_move(self.move)

            # If return_none is false then self.facing is still a valid move
            if move == self.facing:
                return self.facing

            # If move is None it is because the sprite has collided with a wall
            elif move is None:
                return None

            else:
                self.get_new_move = False
                return move

        # Move in the current direction until the tile has changed
        else:
            return self.validate_move(self.facing)

    def validate_move(self, move):
        """
        Checks specifically whether the move will cause the player to collide with a wall or whether they are colliding.
        :param move: Move that the sprite wants to use.
        :return: A valid (won't collide with a wall) move.
        """

        tile_facing = self.get_next_tile(self.facing)
        tile_move = self.get_next_tile(move)

        if tile_move.type in ['wall', 'ghost_barrier']:
            if tile_facing.type in ['wall', 'ghost_barrier']:
                if self.rect.colliderect(tile_facing.rect):
                    self.return_None = True
                    return None
                else:
                    return self.facing
            else:
                return self.facing
        else:
            return move

    def correct_pos(self):
        """
        If the sprite is colliding with a wall it will work out how far the sprites (x,y) co-ords differ from the tile
        it is currently on and gradually bring them closer together. This keeps the sprites centred and prevents
        sprites from clipping through walls.
        :return: None
        """

        pac_x, pac_y = self.tile.pos

        tiles = []
        try:
            # Gets a list of all the tiles surrounding the sprite
            tiles = [self.maze.tiles[y + pac_y - 3][x + pac_x] for x, y in [(1, 0), (-1, 0), (0, 1), (0, -1)]]
        except IndexError as e:
            print(e)

        for tile in tiles:
            if self.rect.colliderect(tile.rect) and tile.type == 'wall':
                # Delay means that every other call of the correct_pos function the following is executed. This means
                # the animation appears much smoother
                if self.wall_defence_delay:
                    self.wall_defence_delay = False
                    wall_x, wall_y = tile.pos
                    difference_x = wall_x - pac_x
                    difference_y = wall_y - pac_y

                    self.x -= difference_x
                    self.y -= difference_y

                else:
                    self.wall_defence_delay = True

    def correct_tunnel(self):
        """
        Allows players to go through the tunnels by changing their x coordinate when they go off the screen.
        :return: None
        """

        # There are 12 pixels in each tile which is where the 12 comes from
        if self.x < -12 * self.win_scale and self.facing == 'w':
            self.x = 29 * 12 * self.win_scale

        if self.x > 29 * 12 * self.win_scale and self.facing == 'e':
            self.x = 0 * 12 * self.win_scale

    def update_pos(self, move):
        """
        Updates sprite's current position, according to the move, current speed and win_scale.
        :param move: Move that has now been checked can be used to move the sprite.
        :return: None
        """

        # Dictionary keeping track of what direction the moves will move the sprite and with what magnitude (in this
        # case it is a predetermined speed which can change throughout the game
        moves = {'n': (0, -self._speed),
                 'e': (self._speed, 0),
                 's': (0, self._speed),
                 'w': (-self._speed, 0),
                 None: (0, 0)
                 }

        x, y = moves[move]

        # This records what move has been used to move in the direction. Usually sent to the server in a
        # multiplayer game to correctly show the direction of a sprite on clients
        self.online_move = move

        # Skin clock is incremented once every frame unless the sprite is not moving. This is to make sure the skin
        # isn't changing while a sprite is stationary. The skin_clock attribute is used in the get_skin method
        if move is not None:
            self.skin_clock += 1

        # sprite position updated as per the above move and multiplied by win_scale to allow different sized windows
        self.x += x * self.win_scale
        self.y += y * self.win_scale

        # the position is then used to form the new rectangles which are used for blitting to the screen (skin_rect) and
        # for managing collisions (rect)
        self.skin_rect = self.skins['{}_{}.png'.format(self.facing, self.skin)].get_rect(center=(self.x, self.y))
        self.rect = pg.Rect(self.x - int(6 * self.win_scale),
                            self.y - int(6 * self.win_scale),
                            12 * self.win_scale,
                            12 * self.win_scale)

    def update_tile(self):
        """
        Updates what tile the sprite is on. This is used by many methods to determine whether the sprite is going to
        collide with walls in the future.
        :return: None
        """

        # Gets tile x,y coords as opposed to pixel x,y coords based on the sprites pixel position
        rect_tile_x, rect_tile_y = self.rect.centerx / (12 * self.win_scale), self.rect.centery / (12 * self.win_scale)

        # Gets tile x,y coords for the sprites current tile
        tile_x, tile_y = self.tile.pos

        # If we do the following when the sprite is off the screen (in the tunnel) we get many errors
        if rect_tile_x > 0:

            # If the tile x,y from the pixel position is not equal to the current tile, we update the current tile to
            # whichever tile the current pixel coords are inside of
            if not(int(rect_tile_x) == tile_x and int(rect_tile_y) == tile_y):
                self.previous_tile = self.tile
                try:
                    self.tile = self.maze.tiles[int(rect_tile_y) - 3][int(rect_tile_x)]
                except IndexError as e:
                    print(e)
                # If the tile has changed we can receive a new move
                self.get_new_move = True

    def display(self, win):
        """
        Displays the sprite with the skin that corresponds with the direction and also the skin_number (skin attribute)
        which is either a 0 or a 1.
        :param win: The current window, all objects must be blitted to this window to be displayed.
        :return: None
        """

        win.blit(self.skins['{}_{}.png'.format(self.facing, self.skin)], self.skin_rect)

    def get_next_tile(self, move):
        """
        This is used by the move validating methods by returning the next tile the sprite will collide with if it
        carries out the move passed through.
        :param move: The method will return the next tile after this move.
        :return: The next tile that will be reached if the sprite continues with the move.
        """

        # This is the dictionary storing which tiles (in relation to the current one) will need to be checked depending
        # on the move argument
        checks = {'n': (0, -1),
                  'e': (1, 0),
                  's': (0, 1),
                  'w': (-1, 0)}

        # if the move is None the method returns the move that
        if move is None:
            check = checks[self.facing]
        else:
            check = checks[move]
        x, y = check
        tile_x, tile_y = self.tile.pos
        # All y values must have 3 subtracted from them as the game is 3 tiles below the top of the window to allow
        # space for indicators such as score and highscore
        tile_y -= 3

        try:
            # Because tiles is a two dimensional list the y value must go first
            return self.maze.tiles[tile_y + y][tile_x + x]
        except IndexError as e:
            print(e)
            return self.maze.tiles[14][0]

    def draw_rect(self, win):
        """
        Used for debugging
        :param win: the current window, all objects must be blitted to this window to be displayed
        :return: None
        """
        pg.draw.rect(win, (255, 0, 0), self.rect)


class PacMan(Sprite):
    def __init__(self, resource_pack, maze, win_scale):
        """
        Contains all of the extra information specific to Pac-Man (not shared with ghosts).
        :param resource_pack: Contains the path to the folder containing the skins for the sprite.
        :param maze: Two dimensional list representation of the maze.
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables.
        """

        # Essential
        position = (167, 318)
        super().__init__(resource_pack, position, maze, win_scale)

        # Skins
        self.skin = '0'
        self.facing = 'e'
        self.move = 'e'
        self.num = 0

        #   Death animation
        self.death_animation_index = 0
        self.death_animation_skins = {}
        self.death_animation_finished = False

        for skin in os.listdir(os.path.join('resources', 'sprites', 'death_animation')):
            self.death_animation_skins.update(
                {skin: pg.transform.scale(
                                           pg.image.load(os.path.join('resources', 'sprites', 'death_animation', skin)),
                                         ((22 * win_scale), (22 * win_scale))
                                        )
                 }
                                                )

        # Sounds
        self.sounds = {}
        for sound in os.listdir(os.path.join('resources', 'sounds', resource_pack)):
            self.sounds.update({sound: pg.mixer.Sound(os.path.join('resources', 'sounds', resource_pack, sound))})

    def update(self, events):
        """
        Run once a frame, this is the method that controls everything to do with Pac-Man.
        :param events: Contains events from the pg.event.get() call containing all keyboard events.
        :return: State of Pac-Man (True: Death Animation Playing, None: Dead so no longer has state, False: Alive)
        """

        if not self.dead:
            move = self.get_move(events)
            super().update(move)
            if move is not None:
                # Plays siren sound only if Pac-Man is moving and if there isn't already a siren sound playing
                if not self.sound_channel.get_busy():
                    self.sound_channel.play(self.sounds['siren.wav'])
        else:
            self.death_animation()

    def death_animation(self):
        """
        Cycles through a series of death animation skins and plays the death animation sound.
        :return: True if death animation has finished
        """

        # Plays the sound once the first skin has been displayed (after 1/8 of a second) unless it is already playing
        if not self.sound_channel.get_busy() and self.death_animation_index == 1:
            self.sound_channel.play(self.sounds['death.wav'])
        self.death_animation_clock += 1/60
        if self.death_animation_clock > 1/8 and not self.death_animation_finished:
            self.death_animation_clock = 0
            self.death_animation_index += 1
        if self.death_animation_index == 13:
            self.death_animation_finished = True

    def display(self, win):
        """
        This display is slightly different as it either displays normally if Pac-Man is alive or displays a death
        animation skin if he is dead.
        :param win: the current window, all objects must be blitted to this window to be displayed
        :return: None
        """

        if self.dead:
            win.blit(self.death_animation_skins[f'{self.death_animation_index}.png'], self.skin_rect)
        elif not self.dead:
            win.blit(self.skins[f'{self.facing}_{self.skin}.png'], self.skin_rect)


class Ghost(Sprite):
    def __init__(self, resource_pack, position, target, maze, win_scale, level):
        """
        Contains all of the extra information specific to Pac-Man (not shared with Pac-Man).
        Target is sprite the ghost will target and level is the current level number which decides the difficulty
        of the ghost.
        :param resource_pack: Contains the path to the folder containing the skins for the sprite.
        :param position: Each ghost starts with a different position on the maze so this is required.
        :param target: Pac-Man object. Required to receive updates on which tile Pac-Man is currently on.
        :param maze: Two dimensional list representation of the maze.
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables).
        :param level: Level number, used to determine how long to wait between the two modes: chase (length increases
        over levels) to scatter (length decreases over levels) and how long between becoming scared to returning to
        normal (lowers over levels).
        """

        super().__init__(resource_pack, position, maze, win_scale)

        # Speed
        self._speed = 4 / 3
        self.speed_buffer = self._speed

        # this is only used by Blinky. When there are are certain number of pellets (lowers as levels progress). Blinky
        # will enter elroy mode and this will be set to True
        self.elroy = False
        # When there are even less pellets this will be set to True
        self.upgraded_elroy = False

        # This is used to keep track of which ghost caught Pac-Man
        self.won = False

        # These are the times between mode changes i.e on level 1 ghost will scatter for 7 seconds and chase for 20 etc.
        if level == 1:
            self.mode_timings = [7, 20, 7, 20, 5, 20, 5, 9999]
        elif level < 5:
            self.mode_timings = [7, 20, 7, 20, 5, 1033, 1/60, 9999]
        else:
            self.mode_timings = [5, 20, 5, 20, 5, 1037, 1/60, 9999]

        # Skins
        self.facing = 'e'
        self.skin = '0'

        self.skin_cap = 10

        skin_size = (22 * win_scale, 22 * win_scale)
        self.scared_skins = {}
        for skin in os.listdir(os.path.join('resources', 'sprites', 'scared')):
            scared_skin_path = os.path.join('resources', 'sprites', 'scared', skin)
            self.scared_skins.update(
                {skin: pg.transform.scale(pg.image.load(scared_skin_path), skin_size)}
            )

        self.dead_skins = {}
        for skin in os.listdir(os.path.join('resources', 'sprites', 'dead')):
            dead_skin_path = os.path.join('resources', 'sprites', 'dead', skin)
            self.dead_skins.update(
                {skin: pg.transform.scale(pg.image.load(dead_skin_path), skin_size)}
            )

        self.scared_flashing_skins = {}
        for skin in os.listdir(os.path.join('resources', 'sprites', 'scared_flashing')):
            scared_flashing_skin_path = os.path.join('resources', 'sprites', 'scared_flashing', skin)
            self.scared_flashing_skins.update(
                {skin: pg.transform.scale(pg.image.load(scared_flashing_skin_path), skin_size)}
            )

        self.colour = (255, 255, 255)

        # Rect
        self.skin_rect = self.skins['e_0.png'].get_rect(center=(self.x, self.y))

        self.mode_index = 0
        self.mode_count = 0

        # Modes
        self.mode = self.scatter
        self.buffer_mode = self.scatter

        self.to_switch = False

        self.scared = False
        self.scared_cap = 5 - 0.3 * level
        if self.scared_cap < 0:
            self.scared_cap = 0
        self.scared_clock = 0

        self.respawned = False

        # Path finding
        self.search = Search(maze.tile_map)

        self.target = target

        self.home = (26, 4)

        self.next_coords = self.scatter()[1]

        self.path = self.get_path(self.mode)

        self.next_x = 0
        self.next_y = 0

        self.axis_change = 'x'

        # Sound
        self.sound_channel = pg.mixer.Channel(1)
        self.sound_channel.set_volume(0.5 * (local_settings.get_setting('game_volume')/100))
        self.death_sound = pg.mixer.Sound(os.path.join('resources', 'sounds', 'ghost', 'death.wav'))

    def kill(self):
        """
        When a ghost is killed this is run.
        :return: None
        """

        self.dead = True
        self.scared = False
        self._speed = 2
        self.skins = self.dead_skins
        self.sound_channel.play(self.death_sound)

    def update(self, events):
        """
        Run once a frame, this is the method that controls everything to do with the Ghost.
        :param events: Contains events from the pg.event.get() call containing all keyboard events.
        :return: None
        """
        self.mode = self.get_mode()
        if self.to_switch:
            move = self.switch()
            self.to_switch = False
        else:
            move = self.get_move(events)

        super().update(move)
        self.check_collision()

    def get_mode(self):
        """
        Determines which mode should be used to get the Ghosts next target co-ords.
        :return: Name of the correct coord-getting method.
        """

        # Keeps track of how long a mode has been active for
        self.mode_count += 1/60

        # Once the current mode has been active for the preset amount of time
        if int(self.mode_count) == self.mode_timings[self.mode_index]:
            self.mode_index += 1
            # Reset count
            self.mode_count = 0

            # Toggles buffer mode between scatter or chase. Buffer is needed as some modes (e.g. 'scared' mode) stay
            # active even when ghosts have changed to a different base mode ('chase' or 'scatter'). Switch is also set
            # to True. This is a boolean and not a return as it is only used if the ghost is not 'scared' and not 'dead'
            # / 'respawning'.
            if self.buffer_mode == self.scatter:
                if not(self.scared or self.dead):
                    self.to_switch = True
                self.buffer_mode = self.chase
                return self.chase
            else:
                if not(self.scared or self.dead):
                    self.to_switch = True
                self.buffer_mode = self.scatter
                return self.scatter

        # Slows down the ghost when they are passing over a ghost barrier (like the original game)
        if not self.dead:
            if self.tile.type == 'ghost_barrier':
                self._speed = 0.25
            elif not self.scared:
                self._speed = self.speed_buffer

        # When a ghost reaches either of these coords (outside the ghost area) their mode is no longer 'respawn'. The
        # active mode will then become either 'chase' or 'scatter' depending on the buffer mode.
        if self.tile.pos in [(13, 14), (14, 14)]:
            self.respawned = False

        # If a ghost is dead the active mode is 'respawn' which will direct them to the ghost area.
        if self.dead:
            # Once they reach the ghost area -(13, 18) and (14, 18) are in the ghost area- they become alive again.
            # There skins and speed change to account for this
            if self.tile.pos in [(13, 18), (14, 18)]:
                self.dead = False
                self.respawned = True
                self.to_switch = True
                self._speed = self.speed_buffer
                self.skins = self.normal_skins
            else:
                return self.respawn

        elif self.respawned:
            return self.respawn

        elif self.scared:
            return self.random

        return self.buffer_mode

    def check_collision(self):
        """
        Checks whether the ghost is colliding with the target (Pac-Man).
        :return: None
        """
        
        if self.rect.colliderect(self.target.rect):
            if self.scared:
                self.kill()
            elif self.dead:
                pass
            else:
                self.won = True
                self.target.kill()
        else:
            self.won = False

    def get_move(self, events):
        """
        Uses the current mode to get the next co-ords. Works out the next move based on the target co-ords.
        :param events: Events not used, but keeps same method signature.
        :return: Ghost's move.
        """

        # When a ghost is in a tunnel their speed must decrease to 0.8, they must continue in the direction they are
        # facing and as soon as they leave the tunnel they must get a new path

        path = self.path

        if self.tile.pos[1] == 17:
            if self.tile.pos[0] <= 5 or self.tile.pos[0] >= 22:
                self._speed = 0.8
                if self.tile.pos[0] == 5 or self.tile.pos[0] == 22:
                    path = self.get_path(self.mode)
                    if path is None:
                        return self.facing
                else:
                    return self.facing
            else:
                if not self.scared:
                    if not self.dead:
                        self._speed = self.speed_buffer

        self.path = path
        self.next_coords = self.path[1]

        # This bit tests to see if the ghost has reached the 'next coords'. If it has, then new coords are calculated
        tile_x, tile_y = self.tile.pos
        x, y = self.next_coords

        if x == tile_x and y == tile_y - 3:
            path = self.get_path(self.mode)

            if path is None:
                path = self.chase()

            if path is None:
                return self.facing

            self.path = path
            self.next_coords = self.path[1]

        # Works out which direction the next coordinates are
        x, y = self.next_coords
        y += 3

        x *= 12 * self.win_scale
        x += 6 * self.win_scale

        y *= 12 * self.win_scale
        y += 6 * self.win_scale

        self.next_x = x
        self.next_y = y

        # If we just had self.x < x here then when we have a larger a screen the pos will jump above and below the
        # desired coords. Having self.x - x < -self.win_scale: means that we say the ghost has reached the correct
        # coords when it is within a few pixels of the exact coords pos
        if self.axis_change == 'x':
            if self.x < x and self.x - x < -self.win_scale:
                return 'e'
            elif self.x > x and self.x - x > self.win_scale:
                return 'w'
            else:
                self.axis_change = 'y'

        if self.axis_change == 'y':
            if self.y < y and self.y - y < -self.win_scale:
                return 's'
            elif self.y > y and self.y - y > self.win_scale:
                return 'n'
            else:
                self.axis_change = 'x'

    def get_move(self, events):
        """
        Uses the current mode to get the next coords. Works out the next move based on the target coords.
        :param events: Events not used, but keeps same method signature.
        :return: Ghost's move.
        """

        # When a ghost is in a tunnel their speed must decrease to 0.8, they must continue in the direction they are
        # facing and as soon as they leave the tunnel they must get a new path
        if self.tile.pos[1] == 17:
            if self.tile.pos[0] <= 5 or self.tile.pos[0] >= 22:
                self._speed = 0.8
                if self.tile.pos[0] == 5 or self.tile.pos[0] == 22:
                    try:
                        self.path = self.get_path(self.mode)
                        self.next_coords = self.path[1]
                    except Exception as e:
                        print(e)
                return self.facing
            else:
                if not self.scared:
                    if not self.dead:
                        self._speed = self.speed_buffer

        # This bit tests to see if the ghost has reached the 'next coords'. If it has, then new coords are calculated
        tile_x, tile_y = self.tile.pos
        x, y = self.next_coords

        if x == tile_x and y == tile_y - 3:
            try:
                self.path = self.get_path(self.mode)
                self.next_coords = self.path[1]
            except TypeError as e:
                print(e)
                try:
                    self.path = self.chase()
                    self.next_coords = self.path[1]
                except TypeError as e:
                    print(e)

        # Works out which direction the next coordinates are
        x, y = self.next_coords
        y += 3

        x *= 12 * self.win_scale
        x += 6 * self.win_scale

        y *= 12 * self.win_scale
        y += 6 * self.win_scale

        self.next_x = x
        self.next_y = y

        # If we just had self.x < x here then when we have a larger a screen the pos will jump above and below the
        # desired coords. Having self.x - x < -self.win_scale: means that we say the ghost has reached the correct
        # coords when it is within a few pixels of the exact coords pos
        if self.axis_change == 'x':
            if self.x < x and self.x - x < -self.win_scale:
                return 'e'
            elif self.x > x and self.x - x > self.win_scale:
                return 'w'
            else:
                self.axis_change = 'y'

        if self.axis_change == 'y':
            if self.y < y and self.y - y < -self.win_scale:
                return 's'
            elif self.y > y and self.y - y > self.win_scale:
                return 'n'
            else:
                self.axis_change = 'x'

    def validate_move(self, move):
        """
        Checks to see if a move is valid by checking whether it is opposite the current direction (facing). And by
        using the Sprite's validate_move above. This is not needed in classic mode as the path finding algorithm does
        not produce paths that require a 180 degree change in direction, however this is needed for online.
        :param move: Sprite's unchecked next move.
        :return: Validated move.
        """

        """
        if False:
            directions = ['n', 'e', 's', 'w', 'n', 'e']
            if move == directions[directions.index(self.facing) + 2]:
                return super().validate_move(self.facing)
            else:
                return super().validate_move(move)
        else:
            return super().validate_move(move)"""

        return super().validate_move(move)

    def get_path(self, mode):
        """
        Uses the mode to get a path. This middle man is needed in case the target is unreachable (in which case the path
        is None and instead the chase mode is used (which is always reachable).
        :param mode: Method for retrieving the path.
        :return: Path.
        """

        path = mode()
        if path is None:
            path = self.chase()
        return path

    def scare(self):
        """
        Sets the ghost into scared mode when called.
        :return: None.
        """

        if self.dead:
            # If the ghost is dead then they cannot become scared
            pass

        elif not self.scared:
            # If the ghost is not already scared change the following
            self._speed = 0.5
            self.skins = self.scared_skins
            self.scared_clock = 0
            self.scared = True
            self.switch()  # Changes the ghost's direction
            Thread(target=self.scared_timer).start()  # Keeps track of how long the ghost is scared

        else:
            # If the ghost is already scared, set the skins to scared and reset the clock
            self.skins = self.scared_skins
            self.scared_clock = 0

    def scared_timer(self):
        """
        Keeps track of how long the ghost is scared and adjust attributes accordingly. It's run on a thread.
        :return: None.
        """

        while self.scared:
            if self.scared_clock > self.scared_cap:
                # After the cap begin swapping the skins 4 times a second (rate based on how long the sleep is)
                if self.skins == self.scared_skins:
                    self.skins = self.scared_flashing_skins
                else:
                    self.skins = self.scared_skins

            if int(self.scared_clock) == 8:
                self.scared = False
                self._speed = 4/3
                self.skins = self.normal_skins
                break

            sleep(0.25)
            self.scared_clock += 0.25

    def draw_target(self, win):
        """
        At the moment used for debugging ghost paths and ensuring they are working correctly. Displays ghost's path
        :param win: The current window, all objects must be blitted to this window to be displayed.
        :return: None.
        """

        try:
            for x, y in self.path:
                pg.draw.rect(win, (0, 255, 0), pg.Rect(x * 12 * self.win_scale, (y+3) * 12 * self.win_scale, 15, 15))
        except Exception as e:
            print(e)

    def draw_next_tile_target(self, win):
        """
        Used for debugging ghost paths and ensuring they are working correctly. Displays ghost's target tile.
        :param win: The current window, all objects must be blitted to this window to be displayed.
        :return: None.
        """

        pg.draw.rect(win, (0, 255, 0), pg.Rect(self.next_x, self.next_y, 4, 4))

    def draw_path(self, win):
        """
        Used for the storymode to teach the use how the AI works. Simply draws the path that the AI will take at any
        given moment.
        :param win: The current window, all objects must be blitted to this window to be displayed.
        :return:
        """

        try:
            tile_path = [self.maze.tiles[tile_y][tile_x] for tile_x, tile_y in self.path]

            for pathtile_rect in self.get_pathtiles(tile_path, []):
                pg.draw.rect(win, self.colour, pathtile_rect)
        except IndexError as e:
            print(f'{e} in draw_path')

    def get_pathtiles(self, path, pathtiles):
        """
        Simply returns the PyGame rectangle responsible for displaying the path. This is in a separate method so
        it can be run recursively. It is static but I have included in the object, so it is easy to see how it is
        being called.
        :return: Pathtiles
        """

        if len(path) == 1:
            return pathtiles

        previous_tile = path[0]
        previous_x, previous_y = previous_tile.rect.center

        current_tile = path[1]
        current_x, current_y = current_tile.rect.center

        rect_long = 14 * self.win_scale
        rect_short = 2 * self.win_scale

        if previous_x == current_x:
            # must be a change in the y
            if previous_y < current_y:
                rect = pg.Rect(current_x - self.win_scale, previous_y - self.win_scale, rect_short, rect_long)
            else:
                rect = pg.Rect(current_x - self.win_scale, current_y - self.win_scale, rect_short, rect_long)
        else:
            # must be a change in the x
            if previous_x < current_x:
                rect = pg.Rect(previous_x - self.win_scale, current_y - self.win_scale,  rect_long, rect_short)
            else:
                rect = pg.Rect(current_x - self.win_scale, current_y - self.win_scale,  rect_long, rect_short)

        pathtiles.append(rect)

        return self.get_pathtiles(path[1:], pathtiles)

    def switch(self):
        """
        Changes the direction of the ghost.
        :return: Returns the opposite of the current move
        """

        directions = ['n', 'e', 's', 'w', 'n', 'e']
        move = directions[directions.index(self.facing) + 2]
        x, y = self.previous_tile.pos
        self.next_coords = (x, y-3)
        return move

    def respawn(self):
        """
        Pathfinding mode: It targets inside the centre, then targets outside once it has reached it.
        :return: The next path.
        """

        start_tile = self.tile.pos
        if self.respawned:
            target_tile = (13, 14)
        else:
            target_tile = (13, 18)
        start_tile = (start_tile[0], start_tile[1] - 3)
        target_tile = (target_tile[0], target_tile[1] - 3)
        return self.search.astar(start_tile, target_tile, self.facing)

    def scatter(self):
        """
        Pathfinding mode: It targets the specific ghost's home tile.
        :return: The next path.
        """

        start_tile = self.tile.pos
        target_tile = self.home
        start_tile = (start_tile[0], start_tile[1] - 3)
        target_tile = (target_tile[0], target_tile[1] - 3)
        return self.search.astar(start_tile, target_tile, self.facing)

    def chase(self):
        """
        Pathfinding mode: Unique to ghosts: default (Blinky) targets Pac-Man's current tile.
        :return: The next path.
        """

        start_tile = self.tile.pos
        target_tile = self.target.tile.pos
        start_tile = (start_tile[0], start_tile[1] - 3)
        target_tile = (target_tile[0], target_tile[1] - 3)
        return self.search.astar(start_tile, target_tile, self.facing)

    def random(self):
        """
        Pathfinding mode: Targets random row and random tile on that row as long as it's a pellet.
        :return: The next path.
        """

        start_tile = self.tile.pos
        chosen_row = random.choice(self.maze.tiles[1:-1])
        pellet_tiles = [tile for tile in chosen_row if tile.type == 'pellet']
        target_tile = random.choice(pellet_tiles).pos
        start_tile = (start_tile[0], start_tile[1] - 3)
        target_tile = (target_tile[0], target_tile[1] - 3)

        return self.search.astar(start_tile, target_tile, self.facing)


class Blinky(Ghost):
    def __init__(self, resource_pack, target, maze, win_scale, level):
        """
        Class for Blinky (contains home tile, starting position and can become elroy).
        :param resource_pack: Contains the path to the folder containing the skins for the sprite.
        :param target: Pac-Man object. Required to receive updates on which tile Pac-Man is currently on.
        :param maze: Two dimensional list representation of the maze.
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables).
        :param level: Level number, used to determine how long to wait between the two modes: chase (length increases
        over levels) to scatter (length decreases over levels) and how long between becoming scared to returning to
        normal (lowers over levels).
        """

        position = (168, 176)
        super().__init__(resource_pack, position, target, maze, win_scale, level)
        self.facing = 'e'
        self.visible = True
        self.colour = (222, 0, 0)

    def make_elroy(self):
        """
        Turns Blinky into Elroy (faster).
        :return: None
        """

        self.elroy = True
        self.speed_buffer = 13/9

    def elroy_upgrade(self):
        """
        Turns Blinky into upgraded Elroy (faster, and still targets Pac-Man in scatter mode).
        :return: None
        """
        self.upgraded_elroy = True
        self.speed_buffer = 5/3

    def scatter(self):
        """
        Pathfinding mode: It targets the Blinky's home tile unless Blinky is in Elroy mode, in which case this will
        function in the same way as the chase mode.
        :return: The next path.
        """

        start_tile = self.tile.pos
        if not self.elroy:
            target_tile = self.home
        else:
            target_tile = self.target.tile.pos

        start_tile = (start_tile[0], start_tile[1] - 3)
        target_tile = (target_tile[0], target_tile[1] - 3)
        return self.search.astar(start_tile, target_tile, self.facing)


class Pinky(Ghost):
    def __init__(self, resource_pack, target, maze, win_scale, level):
        """
        Class for Pinky (contains home tile, starting position).
        :param resource_pack: Contains the path to the folder containing the skins for the sprite.
        :param target: Pac-Man object. Required to receive updates on which tile Pac-Man is currently on.
        :param maze: Two dimensional list representation of the maze.
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables).
        :param level: Level number, used to determine how long to wait between the two modes: chase (length increases
        over levels) to scatter (length decreases over levels) and how long between becoming scared to returning to
        normal (lowers over levels).
        """

        position = (168, 214)
        super().__init__(resource_pack, position, target, maze, win_scale, level)

        self.home = (1, 4)
        self.facing = 's'
        self.colour = (255, 181, 255)

    def chase(self):
        """
        Pathfinding mode: Uses the tile 4 spaces ahead of Pac-Man to get the path. This decreases by one until the
        target reaches Pac-Man if the tiles in front are not reachable.
        :return: The next path.
        """

        start_tile = self.tile.pos
        target_tile = self.target.tile.pos
        start_tile = (start_tile[0], start_tile[1] - 3)
        target_tile = (target_tile[0], target_tile[1] - 3)

        targets = {'n': (0, -4), 'e': (4, 0), 's': (0, 4), 'w': (-4, 0)}
        tile_x, tile_y = target_tile
        facing = self.target.facing
        x, y = targets[facing]

        if x == 0:
            change = 'y'
            tile_x_temp = tile_x
        else:
            change = 'x'
            tile_y_temp = tile_y

        for i in range(5):
            if change == 'x':
                if x > 0:
                    tile_x_temp = tile_x + (x - i)
                else:
                    tile_x_temp = tile_x + (x + i)
            else:
                if y > 0:
                    tile_y_temp = tile_y + (y - i)
                else:
                    tile_y_temp = tile_y + (y + i)

            try:
                if self.maze.tiles[abs(tile_y_temp)][tile_x_temp].type in ['pellet', 'empty_tile']:
                    break

            except IndexError:
                continue

        path = self.search.astar(start_tile, (tile_x_temp, abs(tile_y_temp)), self.facing)
        if path is None:
            path = super().chase()
        return path


class Clyde(Ghost):
    def __init__(self, resource_pack, target, maze, win_scale, level):
        """
        Class for Clyde (contains home tile, starting position, start clock (Clyde doesn't leave centre straight away).
        :param resource_pack: Contains the path to the folder containing the skins for the sprite.
        :param target: Pac-Man object. Required to receive updates on which tile Pac-Man is currently on.
        :param maze: Two dimensional list representation of the maze.
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables).
        :param level: Level number, used to determine how long to wait between the two modes: chase (length increases
        over levels) to scatter (length decreases over levels) and how long between becoming scared to returning to
        normal (lowers over levels).
        """

        position = (192, 214)
        super().__init__(resource_pack, position, target, maze, win_scale, level)
        self.home = (1, 32)

        self.path = [(16, 15), (16, 14), (16, 13)]
        self.start_clock_master = 0
        self.start_clock = 0
        self.facing = 'n'
        self.speed_buffer = self._speed
        self._speed = 1

        self.colour = (255, 181, 33)

    def update(self, events):
        """
        Run once a frame, this is the method that controls the start (when Clyde is still inside the centre).
        :param events: Contains events from the pg.event.get() call containing all keyboard events.
        :return: None
        """

        if self.start_clock_master > 18:
            if not self.scared:
                self._speed = self.speed_buffer
            super().update(events)
        else:
            self.mode = self.get_mode()
            self.start_clock += 1/60
            self.start_clock_master += 1/60
            if self.start_clock <= 8/60:
                self.facing = 'n'
                self.update_pos('n')
            if 8/60 < self.start_clock <= 16/60:
                self.facing = 's'
                self.update_pos('s')
            elif self.start_clock > 16/60:
                self.start_clock = 0

    def euclidean_distance(self, target):
        """
        Needs this to work out how far from Pac-Man Clyde is. (Used in chase method).
        :param target: Object you want to measure the distance to (Pac-Man).
        :return: Distance.
        """
        tile_x, tile_y = self.tile.pos
        target_tile_x, target_tile_y = target.tile.pos

        return ((tile_x - target_tile_x)**2 + (tile_y - target_tile_y)**2)**0.5

    def chase(self):
        """
        Pathfinding mode: Targets Pac-Man's tile until the distance to him is less than 8 tiles, when Clyde, instead,
        targets his home corner.
        :return: The next path.
        """
        start_tile = self.tile.pos
        start_tile = (start_tile[0], start_tile[1] - 3)
        if self.euclidean_distance(self.target) > 8:
            target_tile = self.target.tile.pos
        else:
            target_tile = self.home

        target_tile = (target_tile[0], target_tile[1] - 3)

        path = self.search.astar(start_tile, target_tile, self.facing)
        if path is None:
            path = super().chase()
        return path


class Inky(Ghost):
    def __init__(self, resource_pack, target, maze, win_scale, level, blinky):
        """
        Class for Inky (contains home tile, starting position).
        :param resource_pack: Contains the path to the folder containing the skins for the sprite.
        :param target: Pac-Man object. Required to receive updates on which tile Pac-Man is currently on.
        :param maze: Two dimensional list representation of the maze.
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables).
        :param level: Level number, used to determine how long to wait between the two modes: chase (length increases
        over levels) to scatter (length decreases over levels) and how long between becoming scared to returning to
        normal (lowers over levels).
        """

        position = (144, 214)
        super().__init__(resource_pack, position, target, maze, win_scale, level)
        self.home = (26, 32)
        self.blinky = blinky
        self.start_clock_master = 0
        self.start_clock = 0
        self.facing = 'n'
        self.speed_buffer = self._speed
        self._speed = 1

        self.colour = (0, 222, 222)

    def update(self, events):
        """
        Run once a frame, this is the method that controls the start (when Inky is still inside the centre).
        :param events: Contains events from the pg.event.get() call containing all keyboard events.
        :return: None
        """

        if self.start_clock_master > 4:
            if not self.scared:
                self._speed = self.speed_buffer
            super().update(events)
        else:
            self.mode = self.get_mode()
            self.start_clock += 1/60
            self.start_clock_master += 1/60
            if self.start_clock <= 8/60:
                self.facing = 'n'
                self.update_pos('n')
            if 8/60 < self.start_clock <= 16/60:
                self.facing = 's'
                self.update_pos('s')
            elif self.start_clock > 16/60:
                self.start_clock = 0

    def chase(self):
        """
        Pathfinding mode: Takes the vector between Blinky and Pac-Man and doubles it. Adds this vector to Blinky's
        position and target that tile.
        :return: THe next path.
        """

        path = None
        start_tile = self.tile.pos
        start_tile = (start_tile[0], start_tile[1] - 3)

        pac_x, pac_y = self.target.tile.pos
        blinky_x, blinky_y = self.blinky.tile.pos
        vector = (pac_x - blinky_x, pac_y - blinky_y)

        x, y = vector

        target_x, target_y = (pac_x + x, pac_y + y - 3)

        found = False

        try:
            if self.maze.tiles[abs(target_y)][target_x].type == 'pellet':
                path = self.search.astar(start_tile, (target_x, abs(target_y)), self.facing)
                found = True

        except IndexError:
            if target_x > 26:
                target_x = 26  # check these numbers to make sure they are the correct ones
            elif target_x < 1:
                target_x = 1

            if target_y > 29:
                target_y = 29
            elif target_y < 1:
                target_y = y

        if not found:
            for x, y in [(0, 0), (-1, 0), (1, 0), (0, 1), (0, -1)]:
                tile_x_temp = target_x + x
                tile_y_temp = target_y + y
                try:
                    if self.maze.tiles[abs(tile_y_temp)][tile_x_temp].type == 'pellet':
                        break
                    else:
                        continue
                except IndexError:
                    continue

            path = self.search.astar(start_tile, (tile_x_temp, abs(tile_y_temp)), self.facing)

        if path is None:
            path = super().chase()
        return path


class Pellet:
    def __init__(self, skin, tile, predator, win_scale, death_sound, sound_channel, power_pellet=False):
        """
        Class for every pellet in the game.
        :param skin: Contains the picture that is blitted to the screen.
        :param tile: The tile that the pellet is on.
        :param predator: The sprite that can collide with the pellet.
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables).
        :param death_sound: Sound file that plays when a pellet is eaten.
        :param sound_channel: Pellet sound channel (same for all pellets, different one for all power pellets).
        :param power_pellet: Boolean - decides whether or not
        """

        self.power_pellet = power_pellet
        self.eaten = False

        self.skin = skin
        self.tile = tile
        self.predator = predator

        self.x = self.tile.pos[0]
        self.y = self.tile.pos[1]

        self.rect = self.skin.get_rect(center=(
                                                (self.x * 12 * win_scale) + 6 * win_scale,
                                                (self.y * 12 * win_scale) + 6 * win_scale
                                                )
                                       )

        self.sound_channel = sound_channel
        self.death_sound = death_sound

        self.display_clock = 0

    def update(self):
        """
        Runs every frame, just checks whether the pellets is colliding.
        :return: None
        """

        self.check_collision()

    def display(self, win):
        """
        Displays the pellet using the skin. If it's a power pellet it will flash.
        :param win: the current window, all objects must be blitted to this window to be displayed
        :return: None
        """

        if self.power_pellet:
            self.display_clock += 1/60
            if 0.3 > self.display_clock > 0.15:
                win.blit(self.skin, self.rect)
            elif self.display_clock > 0.3:
                self.display_clock = 0
        else:
            win.blit(self.skin, self.rect)

    def check_collision(self):
        """
        If pellet's and Pac-Man's  rectangles are colliding, kill pellet and play death sound.
        :return: None
        """

        if self.rect.colliderect(self.predator.tile.rect):
            if not self.sound_channel.get_busy():
                self.sound_channel.play(self.death_sound)
            self.eaten = True


# add this to GUI
class StaticSprite:
    def __init__(self, skins, rect):
        """
        Essentially just a picture (used to display how many lives the player has left).
        :param skins: The skins that are blitted to the screen (can be one skin).
        :param rect: The sprite's rect (decides where the skin is blitted).
        """

        self.skin_index = 0
        self.skin_cap = 8
        self.skin_count = 0

        self.skins = skins
        self.rect = rect

    def update(self, events):
        self.skin_count += 1
        if self.skin_count == self.skin_cap:
            self.skin_index = abs(self.skin_index-1)
            self.skin_count = 0

    def display(self, win):
        """
        Blits the skin to the window.
        :param win: The current window, all objects must be blitted to this window to be displayed.
        :return: None
        """

        win.blit(self.skins[self.skin_index], self.rect)


"""    def update_tile(self):
        tile_x, tile_y = self.tile.pos
        tiles = []
        tile_update = False

        try:
            tiles = [self.maze.tiles[y + tile_y - 3][x + tile_x] for x, y in [(1, 0), (-1, 0), (0, 1), (0, -1)]]
        except IndexError as e:
            print(e)

        for tile in tiles:
            centre_x, centre_y = self.rect.center
            tile_centre_x, tile_centre_y = tile.rect.center

            if abs(centre_y - tile_centre_y) < self.win_scale * 6 and abs(centre_x - tile_centre_x) < self.win_scale * 6:
                self.previous_tile = self.tile
                self.tile = tile
                self.get_new_move = True
                tile_update = True

        if not tile_update:
            self.get_new_move = False"""


if __name__ == '__main__':
    pass
