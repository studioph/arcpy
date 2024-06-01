import contextlib
import fnmatch
import pathlib
from typing import Unpack

@contextlib.contextmanager
def reraise(
    *errors: Unpack[Exception], as_: Exception = RuntimeError, **exception_args
):
    try:
        yield
    except errors as error:
        raise as_(error, **exception_args) from error
    
def get_archive_name(file: pathlib.Path):
    # Keep chopping off suffix until "part" is no longer included
    tmp_path = pathlib.PurePath(file.stem)
    while fnmatch.filter(tmp_path.suffixes, pat=".part*"):
        tmp_path = pathlib.PurePath(tmp_path.stem)
    return tmp_path.name