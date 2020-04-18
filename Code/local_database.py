__author__ = 'Will Evans'
import sqlite3
import json
import datetime
import os.path
import re


def create_users(cursor):
    """
    Creates table 'Users'.
    :param cursor: Object used to execute SQL within the database.
    :return: None
    """

    sql = """CREATE TABLE Users
                         (UserID INTEGER,
                          UserName TEXT,
                          Password TEXT,
                          PRIMARY KEY(UserID))
            """
    cursor.execute(sql)


def create_game_history(cursor):
    """
    Creates table 'GameHistory'.
    :param cursor: Object used to execute SQL within the database.
    :return: None
    """

    sql = """CREATE TABLE GameHistory
                         (GameID INTEGER,
                          UserID INTEGER,
                          MazeID INTEGER,
                          Initials TEXT,
                          Date TEXT,
                          Time TEXT,
                          PRIMARY KEY(GameID),
                          FOREIGN KEY(UserID) REFERENCES  Users(UserID),
                          FOREIGN KEY(MazeID) REFERENCES Mazes(MazeID))
                       """
    cursor.execute(sql)


def create_game_level(cursor):
    """
    Creates table 'GameLevel'.
    :param cursor: Object used to execute SQL within the database.
    :return: None
    """

    sql = """
                CREATE TABLE GameLevel
                          (LevelID INTEGER,
                           GameID INTEGER,
                           LevelNum INTEGER,
                           Lives INTEGER,
                           Score INTEGER,
                           Length INTEGER,
                           PelletsEaten INTEGER,
                           PowerPelletsEaten INTEGER,
                           GhostsEaten INTEGER,
                           PRIMARY KEY(LevelID),
                           FOREIGN KEY(GameID) REFERENCES GameHistory(GameID))
                          
                """
    cursor.execute(sql)


def create_multiplayer_game_history(cursor):
    """
    Creates table 'MultiplayerGameHistory'.
    :param cursor: Object used to execute SQL within the database.
    :return: None
    """

    sql = """CREATE TABLE MultiplayerGameHistory
                          (MultiPlayerGameID INTEGER,
                          GameID INTEGER,
                          PRIMARY KEY(MultiPlayerGameID),
                          FOREIGN KEY(GameID) REFERENCES GameHistory(GameID))
                          
                          """
    cursor.execute(sql)


def create_multiplayer_player_history(cursor):
    """
    Creates table 'MultiplayerPlayerHistory'.
    :param cursor: Object used to execute SQL within the database.
    :return: None
    """

    sql = """"""
    cursor.execute(sql)


def create_mazes(cursor):
    """
    Creates table 'Mazes'.
    :param cursor: Object used to execute SQL within the database.
    :return: None
    """

    sql = """CREATE TABLE Mazes
                          (MazeID INTEGER,
                           UserID INTEGER,
                           Maze TEXT,
                           Date TEXT,
                           PRIMARY KEY(MazeID),
                           FOREIGN KEY(UserID) REFERENCES Users(UserID))
            """
    cursor.execute(sql)

    sql = """
              INSERT INTO Mazes
              (Maze)
              VALUES (?)  

              """

    for maze_id in range(1):
        mazes = ['Level1', 'Level2']
        default_mazes_path = os.path.join('Resources', 'Levels.txt')
        with open(default_mazes_path, 'r') as json_file:
            maze = json.load(json_file)[mazes[maze_id]]

        maze = json.dumps(maze)
        query(sql, (maze,))


def create_db():
    """
    Checks whether the database has already been created and if not creates it.
    :return: None
    """

    if not os.path.exists('data\\database.db'):
        with sqlite3.connect('data\\database.db') as db:
            cursor = db.cursor()

            create_users(cursor)
            create_game_level(cursor)
            create_game_history(cursor)
            create_multiplayer_game_history(cursor)
            create_mazes(cursor)


def query(sql, data=None):
    """
    Used to execute SQL statements, can also return data.
    :param sql: The SQL that will be executed.
    :param data: Data can be added when an SQL statement inputs data into the database.
    :return: Results if there are any.
    """

    db_path = os.path.join('data', 'database.db')
    with sqlite3.connect(db_path) as db:
        cursor = db.cursor()
        if data is None:
            cursor.execute(sql)
        else:
            cursor.execute(sql, data)
        results = cursor.fetchall()
        db.commit()
    return results


def get_game_id(user_id, maze_id):
    """
    Creates a game history entry using the arguments and date, time. Returns the GameID just created.
    :param user_id: Users personal ID
    :param maze_id: MazeID for the maze being played on.
    :return: GameID
    """

    sql = """INSERT INTO GameHistory (UserID, MazeID, Date, Time) VALUES (?, ?, ?, ?)"""
    data = (user_id, maze_id, get_date(), get_time())
    query(sql, data)

    sql = """SELECT Max(GameID) FROM GameHistory"""
    return query(sql)[0][0]


def get_highscore():
    """
    Returns the current high score! In one line! One complex query!
    :return: Highscore
    """

    # This is one complex query!
    return query("""SELECT Max(Scores) FROM(SELECT Sum(Score) as Scores from GameLevel Group BY GameID)""")[0][0]


def save_level(level_num, game_id, lives, score, length, pellets_eaten, power_pellets_eaten, ghosts_eaten):
    """
    Saves Individual level data to GameLevel.
    :param level_num: Level number.
    :param game_id: GameID.
    :param lives: How many lives at the end of the level.
    :param score: Score for that particular level.
    :param length: Length of level.
    :param pellets_eaten: Pellets eaten in level.
    :param power_pellets_eaten: Powerpellets eaten in level.
    :param ghosts_eaten: Ghosts eaten in level.
    :return: None
    """

    sql = """
             INSERT INTO GameLevel 
             (GameID, LevelNum, Lives, Score, Length, PelletsEaten, PowerPelletsEaten, GhostsEaten) 
             VALUES (?, ?, ?, ?, ?, ?, ?, ?)
          """

    query(sql, (game_id, level_num, lives, score, length, pellets_eaten, power_pellets_eaten, ghosts_eaten))


def save_initials(game_id, initials):
    """
    Saves initials to game history after the game has finished.
    :param game_id: GameID that the initials will be assigned to.
    :param initials: 3 Character initials.
    :return: None
    """

    sql = """
          UPDATE GameHistory
          SET Initials=?    
          WHERE GameID=?
          """

    if len(initials) == 3:
        query(sql, (initials, game_id))


def save_maze(user_id, maze):
    """
    After a user has created a maze it can be saved to their account using this function.
    :param user_id: UserID from user who created level.
    :param maze: 2D list of maze.
    :return: None
    """

    sql = """
            INSERT INTO 
            Mazes (UserID, Maze, Date, Time) 
            VALUES (?, ?, ?, ?)
          """
    query(sql, (user_id, json.loads(maze), get_date(), get_time()))


def save_user(username, password):
    """
    When a user has completed the sign up from their information is used to create a user here.
    :param username: The user's chosen username.
    :param password: The user's chosen password.
    :return: None
    """

    sql = """
            INSERT INTO Users (Username, Password) 
            VALUES (?, ?)
          """

    query(sql, (username, password))


def get_maze(maze_id):
    """
    Returns the 2D maze from the database that corresponds to the MazeID.
    :param maze_id:
    :return:
    """

    sql = """
          SELECT Maze 
          FROM Mazes
          WHERE MazeID=?
          """

    return query(sql, (maze_id,))[0][0]


def login(username, password):
    """
    Checks user provided details against database.
    :return: UserID
    """

    sql = """
                SELECT UserID 
                FROM Users 
                WHERE Username=? 
                AND Password=?
          """
    try:
        user_id = query(sql, (username, password))[0][0]
    except IndexError:
        return None
    return user_id


def check_sign_up(user_name, password, password_confirm):
    """
    Performs the following checks in order: Username length, username availability, password length, password strength,
    password matches.
    :param user_name: User's chosen username
    :param password: User's chosen password.
    :param password_confirm: User's chosen password confirm.
    :return: Boolean: whether the details are valid, String: Error message if one of the checks failed. (appropriate for
    given any error).
    """

    # Username Length
    if len(user_name) < 5:
        return False, "Username must be 5 characters"

    # Username availability
    sql = """SELECT EXISTS(SELECT 1 FROM Users WHERE Username=?)"""
    if query(sql, (user_name,))[0][0]:
        return False, "Username taken"

    # Password Length
    if len(password) < 7:
        return False, "Password must be 7 characters"

    # Password Strength
    if not re.search("[a-z]", password):
        return False, "Password must contain lower"

    if not re.search("[A-Z]", password):
        return False, "Password must contain upper"

    if not re.search("[0-9]", password):
        return False, "Password must contain number"

    # Passwords match
    if password != password_confirm:
        return False, "Passwords must match"

    return True, None


def get_username(user_id):
    """
    Returns username from database, given the user_id.
    :param user_id: UserID returned from login earlier.
    :return: Username corresponding to the UserID.
    """

    sql = """SELECT Username FROM Users WHERE UserID=?"""
    return query(sql, (user_id,))[0][0]


def get_statistics(user_id):
    """
    Returns statistics in a list from database corresponding to the given user_id.
    :param user_id:
    """
    
    sql = """
        SELECT
        SUM(Score) as Total_Score, 
        SUM(PelletsEaten) as Pellets_Eaten,
        SUM(PowerPelletsEaten) as Power_Pellets_Eaten,
        SUM(Length) as Time_Played,
        SUM(GhostsEaten) as Ghosts_Eaten
        FROM GameLevel, GameHistory 
        WHERE GameHistory.GameID = GameLevel.GameID AND UserId=? 
        GROUP BY UserID
        """

    database_path = os.path.join('data', 'database.db')
    with sqlite3.connect(database_path) as db:
        db.row_factory = sqlite3.Row
        cursor = db.cursor()
        cursor.execute(sql, (user_id,))
        stats_tuple = cursor.fetchall()

    if len(stats_tuple) is 0:
        return None
    else:
        return dict(stats_tuple[0])


def get_highscores():
    sql = """SELECT Sum(score) as SCORE, GameHistory.Initials
             FROM GameLevel, GameHistory 
             WHERE GameLevel.GameID = GameHistory.GameID
             AND GameHistory.Initials IS NOT NULL
             GROUP BY GameHistory.GameID
             ORDER BY SCORE DESC 
            """

    return query(sql)


def get_date():
    """
    Returns the date in the format: 'dd/mm/yyyy'.
    :return: Date
    """

    return datetime.datetime.now().strftime("%d/%m/%Y")


def get_time():
    """
    Gets time.
    :return: Time.
    """

    return datetime.datetime.now().strftime("%H:%M:%S")


if __name__ == '__main__':
    sql = """
          INSERT INTO Mazes
          (Maze)
          VALUES (?)  

          """

    maze_id = 1
    mazes = ['Level1', 'Level2']
    with open('Resources\\Levels.txt', 'r') as json_file:
       maze = json.load(json_file)[mazes[maze_id - 1]]

    maze = json.dumps(maze)
    query(sql, (maze,))
