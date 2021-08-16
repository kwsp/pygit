from typing import Optional
from pathlib import Path
import hashlib
import sys
import zlib

from pygit.defs import *

GIT_ROOT = Path(".")
GIT_DIR = Path(".pygit")


def set_git_root(path: PATH_T):
    global GIT_ROOT
    GIT_ROOT = Path(path)


def init():
    # TODO: check if we are inside a git directory already
    # Create the git directory
    GIT_DIR.mkdir()

    (GIT_DIR / "HEAD").touch()
    (GIT_DIR / "objects").mkdir()
    (GIT_DIR / "refs").mkdir()


def check_initialised():
    if not GIT_DIR.exists():
        print("fatal: not a git repository", file=sys.stderr)
        sys.exit(-1)


def update_ref(ref: str, oid: str):
    path = GIT_DIR / ref
    path.parent.mkdir(exist_ok=True)
    with path.open("w") as fp:
        fp.write(oid)


def get_ref(ref: str) -> Optional[str]:
    path = GIT_DIR / ref
    if path.exists():
        with path.open("r") as fp:
            return fp.read().strip()
    return None


def get_oid_path(oid: str) -> Path:
    _dir = oid[:2]
    fname = oid[2:]
    path = GIT_ROOT / GIT_DIR / "objects" / _dir / fname
    return path


def hash_object(data: bytes, p_type="blob") -> str:
    _size = len(data)
    header = f"{p_type} {_size}\0".encode()
    obj = header + data
    oid = hashlib.sha1(obj).hexdigest()
    path = get_oid_path(oid)
    if not path.exists():
        path.parent.mkdir(exist_ok=True)
    with path.open("wb") as fp:
        fp.write(zlib.compress(obj))
    return oid


def get_object(oid: str, expected="blob", git_root: PATH_T = GIT_DIR) -> bytes:
    path = get_oid_path(oid)
    if not path.exists():
        print("fatal: not a valid object name", oid, file=sys.stderr)
        sys.exit(-1)

    with path.open("rb") as fp:
        obj = zlib.decompress(fp.read())

    header, _, content = obj.partition(b"\0")
    type_, _, size = header.decode().partition(" ")
    if type_ != expected:
        print(f"Expected oid of type {expected}, got {type_}", file=sys.stderr)
        sys.exit(-1)
    return content


def iter_refs():
    refs = ["HEAD"]
    for path in (GIT_DIR / "refs").glob("**/*"):
        if path.is_dir():
            continue
        relpath = path.relative_to(GIT_DIR)
        refs.append(relpath)

    for ref in refs:
        yield ref, get_ref(ref)
