import yaml
import pathlib

from sqlalchemy import MetaData

META_DATA = MetaData()

BASE_DIR = pathlib.Path(__file__).parent

CONFIG_FILE = 'config.yaml'

SECRET_KEY = 'be65UP<7cEDz_2OlbD?v3]*y^$uD)KMz7g~L9Qwo|PM4jTgG5wOKR)$]w/&8:71'

def load_config():
    with open(CONFIG_FILE) as config_file:
        return yaml.safe_load(config_file)