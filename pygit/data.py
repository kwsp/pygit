import hashlib
import pathlib
import sys
import zlib

GIT_DIR = pathlib.Path(".pygit")


def init():
    GIT_DIR.mkdir()
    (GIT_DIR / "HEAD").touch()
    (GIT_DIR / "objects").mkdir()


def check_initialised():
    if not GIT_DIR.exists():
        print("fatal: not a git repository", file=sys.stderr)
        sys.exit(-1)


def set_head(commit_oid: str):
    with (GIT_DIR / "HEAD").open("w") as fp:
        fp.write(commit_oid)


def get_head() -> str:
    with (GIT_DIR / "HEAD").open("r") as fp:
        return fp.read()


def get_oid_path(oid: str) -> pathlib.Path:
    dir = oid[:2]
    fname = oid[2:]
    path = GIT_DIR / "objects" / dir / fname
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


def get_object(oid: str, expected="blob") -> bytes:
    path = get_oid_path(oid)
    if not path.exists():
        print("fatal: not a valid object name", oid, file=sys.stderr)
        sys.exit(-1)

    with path.open("rb") as fp:
        obj = zlib.decompress(fp.read())

    header, _, content = obj.partition(b"\0")
    type_, _, size = header.decode().partition(" ")
    if type_ != expected:
        print(f"Expected {expected}, got {type_}", file=sys.stderr)
        sys.exit(-1)
    return content
