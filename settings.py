import yaml
import pathlib

from sqlalchemy import MetaData

META_DATA = MetaData()

BASE_DIR = pathlib.Path(__file__).parent

CONFIG_FILE = 'config.yaml'



def load_config():
    with open(CONFIG_FILE) as config_file:
        return yaml.safe_load(config_file)