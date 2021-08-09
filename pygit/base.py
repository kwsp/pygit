from typing import Union, List
import re
import os
import pathlib

from pygit import data

IGNORE_FILE = pathlib.Path(".gitignore")
PATH_T = Union[str, pathlib.Path]

# TODO: implement .gitignore https://git-scm.com/docs/gitignore
IGNORE_LIST: List[str] = [
    ".pygit",
    ".git",
    "venv",
    ".mypy_cache",
    ".vim",
    "__pycache__",
    "pygit.egg-info",
]


def write_tree(dir: PATH_T = "."):
    dirp = pathlib.Path(dir)
    entries = []

    for entry in dirp.iterdir():
        if is_ignored(entry):
            continue

        abspath = entry.absolute()
        _type = "blob"

        if entry.is_file():
            with entry.open("rb") as fp:
                oid = data.hash_object(fp.read())
        elif entry.is_dir():
            _type = "tree"
            oid = write_tree(entry)
        else:
            print("Unrecognised file type:")
            print(abspath)
            breakpoint()

        entries.append((entry.name, oid, _type))

    entries.sort()
    tree = "".join(f"{_type} {oid} {name}\n" for name, oid, _type in entries).encode()

    return data.hash_object(tree, "tree")


def _iter_tree(oid: str):
    if not oid:
        return

    tree = data.get_object(oid, "tree").decode()
    for entry in tree.splitlines():
        _type, oid, name = entry.split(" ", 2)
        yield _type, oid, name


def get_tree(oid: str, base_path: PATH_T = "./") -> dict:
    res = {}
    base_path = pathlib.Path(base_path)
    for _type, oid, name in _iter_tree(oid):
        path = base_path / name
        if _type == "blob":
            res[path] = oid
        elif _type == "tree":
            res.update(get_tree(oid, path))
        else:
            print("Unknown type: ", _type)
            breakpoint()
    return res


def read_tree(tree_oid: str):
    tmp = get_tree(tree_oid)
    for path, oid in tmp.items():
        path.parent.mkdir(exist_ok=True)
        with path.open("wb") as fp:
            fp.write(data.get_object(oid))


def is_ignored(path: pathlib.Path) -> bool:
    return path.name in IGNORE_LIST
