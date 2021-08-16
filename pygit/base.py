from typing import Dict, Final, List, NamedTuple, Union
from pathlib import Path

import pygit.data as data
from pygit.defs import *


class GitTreeEntry(NamedTuple):
    name: str
    oid: str
    type: str
    mode: str


def write_tree(dir: PATH_T = "."):
    """
    The structure of a tree object:
        'tree <size>\0<object entries>'
    where each object in <object entries> is
        '<mode> <name>\0<sha-1 digest in binary>'
    https://stackoverflow.com/questions/14790681/what-is-the-internal-format-of-a-git-tree-object
    """
    dirp = Path(dir)
    entries = []

    for entry in dirp.iterdir():
        if is_ignored(entry):
            continue

        abspath = entry.absolute()
        _type = "blob"
        _mode = GIT_MODES.REGULAR_NON_EXECUTABLE_FILE

        if entry.is_symlink():
            # git doesn't care if simlink is file or dir
            _mode = GIT_MODES.SYMBOLIC_LINK
            oid = data.hash_object(bytes(entry.readlink()))

        elif entry.is_file():
            if entry.stat().st_mode & 0b001000000:  # Check if file executable
                _mode = GIT_MODES.REGULAR_EXECUTABLE_FILE

            with entry.open("rb") as fp:
                oid = data.hash_object(fp.read())

        elif entry.is_dir():
            _type = "tree"
            _mode = GIT_MODES.DIRECTORY
            oid = write_tree(entry)
        else:
            raise ValueError("Unrecognised file type for ", abspath)

        entries.append(GitTreeEntry(name=entry.name, oid=oid, type=_type, mode=_mode))

    entries.sort()
    tree = b""
    for name, oid, _, mode in entries:
        tree += f"{mode} {name}\0".encode() + bytes.fromhex(oid)

    return data.hash_object(tree, "tree")


def _iter_tree(oid: str):
    if not oid:
        return

    buf = data.get_object(oid, "tree")
    while buf:
        # extract mode and name
        mode_name, _, buf = buf.partition(b"\0")
        mode, _, name = mode_name.partition(b" ")

        # extract sha1 digest in binary (20 bytes)
        sha1digest = buf[:20]
        buf = buf[20:]

        yield GitTreeEntry(
            name=name.decode(), oid=sha1digest.hex(), type="", mode=mode.decode()
        )


def get_tree(oid: str, base_path: PATH_T = "./") -> Dict[Path, str]:
    res = {}
    base_path = Path(base_path)
    for name, oid, _, mode in _iter_tree(oid):
        path = base_path / name
        if mode == GIT_MODES.DIRECTORY:
            res.update(get_tree(oid, path))
        else:
            res[path] = oid
    return res


def read_tree(tree_oid: str):
    tmp = get_tree(tree_oid)
    for path, oid in tmp.items():
        path.parent.mkdir(exist_ok=True)
        with path.open("wb") as fp:
            fp.write(data.get_object(oid))


class Commit(NamedTuple):
    tree: str  # oid of tree
    parent: str  # oid of parent
    msg: str  # commit message

    def __repl__(self):
        return self.to_str()

    def to_str(self) -> str:
        commit_txt = f"tree {self.tree}\n"
        if self.parent:
            commit_txt += f"parent {self.parent}\n"

        commit_txt += "\n"
        commit_txt += self.msg
        return commit_txt

    @classmethod
    def from_oid(cls, oid: str) -> "Commit":
        tree = ""
        parent = ""
        raw = data.get_object(oid, "commit").decode()
        raw, msg = raw.split("\n\n", 1)

        for line in raw.split("\n"):
            key, val = line.split(" ", 1)
            if key == "tree":
                tree = val
            elif key == "parent":
                parent = val

        return cls(tree=tree, parent=parent, msg=msg)


def commit(msg: str) -> str:
    tree_oid = write_tree()
    HEAD = data.get_ref("HEAD")

    _commit = Commit(tree=tree_oid, parent=HEAD, msg=msg)
    commit_txt = _commit.to_str()
    commit_oid = data.hash_object(commit_txt.encode(), "commit")
    data.update_ref("HEAD", commit_oid)

    return commit_txt


def get_commit(oid: str) -> Commit:
    return Commit.from_oid(oid)


def checkout(commit_oid: str):
    commit = get_commit(commit_oid)
    read_tree(commit.tree)
    data.update_ref("HEAD", commit_oid)


def create_tag(name: str, oid: str):
    data.update_ref(f"refs/tags/{name}", oid)


def get_oid(name: str) -> str:
    "Get oid from a ref name"
    if name == "@":
        name = "HEAD"

    refs_to_try = [
        name,
        f"refs/{name}",
        f"refs/tags/{name}",
        f"refs/heads/{name}",
    ]
    for ref in refs_to_try:
        if oid := data.get_ref(ref):
            return oid

    # check if name is hexdigest
    isHex = False
    try:
        _ = int(name, 16)
    except ValueError:
        pass
    else:
        isHex = True

    if len(name) == 40 and isHex:
        return name
    raise ValueError("Unknown name: ", name)


def is_ignored(path: Path) -> bool:
    return path.name in IGNORE_LIST
