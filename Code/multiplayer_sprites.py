__author__ = 'Will Evans'

import sprites
import pygame as pg
import random
import os
from pathfinding import Manhattan as Search


class ClientPacMan(sprites.PacMan):
    def __init__(self, resource_pack, maze, win_scale, client, client_id):
        """
        Client-side Pac-Man sprite that takes input from another client or possibly the server (not from keyboard).
        :param resource_pack: Contains the path to the folder containing the skins for the sprite.
        :param maze: Two dimensional list representation of the maze.
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables).
        :param client: Client object from networking module (controls the sending and receiving of player data.
        :param client_id: ClientID (comes client object, but is stored in multiplayer section).
        """

        super().__init__(resource_pack, maze, win_scale)
        self.client = client
        self.client_id = client_id

    # get rid of stupid returns
    def update(self, events):
        """
        Gets input from Client object.
        :param events: Needed to keep the same signature, but not used.
        :return: None.
        """

        if not self.dead:

            move = self.client.get_data(self.client_id, 'move')
            pos = self.client.get_data(self.client_id, 'pos')
            self.facing, self.skin = self.get_skin(move)
            if move is not None:
                self.skin_clock += 1
            else:
                if not self.sound_channel.get_busy():
                    self.sound_channel.play(self.sounds['siren.wav'])
            self.update_pos(pos)
        else:
            if self.death_animation():
                return None
        return self.dead

    def update_pos(self, pos):
        # from here
        self.x, self.y = pos

        # i moved this if its broken might be this
        self.update_tile()
        
        self.x *= self.win_scale
        self.y *= self.win_scale

        self.skin_rect = self.skins['{}_{}.png'.format(self.facing, self.skin)].get_rect(center=(self.x, self.y))
        self.rect = pg.Rect(self.x - int(6 * self.win_scale),
                            self.y - int(6 * self.win_scale),
                            12 * self.win_scale,
                            12 * self.win_scale)


class ClientPlayerPacMan(ClientPacMan):
    def __init__(self, resource_pack, maze, win_scale, client, client_id):
        """
        Client-side Pac-Man sprite that is controlled by keyboard inputs.
        :param resource_pack: Contains the path to the folder containing the skins for the sprite.
        :param maze: Two dimensional list representation of the maze.
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables).
        :param client: Client object from networking module (controls the sending and receiving of player data.
        :param client_id: ClientID (comes client object, but is stored in multiplayer section).
        """

        super().__init__(resource_pack, maze, win_scale, client, client_id)

    def update(self, events):
        """
        Sends client move to server.
        :param events: Used to get keyboard inputs.
        :return: None.
        """

        self.client.update_data('client_move', self.get_input(events))
        self.client.send_player_data()

        super().update(events)

    def get_input(self, events):
        """
        Gets inputs from keyboard events.
        :param events: Used to get keyboard inputs.
        :return: Buffer move, so that if there isn't a keyboard input the last input will be returned.
        """

        for event in events:
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_UP:
                    self.buffer_move = 'n'
                elif event.key == pg.K_RIGHT:
                    self.buffer_move = 'e'
                elif event.key == pg.K_DOWN:
                    self.buffer_move = 's'
                elif event.key == pg.K_LEFT:
                    self.buffer_move = 'w'

        return self.buffer_move


class ClientGhost(sprites.Ghost):
    def __init__(self, resource_pack, position, target, maze, win_scale, level, client, client_id):
        """
        Client-side ghost sprite that takes input from another client or possibly the server (not from keyboard).
        :param resource_pack: Contains the path to the folder containing the skins for the sprite.
        :param position: Position that sprite should spawn in (needed as ghosts can have different starting positions
        depending on skin.
        :param target: Pac-Man object
        :param maze: Two dimensional list representation of the maze.
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables).
        :param level: Level number (used if ghost is AI to determine difficulty).
        :param client: Client object from networking module (controls the sending and receiving of player data.
        :param client_id: ClientID (comes client object, but is stored in multiplayer section).
        """

        super().__init__(resource_pack, position, target, maze, win_scale, level)

        self.client = client
        self.client_id = client_id

    def update(self, events):
        """
        Gets input from Client object.
        :param events: Needed to keep the same signature, but not used.
        :return: None.
        """

        move = self.client.get_data(self.client_id, 'move')
        pos = self.client.get_data(self.client_id, 'pos')
        self.check_collision()
        self.facing, self.skin = self.get_skin(move)
        self.update_tile()
        self.update_pos(pos)
        self.get_mode()

    def update_pos(self, pos):
        self.x, self.y = pos
        self.x *= self.win_scale
        self.y *= self.win_scale

        self.skin_rect = self.skins['{}_{}.png'.format(self.facing, self.skin)].get_rect(center=(self.x, self.y))
        self.rect = pg.Rect(self.x - int(6 * self.win_scale),
                            self.y - int(6 * self.win_scale),
                            12 * self.win_scale,
                            12 * self.win_scale)


class ClientPlayerGhost(ClientGhost):
    def __init__(self, resource_pack, position, target, maze, win_scale, level, client, client_id):
        """
        Client-side Ghost sprite that is controlled by keyboard inputs.
        :param resource_pack: Contains the path to the folder containing the skins for the sprite.
        :param position: Position that sprite should spawn in (needed as ghosts can have different starting positions
        depending on skin.
        :param target: Pac-Man object
        :param maze: Two dimensional list representation of the maze.
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables).
        :param level: Level number (used if ghost is AI to determine difficulty).
        :param client: Client object from networking module (controls the sending and receiving of player data.
        :param client_id: ClientID (comes client object, but is stored in multiplayer section).
        """

        super().__init__(resource_pack, position, target, maze, win_scale, level, client, client_id)
        self.client = client
        # change to spotlights
        spotlight_size = (864 * win_scale, 864 * win_scale)
        spotlight_path = os.path.join('resources', 'sprites', 'spotlights', '12x12.png')
        self.spotlight = pg.transform.scale(pg.image.load(spotlight_path), spotlight_size)

    def update(self, events):
        """
        Sends client move to server.
        :param events: Used to get keyboard inputs.
        :return: None.
        """

        self.client.update_data('client_move', self.get_input(events))
        self.client.send_player_data()
        super().update(events)

    def display(self, win):
        """
        Blits sprite skin to window, and also a spotlight (after the maze, pellets and Pac-Man), but before the other
        ghosts and score.
        :param win: The current window, all objects must be blitted to this window to be displayed.
        :return: None
        """

        win.blit(self.skins['{}_{}.png'.format(self.facing, self.skin)], self.skin_rect)
        win.blit(self.spotlight, self.spotlight.get_rect(center=self.skin_rect.center))

    def get_input(self, events):
        """
        Gets inputs from keyboard events.
        :param events: Used to get keyboard inputs.
        :return: Buffer move, so that if there isn't a keyboard input the last input will be returned.
        """

        for event in events:
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_UP:
                    self.buffer_move = 'n'
                elif event.key == pg.K_RIGHT:
                    self.buffer_move = 'e'
                elif event.key == pg.K_DOWN:
                    self.buffer_move = 's'
                elif event.key == pg.K_LEFT:
                    self.buffer_move = 'w'

        return self.buffer_move



class ServerPacMan(sprites.PacMan):
    def __init__(self, resource_pack, maze, win_scale, server, client_id):
        """
        Server-side Pac-Man sprite controlled by another client.
        :param resource_pack: Contains the path to the folder containing the skins for the sprite.
        :param maze: Two dimensional list representation of the maze.
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables).
        :param client: Client object from networking module (controls the sending and receiving of player data.
        :param client_id: ClientID (comes client object, but is stored in multiplayer section).
        """

        super().__init__(resource_pack, maze, win_scale)
        self.server = server
        self.client_id = client_id

    # fix this one too
    def update(self, events):
        """
        Gets input from Server object, as the get_move method has been overridden below.
        :param events: Needed to keep the same signature, but not used.
        :return: None.
        """

        super().update(events)

        pos = [coord / self.win_scale for coord in [self.x, self.y]]
        self.server.update_data(self.client_id, 'pos', pos)
        self.server.update_data(self.client_id, 'move', self.online_move)
        return self.dead

    def get_move(self, events):
        move = self.server.get_data(self.client_id, 'client_move')

        self.buffer_move = move

        return self.check_move(self.buffer_move)

    def update_score(self, score):
        self.server.update_data(self.client_id, 'score', score)


# Server side ghost
class ServerGhost(sprites.Ghost):
    def __init__(self, resource_pack, position, target, maze, win_scale, level, server, client_id):
        """
        Server-side ghost that is controlled by clients.
        :param resource_pack: Contains the path to the folder containing the skins for the sprite.
        :param position: Position that sprite should spawn in (needed as ghosts can have different starting positions
        depending on skin.
        :param target: Pac-Man object
        :param maze: Two dimensional list representation of the maze.
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables).
        :param level: Level number (used if ghost is AI to determine difficulty).
        :param server: Server object from networking module (controls the sending and receiving of player data.
        :param client_id: ClientID (comes client object, but is stored in multiplayer section).
        """

        super().__init__(resource_pack, position, target, maze, win_scale, level)
        self.server = server
        self.client_id = client_id
        self.respawned = True
        self.buffer_move = self.facing

    def update(self, events):
        """
        Validates client input (from server object) and sends back a valid move.
        :param events: Used to get keyboard events.
        :return: None
        """

        super().update(events)

        pos = [coord / self.win_scale for coord in [self.x, self.y]]
        self.server.update_data(self.client_id, 'pos', pos)
        self.server.update_data(self.client_id, 'move', self.online_move)

    def get_move(self, events):
        """
        Gets move from server object and returns a validated move.
        :param events: Used to get keyboard inputs.
        :return: Valid move.
        """

        if self.dead or self.respawned:
            self.buffer_move = super().get_move(events)
            return self.buffer_move
        else:
            move = self.server.get_data(self.client_id, 'client_move')
            if move is not None:
                self.buffer_move = move

        return self.check_move(self.buffer_move)

    def add_points(self, points):
        """
        Updates points for that particular player based on interactions the sprite has server side.
        :param points: Points to be added to player's total.
        :return: None.
        """

        score = self.server.get_data(self.client_id, 'score')
        self.server.update_data(self.client_id, 'score', score + points)


class ServerPlayerPacMan(sprites.PacMan):
    def __init__(self, resource_pack, maze, win_scale, server):
        """
        Server-side Pac-Man sprite controlled by keyboard inputs.
        :param resource_pack: Contains the path to the folder containing the skins for the sprite.
        :param maze: Two dimensional list representation of the maze.
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables).
        :param server: Server object from networking module (controls the sending and receiving of player data.
        """

        super().__init__(resource_pack, maze, win_scale)
        self.server = server
        self.client_id = 0

    def update(self, events):
        """
        Sends move and pos to server object.
        :param events: Used to get keyboard events.
        :return: None.
        """

        super().update(events)

        pos = [coord / self.win_scale for coord in [self.x, self.y]]
        self.server.update_data(self.client_id, 'move', self.online_move)
        self.server.update_data(self.client_id, 'pos', pos)

        return self.dead

    def update_score(self, score):
        self.server.update_data(self.client_id, 'score', score)


class ServerPacManAI(sprites.PacMan):
    def __init__(self, resource_pack, maze, win_scale, server, client_id):
        """
        Server-side Pac-Man AI. Makes random moves and sends to server object.
        :param resource_pack: Contains the path to the folder containing the skins for the sprite.
        :param maze: Two dimensional list representation of the maze.
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables).
        :param server: Server object from networking module (controls the sending and receiving of player data.
        :param client_id: ClientID (comes client object, but is stored in multiplayer section).
        """

        super().__init__(resource_pack, maze, win_scale)
        self.server = server
        self.client_id = client_id

        # Search
        self.search = Search(maze.tile_map)

        # Path finding
        self.path = self.get_path()
        self.next_coords = self.path[1]

        self.next_x = 0
        self.next_y = 0

        self.axis_change = 'x'

    def update(self, events):
        """
        Updates server with move.
        :param events: Used to get keyboard events.
        :return: None.
        """

        super().update(events)

        pos = [coord / self.win_scale for coord in [self.x, self.y]]
        self.server.update_data(self.client_id, 'move', self.online_move)
        self.server.update_data(self.client_id, 'pos', pos)

        return self.dead

    def get_move(self, events):
        """
        Gets move by working out the move needed to reach the next tile in the path that is worked out by randomly
        selecting a tile before hand.
        :param events: Used to get keyboard events.
        :return: Next move.
        """

        if self.tile.pos[1] == 17:
            if self.tile.pos[0] <= 5 or self.tile.pos[0] >= 22:
                if self.tile.pos[0] == 5 or self.tile.pos[0] == 22:
                    self.next_coords = self.get_path()[1]
                return self.facing

        tile_x, tile_y = self.tile.pos
        x, y = self.next_coords

        if x == tile_x and y == tile_y - 3:
            try:
                self.next_coords = self.get_path()[1]
            except TypeError as e:
                print(e)
        x, y = self.next_coords
        y += 3

        x *= 12 * self.win_scale
        x += 6 * self.win_scale

        y *= 12 * self.win_scale
        y += 6 * self.win_scale

        self.next_x = x
        self.next_y = y

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

    def get_path(self):
        """
        Gets path to random pellet tile.
        :return: Path
        """

        start_tile = self.tile.pos
        chosen_row = random.choice(self.maze.tiles[1:-1])
        pellet_tiles = [tile for tile in chosen_row if tile.type == 'pellet']
        target_tile = random.choice(pellet_tiles).pos
        start_tile = (start_tile[0], start_tile[1] - 3)
        target_tile = (target_tile[0], target_tile[1] - 3)
        return self.search.astar(start_tile, target_tile, self.facing)

    def update_score(self, score):
        self.server.update_data(self.client_id, 'score', score)


# Server side ghost controlled by the server player
class ServerPlayerGhost(sprites.Ghost):
    def __init__(self, resource_pack, position, target, maze, win_scale, level, server):
        """
        Server-side ghost sprite controlled by keyboard inputs.
        :param resource_pack: Contains the path to the folder containing the skins for the sprite.
        :param position: Position that sprite should spawn in (needed as ghosts can have different starting positions
        depending on skin.
        :param target: Pac-Man object
        :param maze: Two dimensional list representation of the maze.
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables).
        :param level: Level number (used if ghost is AI to determine difficulty).
        :param server: Server object from networking module (controls the sending and receiving of player data.
        """

        super().__init__(resource_pack, position, target, maze, win_scale, level)
        self.server = server
        self.client_id = 0
        self.respawned = True
        self.buffer_move = self.facing
        self.spotlight = pg.transform.scale(pg.image.load('resources\\sprites\\spotlights\\12x12.png'),
                                            (864 * win_scale, 864 * win_scale))

    def update(self, events):
        """
        Gets move from keyboard inputs and then sends to server object.
        :param events: Used to get keyboard events.
        :return: None.
        """
        super().update(events)

        pos = [coord / self.win_scale for coord in [self.x, self.y]]
        self.server.update_data(self.client_id, 'pos', pos)
        self.server.update_data(self.client_id, 'move', self.online_move)

    def display(self, win):
        win.blit(self.skins['{}_{}.png'.format(self.facing, self.skin)], self.skin_rect)
        win.blit(self.spotlight, self.spotlight.get_rect(center=self.skin_rect.center))

    def get_move(self, events):
        """
        Gets move using keyboard events.
        :param events: Used to get keyboard events.
        :return: Validated move.
        """

        if self.dead or self.respawned:
            self.buffer_move = super().get_move(events)
            return self.buffer_move
        else:
            move = self.get_input(events)
            if move is not None:
                self.buffer_move = move

        return self.check_move(self.buffer_move)

    def get_input(self, events):
        for event in events:
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_UP:
                    self.buffer_move = 'n'
                elif event.key == pg.K_RIGHT:
                    self.buffer_move = 'e'
                elif event.key == pg.K_DOWN:
                    self.buffer_move = 's'
                elif event.key == pg.K_LEFT:
                    self.buffer_move = 'w'

        return self.buffer_move

    def add_points(self, points):
        score = self.server.get_data(self.client_id, 'score')
        self.server.update_data(self.client_id, 'score', score + points)


class ServerBlinky(sprites.Blinky):
    def __init__(self, resource_pack, target, maze, win_scale, level, server, client_id):

        super().__init__(resource_pack, target, maze, win_scale, level)
        self.server = server
        self.client_id = client_id

    def update(self, events):
        super().update(events)
        self.server.update_data(self.client_id, 'move', self.facing)
        pos = [coord / self.win_scale for coord in [self.x, self.y]]
        self.server.update_data(self.client_id, 'pos', pos)

    def add_points(self, points):
        score = self.server.get_data(self.client_id, 'score')
        self.server.update_data(self.client_id, 'score', score + points)


class ServerPinky(sprites.Pinky):
    def __init__(self, resource_pack, target, maze, win_scale, level, server, client_id):
        super().__init__(resource_pack, target, maze, win_scale, level)
        self.server = server
        self.client_id = client_id

    def update(self, events):
        super().update(events)
        self.server.update_data(self.client_id, 'move', self.facing)
        pos = [coord / self.win_scale for coord in [self.x, self.y]]
        self.server.update_data(self.client_id, 'pos', pos)

    def add_points(self, points):
        score = self.server.get_data(self.client_id, 'score')
        self.server.update_data(self.client_id, 'score', score + points)


class ServerInky(sprites.Inky):
    def __init__(self, resource_pack, target, maze, win_scale, level, blinky, server, client_id):
        super().__init__(resource_pack, target, maze, win_scale, level, blinky)
        self.server = server
        self.client_id = client_id

    def update(self, events):
        super().update(events)
        self.server.update_data(self.client_id, 'move', self.facing)
        pos = [coord / self.win_scale for coord in [self.x, self.y]]
        self.server.update_data(self.client_id, 'pos', pos)

    def add_points(self, points):
        score = self.server.get_data(self.client_id, 'score')
        self.server.update_data(self.client_id, 'score', score + points)


class ServerClyde(sprites.Clyde):
    def __init__(self, resource_pack, target, maze, win_scale, level, server, client_id):
        super().__init__(resource_pack, target, maze, win_scale, level)
        self.server = server
        self.client_id = client_id

    def update(self, events):
        super().update(events)
        self.server.update_data(self.client_id, 'move', self.facing)
        pos = [coord / self.win_scale for coord in [self.x, self.y]]
        self.server.update_data(self.client_id, 'pos', pos)

    def add_points(self, points):
        score = self.server.get_data(self.client_id, 'score')
        self.server.update_data(self.client_id, 'score', score + points)
