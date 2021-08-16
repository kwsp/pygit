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

    # Pass this as type to all args that expect oid
    # It handles conversion from tag name to oid
    oid = base.get_oid

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
    cat_file_parser.add_argument("object", type=oid, help="Object identifier")

    write_tree_parser = commands.add_parser("write-tree")
    write_tree_parser.set_defaults(func=write_tree)

    read_tree_parser = commands.add_parser("read-tree")
    read_tree_parser.set_defaults(func=read_tree)
    read_tree_parser.add_argument("tree", type=oid)

    commit_parser = commands.add_parser("commit")
    commit_parser.set_defaults(func=commit)
    commit_parser.add_argument("-m", "--message", required=True)

    log_parser = commands.add_parser("log")
    log_parser.set_defaults(func=log)
    log_parser.add_argument("oid", default="@", type=oid, nargs="?")

    checkout_parser = commands.add_parser("checkout")
    checkout_parser.set_defaults(func=checkout)
    checkout_parser.add_argument(
        "oid", default="@", type=oid, help="Oid of the commit to checkout"
    )

    tag_parser = commands.add_parser("tag")
    tag_parser.set_defaults(func=tag)
    tag_parser.add_argument("name")
    tag_parser.add_argument(
        "oid", default="@", type=oid, help="Oid of the commit/object to tag"
    )

    k_parser = commands.add_parser("k")
    k_parser.set_defaults(func=k)

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
    # Start log at oid if given, else start at HEAD
    oid = args.oid or data.get_ref("HEAD")
    while oid:
        commit = base.get_commit(oid)

        print(f"commit {oid}")
        print(commit.to_str())
        print()

        oid = commit.parent


@check_initialised
def checkout(args):
    base.checkout(args.commit)


@check_initialised
def tag(args):
    base.create_tag(args.name, args.oid)


@check_initialised
def k(_):
    "Output in graphviz DOT format"
    oids = set()
    dot = "digraph commits {\n"
    for refname, ref in data.iter_refs():
        dot += f'"{refname}" [shape=note]\n'
        dot += f'"{refname}" -> "{ref}"\n'
        oids.add(ref)

    for oid in base.iter_commits_and_parents(oids):
        commit = base.get_commit(oid)
        dot += f'"{oid}" [shape=box style=filled label="{oid[:10]}"]\n'
        if commit.parent:
            dot += f'"{oid}" -> "{commit.parent}"\n'

    dot += "}"
    print(dot)
