import argparse
from importlib import import_module


def call(module_name, class_name, function_name):
    mod = import_module(module_name, function_name)
    f = getattr(mod, function_name)
    f()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Shim for calling a function')
    parser.add_argument('--module_name', action="store")
    parser.add_argument('--class_name', action="store")
    parser.add_argument('--function_name', action="store")
    args = parser.parse_args()
    call(args.module_name, args.class_name, args.function_name)
