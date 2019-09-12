import importlib
import argparse
import logging

logging.basicConfig(format='%(message)s')
logging.getLogger().setLevel(logging.INFO)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Initializes environment for distributed LightGBM')
    parser.add_argument('config_file', help='LightGBM config file')
    parser.add_argument('mlist_file', help='LightGBM machine list file')
    args = parser.parse_args()
    utils = importlib.import_module("utils", package=".")
    print(utils.init_lightgbm_env(args.config_file, args.mlist_file))
