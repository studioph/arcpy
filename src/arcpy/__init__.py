import fnmatch
import logging
import pathlib
import tarfile
import zipfile
from abc import ABC, abstractmethod
from collections.abc import Iterable
from os import PathLike, fspath
from types import TracebackType
from typing import Generic, TypeVar

import context_utils
import py7zr
from unrar import rarfile

LOG = logging.getLogger(__name__)


T = TypeVar("T")


class ArchiveError(Exception):
    """Aggregates errors from different archive types"""


REGISTRY = {}


def register(cls, *extensions: str):
    """Registers a new subclass implementation and its associated file extensions"""
    LOG.debug(
        "Registered new Archive implementation: %s with extensions %s", cls, extensions
    )
    for ext in extensions:
        REGISTRY[ext] = cls


class Archive(Generic[T], ABC):
    _archive: type[T]

    def __init_subclass__(cls, /, extensions: Iterable[str]) -> None:
        register(cls, *extensions)

    def __init__(self, filepath: PathLike) -> None:
        self.parts = [pathlib.Path(filepath)]
        self.name = get_archive_name(self.parts[0])
        self.multipart = "part" in self.parts[0].name
        if self.multipart:
            self._get_parts()

    def __str__(self) -> str:
        return f"{self.__class__.__qualname__}('{self.parts[0].parent / self.name}')"

    def __enter__(self):
        self._archive.__enter__()
        return self

    def __exit__(
        self,
        __exc_type: type[BaseException] | None,
        __exc_value: BaseException | None,
        __traceback: TracebackType | None,
    ) -> bool | None:
        self._archive.__exit__(__exc_type, __exc_value, __traceback)

    @property
    @abstractmethod
    def items(self) -> Iterable[PathLike]: ...

    @abstractmethod
    def extract_items(self, items: Iterable[PathLike], dest: PathLike): ...

    def extract(self, item: PathLike, dest: PathLike):
        self.extract_items(items=[item], dest=dest)

    def move(self, target: pathlib.Path):
        if not target.is_dir():
            raise ValueError("Target must be a folder")
        self.parts = [part.rename(target / part.name) for part in self.parts]

    def _get_parts(self):
        folder = self.parts[0].parent
        self.parts = list(folder.glob(f"{self.name}*{self.parts[0].suffix}"))
        LOG.debug("%s is multipart archive with parts %s", self, self.parts)


class ZipArchive(Archive[zipfile.ZipFile], extensions=(".zip",)):

    def __init__(self, filepath: PathLike) -> None:
        with context_utils.rethrow(zipfile.BadZipFile, as_=ArchiveError):
            super().__init__(filepath)
            self._archive = zipfile.ZipFile(file=filepath)

    @property
    def items(self) -> Iterable[PathLike]:
        return self._archive.namelist()

    def extract_items(self, items: Iterable[PathLike], dest: PathLike):
        with context_utils.rethrow(RuntimeError, as_=ArchiveError):
            return self._archive.extractall(members=items, path=dest)


class TarArchive(
    Archive[tarfile.TarFile],
    extensions=(
        ".tar",
        ".tar.gz",
        ".tgz",
        ".tar.bz2",
        ".tbz2",
        ".tar.bz",
        ".tbz",
        ".tar.xz",
        ".txz",
    ),
):

    def __init__(self, filepath: PathLike) -> None:
        with context_utils.rethrow(
            tarfile.ReadError, tarfile.CompressionError, as_=ArchiveError
        ):
            super().__init__(filepath)
            self._archive = tarfile.open(filepath)

    @property
    def items(self) -> Iterable[PathLike]:
        return self._archive.getnames()

    def extract_items(self, items: Iterable[PathLike], dest: PathLike):
        with context_utils.rethrow(KeyError, as_=ArchiveError):
            tarinfos = [self._archive.getmember(item) for item in items]
            return self._archive.extractall(members=tarinfos, path=dest)


class RarArchive(Archive[rarfile.RarFile], extensions=(".rar",)):

    def __init__(self, filepath: PathLike) -> None:
        with context_utils.rethrow(rarfile.BadRarFile, as_=ArchiveError):
            super().__init__(filepath)
            self._archive = rarfile.RarFile(filename=fspath(filepath))

    @property
    def items(self) -> Iterable[PathLike]:
        return self._archive.namelist()

    def extract_items(self, items: Iterable[PathLike], dest: PathLike):
        with context_utils.rethrow(RuntimeError, as_=ArchiveError):
            return self._archive.extractall(members=items, path=fspath(dest))


class SevenZipArchive(Archive[py7zr.SevenZipFile], extensions=(".7z")): ...


def open(filepath: PathLike) -> Archive:  # pylint: disable=redefined-builtin
    path = pathlib.Path(filepath)
    LOG.debug("Attempting to create archive object from %r", path.name)
    for i in range(len(path.suffixes)):
        suffix = "".join(path.suffixes[i:])
        if registry_entry := REGISTRY.get(suffix):
            return registry_entry(path)

    raise ArchiveError(f"No archive type found in registry for {path.name}")


def get_archive_name(file: pathlib.Path):
    # Keep chopping off suffix until "part" is no longer included
    tmp_path = pathlib.PurePath(file.stem)
    while fnmatch.filter(tmp_path.suffixes, pat=".part*"):
        tmp_path = pathlib.PurePath(tmp_path.stem)
    return tmp_path.name
