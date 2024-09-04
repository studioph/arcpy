from os import PathLike, fspath
from pathlib import Path

import pytest

import arcpy as archive

TEST_DATA_FOLDER = Path(__file__).parent / "data"


@pytest.mark.parametrize(
    ("file", "expected"),
    [
        (Path("/foo/bar/baz.zip"), "baz"),
        (Path("foo.part1.rar"), "foo"),
        (Path("foo.bar.part01.tar.gz"), "foo.bar"),
    ],
)
def test_get_archive_name(file: Path, expected: str):
    assert archive.get_archive_name(file) == expected


def test_rar(tmp_path: Path):
    with archive.RarArchive(TEST_DATA_FOLDER / "test.rar") as rar:
        rar.extract("test", dest=tmp_path)
    assert tmp_path.joinpath("test").exists()


def test_encrypted_rar_throws(tmp_path: Path):
    with (
        pytest.raises(archive.ArchiveError),
        archive.RarArchive(TEST_DATA_FOLDER / "test-pwd.rar") as rar,
    ):
        rar.extract("test", dest=tmp_path)


def test_zip(tmp_path: Path):
    with archive.ZipArchive(TEST_DATA_FOLDER / "test.zip") as z:
        z.extract("test", dest=tmp_path)
    assert tmp_path.joinpath("test").exists()


def test_encrypted_zip_throws(tmp_path: Path):
    with (
        pytest.raises(archive.ArchiveError),
        archive.ZipArchive(TEST_DATA_FOLDER / "test-pwd.zip") as z,
    ):
        z.extract("test", dest=tmp_path)


def test_tar(tmp_path: Path):
    with archive.TarArchive(TEST_DATA_FOLDER / "test.tar.gz") as tar:
        tar.extract("test", dest=tmp_path)
    assert tmp_path.joinpath("test").exists()


def test_tar_throws(tmp_path: Path):
    with (
        pytest.raises(archive.ArchiveError),
        archive.TarArchive(TEST_DATA_FOLDER / "test.tar.gz") as tar,
    ):
        tar.extract("foo", dest=tmp_path)


@pytest.mark.parametrize(
    ("file",),
    [
        (TEST_DATA_FOLDER / "test.zip",),
        (TEST_DATA_FOLDER / "test.rar",),
        (fspath(TEST_DATA_FOLDER / "test.tar.gz"),),
        (TEST_DATA_FOLDER / "test.copy.tar.gz",),
    ],
)
def test_open(file: PathLike):
    archive.open(file)


@pytest.mark.parametrize(
    ["file", "parts"],
    [
        (
            TEST_DATA_FOLDER / "multipart.part01.rar",
            [
                TEST_DATA_FOLDER / "multipart.part01.rar",
                TEST_DATA_FOLDER / "multipart.part02.rar",
            ],
        ),
        (
            TEST_DATA_FOLDER / "multipart.part1.zip",
            [
                TEST_DATA_FOLDER / "multipart.part1.zip",
                TEST_DATA_FOLDER / "multipart.part2.zip",
            ],
        ),
    ],
)
def test_multipart(file: PathLike, parts: list[Path]):
    arcfile = archive.open(file)
    assert arcfile.parts == parts


def test_unknown_type():
    file = TEST_DATA_FOLDER / "bad.zip.foo"
    with pytest.raises(archive.ArchiveError):
        archive.open(file)
