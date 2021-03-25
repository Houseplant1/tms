import json
from os.path import isfile
from os import remove, getenv
from typing import Union
import dotenv

dotenv.load_dotenv()
print("[DEBUG] loaded .env")
print(f"\treceiver: {getenv('RECV')}")
print(f"\tfirefox profile: {getenv('FIREFOX_PROFILE')}")
print(f"\tsleep time: {getenv('REFRESH_INTERVAL')}")


def load_json(file_name: str) -> dict:
    """
    load json data from a file

    :param file_name: string indicating the filename to load json from
    :return: json data
    """
    try:
        # open file in read mode
        with open(file_name, "r") as file:
            try:
                # load json data
                data = json.load(file)
            except ValueError as v_e:
                # JLE = json load error
                return {"Error": "JLE", "ErrorMessage": str(v_e)}

            file.close()
            return data

    except FileNotFoundError as f_n_f:
        # FNF = file not found
        return {"Error": "FNF", "ErrorMessage": str(f_n_f)}


# unused
def save_json(file_name: str, data: dict) -> Union[None, dict]:
    """
    save json data to a file

    :param file_name: string indicating the filename to save json to
    :param data: the data to save
    :return: None or dict if error
    """
    # delete the file if already exists
    if isfile(file_name):
        remove(file_name)

    # open file in read mode
    with open(file_name, "w+") as file:
        try:
            # load json data
            json.dump(data, file)
        except ValueError:
            # JLE = json load error
            return {"Error": "JLE"}

        file.close()
        return
