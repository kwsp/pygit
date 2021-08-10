from typing import Final, List, NamedTuple, Union
from pathlib import Path

IGNORE_FILE = Path(".gitignore")
PATH_T = Union[str, Path]

# TODO: implement .gitignore https://git-scm.com/docs/gitignore
IGNORE_LIST: List[str] = [
    ".pygit",
    ".git",
    "venv",
    ".mypy_cache",
    ".vim",
    "__pycache__",
    "pygit.egg-info",
    ".vscode",
]


class _GIT_MODES(NamedTuple):
    """
    Valid path modes
    """

    DIRECTORY: str = "40000"
    REGULAR_NON_EXECUTABLE_FILE: str = "100644"
    REGULAR_EXECUTABLE_FILE: str = "100755"
    SYMBOLIC_LINK: str = "120000"
    GITLINK: str = "160000"


# valid file modes in git
# https://stackoverflow.com/questions/737673/how-to-read-the-mode-field-of-git-ls-trees-output
GIT_MODES: Final[_GIT_MODES] = _GIT_MODES()
