import argparse
import sys

import pygit.data as data
import pygit.base as base


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
    read_tree_parser.add_argument("tree")

    commit_tree_parser = commands.add_parser("commit")
    commit_tree_parser.set_defaults(func=commit)
    commit_tree_parser.add_argument("-m", "--message", required=True)

    log_tree_parser = commands.add_parser("log")
    log_tree_parser.set_defaults(func=log)
    log_tree_parser.add_argument("oid", nargs="?")

    commit_parser = commands.add_parser("checkout")
    commit_parser.set_defaults(func=checkout)
    commit_parser.add_argument("commit", help="Oid of the commit to checkout")

    return parser.parse_args()


def init(args):
    data.init()
    print(f"initialised empty pygit directory in {data.GIT_DIR.absolute()}")


def check_initialised(func):
    "Decorator to run before most commands"

    def _func(*args, **kwargs):
        data.check_initialised()
        func(*args, **kwargs)

    return _func


@check_initialised
def hash_object(args):
    with open(args.file, "rb") as fp:
        print(data.hash_object(fp.read()))


@check_initialised
def cat_file(args):
    sys.stdout.buffer.write(data.get_object(args.object, expected=args.type))


@check_initialised
def write_tree(args):
    oid = base.write_tree()
    print(oid)


@check_initialised
def read_tree(args):
    base.read_tree(args.tree)


@check_initialised
def commit(args):
    print(base.commit(args.message))


@check_initialised
def log(args):
    oid = args.oid or data.get_head()
    while oid:
        commit = base.get_commit(oid)

        print(f"commit {oid}")
        print(commit.to_str())
        print()

        oid = commit.parent


@check_initialised
def checkout(args):
    base.checkout(args.commit)
