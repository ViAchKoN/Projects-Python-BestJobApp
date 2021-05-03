import os
import pathlib
import yaml


BASE_DIR = pathlib.Path(__file__).parent.absolute()
CONFIG_PATH = os.path.join(BASE_DIR, 'config.yaml')

def get_config(path):
    with open(path) as f:
        config = yaml.safe_load(f)
    return config

CONFIG = get_config(CONFIG_PATH)
