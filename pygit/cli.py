import argparse
import sys

from pygit import data
from pygit import base


def main():
    args = parse_args()
    args.func(args)


def parse_args():
    parser = argparse.ArgumentParser()

    commands = parser.add_subparsers(dest="command")
    commands.required = True

    init_parser = commands.add_parser("init")
    init_parser.set_defaults(func=init)

    hash_object_parser = commands.add_parser("hash-object")
    hash_object_parser.set_defaults(func=hash_object)
    hash_object_parser.add_argument("file")

    cat_file_parser = commands.add_parser("cat-file")
    cat_file_parser.set_defaults(func=cat_file)
    cat_file_parser.add_argument(
        "type",
        choices=["blob", "tree", "commit", "log"],
        help="Object type",
    )
    cat_file_parser.add_argument("object", help="Object identifier")

    write_tree_parser = commands.add_parser("write-tree")
    write_tree_parser.set_defaults(func=write_tree)

    read_tree_parser = commands.add_parser("read-tree")
    read_tree_parser.set_defaults(func=read_tree)
    read_tree_parser.add_argument('tree')

    return parser.parse_args()


def init(args):
    data.init()
    print(f"initialised empty pygit directory in {data.GIT_DIR.absolute()}")


def hash_object(args):
    data.check_initialised()
    with open(args.file, "rb") as fp:
        print(data.hash_object(fp.read()))


def cat_file(args):
    data.check_initialised()
    print(data.get_object(args.object, expected=args.type).decode())


def write_tree(args):
    data.check_initialised()
    oid = base.write_tree()
    print(oid)

def read_tree(args):
    data.check_initialised()
    base.read_tree(args.tree)
