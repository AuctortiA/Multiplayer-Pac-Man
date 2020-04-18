__author__ = 'Will Evans'

from datastructures import *



class Search:
    def __init__(self, maze):
        """
        Search is an object so that we can save the maze.
        :param maze: 2D list of the maze.
        """

        self.maze = maze

    def astar(self, start, end, facing):
        """
        Mainloop of the search algorithm.
        :param start: Start tile (tilex, tiley).
        :param end: End tile (tilex, tiley).
        :param facing: Direction sprite is currently facing.
        :return: Path in (x, y) format.
        """

        open_queue = PriorityQueue()
        closed_set = []
        start_node = Node(*start, facing)
        start_node.h_score = self.heuristic(start_node, end)
        start_node.g_score = start_node.h_score + start_node.f_score
        open_queue.en_queue(start_node)
        flag = False

        while not open_queue.is_empty():

            # Getting the next node (closest to the goal) to evaluate
            current_node = open_queue.pop()
            closed_set.append(current_node)

            # Checking whether the goal has been reached
            if (current_node.x, current_node.y) == end and flag:
                return current_node.get_path([])

            flag = True

            # Getting adjacent nodes
            children = get_children(current_node, self.maze)

            # Adding newly evaluated nodes to the open_queue if not already evaluated
            for child in children:
                self.evaluate(child, end)
                if not open_queue.has(child):
                    if not in_closed(child, closed_set):
                        open_queue.en_queue(child)

    def evaluate(self, child, end):
        """
        Assigns each child an h score and a g score, then combines these for the f score. These determine the fitness of
        the child, by considering how many nodes there have been before the child and how close the child is to
        the end node. This score is then used to choose the next child to expand.
        :param child: Node object.
        :param end: End tile (tilex, tiley)
        :return: None
        """

        child.h_score = self.heuristic(child, end)
        child.g_score = child.parent.g_score + 1
        child.f_score = child.g_score + child.h_score

    def heuristic(self, node, end):
        return 0


class Dijkstra(Search):
    # Checks all paths
    def __init__(self, maze):
        super().__init__(maze)

    # noinspection PyMethodMayBeStatic
    def heuristic(self, node, end):
        """
        Gives a score based on how close the tile is to the end child. In this case it returns 0, as the default
        heuristic is Dijkstra's which checks every path.
        :param node: Node to be evaluated.
        :param end: End tile (tilex, tiley)
        :return: Score.
        """

        return 0


class Manhattan(Search):
    # Uses Manhattan distance as heuristic (most efficient)
    def __init__(self, maze):
        super().__init__(maze)

    # noinspection PyMethodMayBeStatic
    def heuristic(self, node, end):
        x, y = end
        return abs(node.x - x) + abs(node.y - y)


class Euclidean(Search):
    # Not as efficient as Manhattan as cost of diagonal is the same as east and the north move in Pac-Man
    def __init__(self, maze):
        super().__init__(maze)

    # noinspection PyMethodMayBeStatic
    def heuristic(self, node, end):
        x, y = end
        return ((node.x - x)**2 + (node.y - y)**2)**0.5


def get_children(node, maze):
    """
    Returns next available tiles from current tile. This can then be added to the list of children.
    :param node: Current tile.
    :param maze: 2D list of maze.
    :return: List of children of current tile.
    """

    vectors = {'s': (0, 1), 'e': (1, 0), 'w': (-1, 0), 'n': (0, -1)}
    children = []
    possible_moves = ['n', 'e', 's', 'w', 'n', 'e']
    del vectors[possible_moves[possible_moves.index(node.facing) + 2]]
    for key, value in vectors.items():
        x, y = value
        try:
            # Checking surrounding tiles for walls
            if maze[node.y + y][node.x + x] != 1:
                children.append(Node(node.x + x, node.y + y, key, node))
        except IndexError:
            continue

    return children


def in_closed(child, closed):
    """
    Checks if a child is already in the closed set (already been evaluated).
    :param child: Node object of child to be tested.
    :param closed: List of nodes in closed set.
    :return: Boolean as to whether or not the child is in the closed set.
    """

    for node in closed:
        if node.x == child.x and node.y == child.y:
            return True
    return False
