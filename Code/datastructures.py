__author__ = 'Will Evans'

import json
import local_database
import pygame as pg
import os


class PriorityQueue:

    def __init__(self):
        self.queue = []

    def is_empty(self):
        return len(self.queue) == 0

    def en_queue(self, node):
        self.queue.append(node)

    def pop(self):
        self.queue.sort(key=lambda x: x.f_score)
        return self.queue.pop(0)

    def has(self, child):
        for node in self.queue:
            if node.x == child.x and node.y == child.y:
                return True
        return False


def get_maze(maze_id):
    """
    Gets 2D maze list from database.
    :param maze_id: Each maze in the file has a maze ID
    :return: 2D list of the required maze.
    """

    return json.loads(local_database.get_maze(maze_id))


class Node:
    def __init__(self, x, y, facing, parent=None):
        """
        Every tile in a path (or possible path) is called a node. It has tilex and tiley values and also stores the
        the node object of the tile that came before it in the path.
        :param x: Tile x
        :param y: Tile y
        :param facing: The direction the sprite is currently facing (stops ghosts from being able to turn around).
        :param parent: The node object of the tile before in the path.
        """

        self.x = x
        self.y = y

        self.parent = parent

        self.f_score = 0
        self.h_score = 0
        self.g_score = 0

        self.facing = facing

    def get_path(self, path):
        """
        Recursive algorithm to get the path once the target node has been reached.
        :param path: Path so far
        :return: Path with self added.
        """

        if self.parent is not None:
            path = self.parent.get_path(path)
        path.append((self.x, self.y))
        return path


class Tile:
    def __init__(self, tile_x, tile_y, _type, win_scale, skin):
        """
        Class for a tile, containing the type of tile, position, skin and how to blit it.
        :param tile_x: Tile x-coord (not pixel)
        :param tile_y: Tile y-coord (not pixel)
        :param _type: The tile type stored as a number (directly from maze json file).
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables).
        :param skin: Tile's image.
        """

        self.pos = (tile_x, tile_y)
        self.x = tile_x
        self.y = tile_y

        if _type == 0:
            self.type = 'pellet'
            self.colour = (0, 0, 0)

        elif _type == 1:
            self.type = 'wall'
            self.colour = (0, 0, 255)

        elif _type == 2:
            self.type = 'power_pellet'
            self.colour = (0, 0, 0)

        elif _type == 3:
            self.type = 'ghost_barrier'
            self.colour = (0, 0, 0)

        elif _type == 4:
            self.type = 'empty_tile'
            self.colour = (0, 0, 0)

        elif _type == 5:
            self.type = 'out_of_bounds'
            self.colour = (0, 0, 0)

        elif _type == 6:
            self.type = 'inside'
            self.colour = (0, 0, 0)

        self.skin = skin

        self.rect = pg.Rect(tile_x * 12 * win_scale, tile_y * 12 * win_scale, 12 * win_scale, 12 * win_scale)

    def display(self, win):
        """
        Displays tile.
        :param win: The current window, all objects must be blitted to this window to be displayed.
        :return: None
        """

        if self.type in ['wall', 'ghost_barrier']:
            win.blit(self.skin, self.rect)
        else:
            pg.draw.rect(win, self.colour, self.rect)


class Maze:
    def __init__(self, maze_id, win_scale):
        """
        Class for the whole maze, contains details about all the tiles.
        :param maze: 2D list of all tiles (straight from json file).
        :param win_scale: Window Scale (How large the window is - must be multiplied by all size related variables).
        """

        self.tile_map = get_maze(maze_id)
        self.win_scale = win_scale
        self.tiles = self.get_tiles('blue')
        self.skin_colour = 'blue'

    def get_tiles(self, skin_colour):
        """
        Gets list off tile objects based on the tile_map.
        :param skin_colour: This will decide which colour (blue or white) each tile is.
        :return: A 2D list of tile objects.
        """

        tiles = []
        for y, row in enumerate(self.tile_map):
            tiles.append([])
            for x, data in enumerate(row):
                if data == 1:
                    skin_name = f'{self.get_skin(x, y, self.tile_map)}.png'
                    skin_address = os.path.join('Resources', 'sprites', 'walls', skin_colour, skin_name)
                    skin = pg.transform.scale(pg.image.load(skin_address), (12 * self.win_scale, 12 * self.win_scale))

                elif data == 3:
                    skin_address = os.path.join('Resources', 'sprites', 'walls', skin_colour, 'ghost_barrier.png')
                    skin = pg.transform.scale(pg.image.load(skin_address), (12 * self.win_scale, 12 * self.win_scale))
                else:
                    skin = None
                tiles[y].append(Tile(x, y + 3, data, self.win_scale, skin))

        return tiles

    def change_skin(self):
        """
        Changes the colour of all tiles in the 2D list.
        :return: None
        """

        if self.skin_colour == 'blue':
            self.skin_colour = 'white'
        else:
            self.skin_colour = 'blue'
        self.tiles = self.get_tiles(self.skin_colour)

    def display(self, win):
        """
        Displays the maze, by displaying each individual tile.
        :param win: The current window, all objects must be blitted to this window to be displayed.
        :return: None
        """

        for row in self.tiles:
            for tile in row:
                tile.display(win)

    # noinspection PyMethodMayBeStatic
    def get_skin(self, tile_x, tile_y, tile_map):
        """
        Works out what skin each tile should have based on the type of tile in the surrounding 8 spaces.
        :param tile_x: x coord of tile.
        :param tile_y: y coord of tile.
        :param tile_map: The 2D list of tiles from the maze json file.
        :return: String name of skin for the tile specified by the x, y position.
        """

        tile_map = [[0 if x == 2 else x for x in row] for row in tile_map]

        # get adjacency list
        adjacent = {}
        vectors = {'s': (0, 1),
                   'e': (1, 0),
                   'w': (-1, 0),
                   'n': (0, -1),
                   'ne': (1, -1),
                   'se': (1, 1),
                   'sw': (-1, 1),
                   'nw': (-1, -1)
                   }

        for key, value in vectors.items():
            x, y = value
            try:
                new_x = tile_x + x
                new_y = tile_y + y

                if new_x < 0 or new_y < 0:
                    adjacent.update({key: None})
                    continue

                adjacent.update({key: tile_map[tile_y + y][tile_x + x]})
            except IndexError:
                adjacent.update({key: None})

        values = tuple(list(adjacent.values())[:4])
        values_diag = tuple(adjacent.values())

        # ghost edges
        if values == (4, 3, 1, 4):
            return 'left_end_ghost'

        if values == (4, 1, 3, 4):
            return 'right_end_ghost'

        if values == (4, 1, 1, 4) and tile_y == 12:
            return 'lower_boundary'

        if values == (4, 1, 1, 4) and tile_y == 16:
            return 'upper_boundary'

        if values == (1, 4, 4, 1) and tile_x == 10:
            return 'right_boundary'

        if values == (1, 4, 4, 1) and tile_x == 17:
            return 'left_boundary'

        # ghost corners
        if values_diag == (1, 1, 4, 4, 4, 4, 4, 4):
            return 'left_upper_corner_ghost'

        if values_diag == (1, 4, 1, 4, 4, 4, 4, 4):
            return 'right_upper_corner_ghost'

        if values_diag == (4, 4, 1, 1, 4, 4, 4, 4):
            return 'right_lower_corner_ghost'

        if values_diag == (4, 1, 4, 1, 4, 4, 4, 4):
            return 'left_lower_corner_ghost'

        # boundaries edges
        values_temp = tuple([1 if x is None else x for x in values])

        if values == (0, 1, 1, None) or values == (0, 1, 1, 5) or values_temp == (4, 1, 1, 5):
            return 'upper_boundary'

        if values == (None, 1, 1, 0) or values == (5, 1, 1, 0) or values_temp == (5, 1, 1, 4):
            return 'lower_boundary'

        if values == (1, 0, None, 1) or values == (1, 0, 4, 1) or values == (1, 0, 5, 1):
            return 'left_boundary'

        if values == (1, None, 0, 1) or values == (1, 4, 0, 1) or values == (1, 5, 0, 1):
            return 'right_boundary'

        # boundary spits
        if values_diag == (1, 1, 1, None, None, 1, 0, None):
            return 'upper_left_spit_boundary'

        if values_diag == (1, 1, 1, None, None, 0, 1, None):
            return 'upper_right_spit_boundary'

        if values_diag == (None, 1, 1, 1, 1, None, None, 0):
            return 'lower_left_spit_boundary'

        if values_diag == (None, 1, 1, 1, 0, None, None, 1):
            return 'lower_right_spit_boundary'

        if values_diag == (1, None, 1, 1, None, None, 1, 0):
            return 'right_upper_spit_boundary'

        if values_diag == (1, None, 1, 1, None, None, 0, 1):
            return 'right_lower_spit_boundary'

        if values_diag == (1, 1, None, 1, 1, 0, None, None):
            return 'left_lower_spit_boundary'

        if values_diag == (1, 1, None, 1, 0, 1, None, None):
            return 'left_upper_spit_boundary'

        # boundary corners
        if values == (1, 1, None, None) or values == (1, 1, None, 5):
            return 'left_upper_boundary'

        if values == (1, None, 1, None) or values == (1, None, 1, 5):
            return 'right_upper_boundary'

        if values == (None, None, 1, 1) or values == (5, None, 1, 1):
            return 'right_lower_boundary'

        if values == (None, 1, None, 1) or values == (5, 1, None, 1):
            return 'left_lower_boundary'

        # corners
        values_temp = tuple([0 if x == 4 else x for x in values])
        values_diag_temp = tuple([0 if x == 4 else x for x in values_diag])

        if values_temp == (1, 1, 0, 0):
            return 'left_upper_corner'

        if values_temp == (1, 0, 1, 0):
            return 'right_upper_corner'

        if values_temp == (0, 1, 0, 1):
            return 'left_lower_corner'

        if values_temp == (0, 0, 1, 1):
            return 'right_lower_corner'

        if values_diag_temp == (1, 1, 1, 1, 1, 0, 1, 1):
            return 'left_upper_inside_corner'

        if values_diag_temp == (1, 1, 1, 1, 1, 1, 0, 1):
            return 'right_upper_inside_corner'

        if values_diag_temp == (1, 1, 1, 1, 0, 1, 1, 1):
            return 'left_lower_inside_corner'

        if values_diag_temp == (1, 1, 1, 1, 1, 1, 1, 0):
            return 'right_lower_inside_corner'

        # edges
        values_temp = tuple([1 if x == 6 else x for x in [0 if x == 4 else x for x in values]])
        if values_temp == (1, 1, 1, 0):
            return 'upper_edge'

        if values_temp == (1, 1, 0, 1):
            return 'right_edge'

        if values_temp == (0, 1, 1, 1):
            return 'lower_edge'

        if values_temp == (1, 0, 1, 1):
            return 'left_edge'

        return 'temp'
