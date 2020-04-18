__author__ = 'Will Evans'

import json
import os.path


def write_settings():
    """
    If there is not a settings file, one will be created.
    :return: None
    """

    file_path = os.path.join('data', 'settings.json')

    with open(file_path, 'w+') as file:
        json.dump(

                    {

                        'win_scale':         2,
                        'music_volume':     50,
                        'game_volume':      50,
                        'user_name':        None,
                        'password':         None,

                    },

                    file)


def get_setting(setting):
    """
    Reads value from chosen setting. If there is no settings file, one will be created.
    :param setting: The setting that should be read from.
    :return: The value of the setting
    """

    file_path = os.path.join('data', 'settings.json')
    while True:
        try:
            if not os.path.exists(file_path):
                write_settings()

            with open(file_path, 'r') as file:
                data = json.load(file)
                return data[setting]

        except (PermissionError, OSError):
            print("settings fetch error")


def save_setting(setting, value):
    """
    Saves a given value to a given setting.
    :param setting: The setting that will be written to.
    :param value: The value that will be written into the setting.
    :return: None
    """

    file_path = os.path.join('data', 'settings.json')
    while True:
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
                data[setting] = value

            with open(file_path, 'w') as file:
                json.dump(data, file)
            break

        except PermissionError:
            print("save failed")

