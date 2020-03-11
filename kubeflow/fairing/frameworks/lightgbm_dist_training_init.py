from kubeflow.fairing.constants import constants

import importlib
import argparse
import logging

logging.basicConfig(
    level=constants.FAIRING_LOG_LEVEL,
    format=constants.FAIRING_LOG_FORMAT,
    datefmt=constants.FAIRING_LOG_DATEFMT,
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Initializes environment for distributed LightGBM')
    parser.add_argument('config_file', help='LightGBM config file')
    parser.add_argument('mlist_file', help='LightGBM machine list file')
    args = parser.parse_args()
    utils = importlib.import_module("utils", package=".")
    print(utils.init_lightgbm_env(args.config_file, args.mlist_file))
