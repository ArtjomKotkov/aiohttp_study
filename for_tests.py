import yaml
import pathlib

BASE_DIR = pathlib.Path(__file__).parent

CONFIG_FILE = 'config.yaml'



def config_yaml():
    with open(CONFIG_FILE) as config_file:
        return yaml.safe_load(config_file)