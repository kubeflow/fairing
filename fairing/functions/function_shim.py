import argparse
import cloudpickle

def call(serialized_fn_file):
    with open(serialized_fn_file, 'rb') as f:
        fn = cloudpickle.load(f)
        print(fn())

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Shim for calling a serialized function')
    parser.add_argument('--serialized_fn_file', action="store")
    args = parser.parse_args()
    call(args.serialized_fn_file)
