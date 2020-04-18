__author__ = 'Will Evans'

import threading
import socket
import json
import copy
import time


class Connection:
    def __init__(self, user_ip, conn, user_id, players):
        """
        Class for each connection the server has with a client. Controls all information going from server to client.
        :param user_ip: IP for user.
        :param conn: Socket connection used to send and receive data from client.
        :param user_id: A number from 1-4, used to match connection with avatar.
        :param players: List of all players and their information, used to update client's screen.
        """

        self.connected = True
        self.__player_data = {

            'ready': None,
            'client_move': None,

        }

        self.__connected = False
        self.__IP = user_ip
        self.id = user_id
        self.__PORT = 50007
        self.__conn = conn

        # Essential trade of info
        self.send({

                    'client_id': user_id,
                    'players': players

                   })

        self.__player_data['name'] = self.receive()['name']

        threading.Thread(target=self.update).start()

    def update(self):
        """
        Runs once every frame, updates each item in player_data dictionary. Only used at the beginning of the connection
        to share basic information between the client and the host.
        :return: None
        """

        while self.connected:
            data = self.receive()
            if data is not None:
                for attribute, value in data.items():
                    self.__player_data[attribute] = value

    def receive(self):
        """
        Receives data from client (player_data).
        :return: Data in string form (not bytes).
        """

        try:
            data = self.__conn.recv(4096)
            return json.loads(data)
        except Exception as e:
            print("disconnected: {}".format(e))

    def send(self, data):
        """
        Converts data into bytes and sends to client. This is usually the 2D dictionary of player info.
        :param data: Data that is to be sent (player_data).
        :return: None
        """

        if self.connected:
            data = json.dumps(data)
            data = bytes(data, 'utf-8')
            try:
                self.__conn.sendall(data)
            except ConnectionResetError:
                print("disconnected")
                self.connected = False

    def get_player_data(self):
        return self.__player_data

    def get_id(self):
        return self.id

    def close(self):
        """
        When a client quits the connection must be closed. Closes the socket connection and marks the object as not
        connected.
        :return: None
        """

        self.__conn.close()
        self.connected = False


class Server:  # Instantiates whenever a user clicks create game.
    def __init__(self, name):
        """
        Class for server that controls the sending and receiving of game data for each player between the host and
        all clients connected.
        :param name: Host's name. Comes form database based on user's sign in details.
        """

        self.__run = True
        self.test_count = 0
        self.__players_template = {

            0:
                {
                    'name':     '{} [host]'.format(name),
                    'skin':     'pac-man',
                    'score':    0,
                    'ready':    None,
                    'pos':      [167, 318],
                    'move':     None,
                    'countdown': None,
                    'start':    False,
                    'end':      True,
                    'place':    None,
                    'finished': False
                },

            1:
                {
                    'name':     None,
                    'skin':     'blinky',
                    'score':    0,
                    'ready':    None,
                    'pos':      [168, 176],
                    'move':     None,
                    'client_move': None,
                    'place': None
                },

            2:
                {
                    'name':     None,
                    'skin':     'pinky',
                    'score':    0,
                    'ready':    None,
                    'pos':      [168, 214],
                    'move':     None,
                    'client_move': None,
                    'place': None
                },

            3:
                {
                    'name':     None,
                    'skin':     'inky',
                    'score':    0,
                    'ready':    None,
                    'pos':      [144, 214],
                    'move':     None,
                    'client_move': None,
                    'place': None
                },
            4:
                {
                    'name':     None,
                    'skin':     'clyde',
                    'score':    0,
                    'ready':    None,
                    'pos':      [192, 214],
                    'move':     None,
                    'client_move': None,
                    'place': None
                }
            }

        self.__players = copy.deepcopy(self.__players_template)
        self.__IP = self.get_ip()
        self.__port = 50007
        self.__connections = []
        self.__s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.__s.bind((self.__IP, self.__port))

        self.has_ai = False

        self.searching_for_clients = True
        threading.Thread(target=self.connect).start()
        threading.Thread(target=self.receive).start()
        threading.Thread(target=self.check_connections).start()

    def connect(self):
        """
        Before the game starts this method will listen for new connections, and then create a connection when one
        is received.
        :return: None
        """

        while self.searching_for_clients and self.__run:
            self.__s.listen(1)
            if self.searching_for_clients:
                try:
                    conn, addr = self.__s.accept()
                    available_ids = [k for k, v in self.__players.items() if v['name'] is None]
                    client_id = available_ids[0]
                    connection = Connection(addr[0], conn, client_id, self.__players)
                    self.__connections.append(connection)
                except Exception as e:
                    print("Connect: {}".format(e))

    def receive(self):
        """
        This method updates the player data based on information sent my each client to each of the connections. Updates
        twice a second to account for any syncing issues between clients and server.
        :return: None
        """

        while self.__run:
            try:
                for connection in self.__connections:
                    data = connection.get_player_data()
                    for attribute, value in data.items():
                        self.__players[connection.get_id()][attribute] = value
            except Exception as e:
                print(e)
            time.sleep(1/120)

    def update_data(self, client_id, key, value):
        self.__players[client_id][key] = value

    def send_data(self):
        for connection in self.__connections:
            connection.send(self.__players)

    def check_connections(self):
        """
        Runs while the server is running. Checks every connection to see if it is still there, prevents errors with
        connections.
        :return: None
        """

        while self.__run:
            for connection in self.__connections:
                if not connection.connected:
                    connection.close() 
                    self.__players[connection.get_id()] = self.__players_template[connection.get_id()].copy()
                    self.__connections.remove(connection)

            # Limits the number of times the thread can run to save power
            # 1/120 has been chosen to ensure it is run at least once between frames
            time.sleep(1/120)

    def get_data(self, client_id, _type):
        return self.__players[client_id][_type]

    def get_players(self):
        return self.__players

    def get_ip(self):
        return socket.gethostbyname(socket.gethostname())

    def get_client_id(self):
        return 0

    def swap(self, client_id):
        """
        Whichever client_id is passed into this method will become the next Pac-Man. This happens when a ghost catches
        Pac-Man and is needed to swap the skins and start position of players around when they become Pac-Man.
        :param client_id: ClientID of player that is becoming Pac-Man
        :return: None
        """

        pac_man_id = [_id for _id, data in self.__players.items() if data['skin'] == 'pac-man'][0]

        pac_man_skin = "{}".format(self.__players[pac_man_id]['skin'])
        client_skin = "{}".format(self.__players[client_id]['skin'])

        self.__players[pac_man_id]['skin'] = client_skin
        self.__players[client_id]['skin'] = pac_man_skin

    def reset(self):
        """
        At the end of each round the positions of each sprite need to be reset according to the player_template in order
        for the sprites to spawn in the correct place in the following round.
        :return: None
        """

        for client_id, client_data in self.__players.items():
            og_player_data = [og_client_data
                              for og_client_data in self.__players_template.values()
                              if og_client_data['skin'] == client_data['skin']][0]

            client_data['pos'] = og_player_data['pos'][::]

    def add_ai(self):
        """
        Changes name of all available ghosts into 'AI', which will mean they become controlled by AI in the game. This
        method is run when the game countdown is started.
        :return: None
        """

        for client_data in self.__players.values():
            if client_data['name'] is None:
                client_data['name'] = 'AI'
        self.has_ai = True

    def remove_ai(self):
        """
        This changes all AI ghosts back to None when the game countdown is stopped (to allow for more players to join).
        :return:
        """

        for client_data in self.__players.values():
            if client_data['name'] == 'AI':
                client_data['name'] = None
        self.has_ai = False

    def quit(self):
        """
        Correctly adjusts attributes so that all threads and connections terminate when the server is no longer needed.
        :return: None
        """

        self.searching_for_clients = False
        self.__run = False
        for connection in self.__connections:
            connection.close()
        self.__s.close()


class Client:
    def __init__(self, host_ip, name):
        """
        Runs on clients when the user selects join game and enters a GameID.
        :param host_ip: GameID that the user enters. It is actually the host's local IPV4 address.
        :param name: Name of client according to the Users table in the database.
        """

        self.__host_ip = host_ip
        self.__name = name
        self.connected = False
        self.connection_failed = None

        self.__player_data = {

                        'ready':        None,
                        'client_move':  None,

                       }

        self.__port = 50007
        self.__s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.__s.connect((self.__host_ip, self.__port))
            self.connection_failed = False
        except (ConnectionRefusedError, socket.gaierror, TypeError):
            self.connection_failed = True

        if not self.connection_failed:
            # first share of essential data
            init_data = self.receive()
            if init_data is not None:
                self.__client_id = init_data['client_id']
                self.__players = init_data['players']
                self.send({'name': self.__name})

                self.connected = True
                threading.Thread(target=self.update).start()

    def send(self, data):
        data = json.dumps(data)
        data = bytes(data, 'utf-8')
        try:
            self.__s.sendall(data)
        except OSError:
            print("disconnected")

    def receive(self):
        try:
            data = self.__s.recv(1024)
            return json.loads(data)
        except ConnectionResetError as e:
            self.connected = False
            print(e)
        except WindowsError as e:
            self.connected = False
            print(e)
        except Exception as e:
            print(e)

    def update(self):
        """
        Receives data from server and sets equal to players.
        :return: None
        """

        while self.connected:
            data = self.receive()
            if data is not None:
                self.__players = data

    def update_data(self, key, value):
        self.__player_data[key] = value

    def get_data(self, client_id, _type):
        return self.get_players()[client_id][_type]

    def send_player_data(self):
        self.send(self.__player_data)

    def get_players(self):
        """
        Corrects integer keys in players (as they are saved as strings when converted to and from bytes) and returns.
        :return: Dictionary: players
        """
        return {int(k): v for k, v in self.__players.items()}

    def get_client_id(self):
        return self.__client_id  # Ask here if client id is None

    def end(self):
        self.connected = False
        self.__s.close()


if __name__ == "__main__":
    pass
