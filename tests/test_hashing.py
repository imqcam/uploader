" Tests for the hashing utilities "

# pylint: disable=redefined-outer-name

# imports
import shutil
from imqcam_uploaders.utilities.hashing import (
    get_on_disk_file_hash,
    get_girder_file_hash,
)

# pylint: disable=unused-import
from .fixtures import local_tests_dir, default_girder_client, static_file_id


def test_on_disk_file_hash(local_tests_dir):
    test_dir_path = local_tests_dir / test_on_disk_file_hash.__name__
    assert not test_dir_path.is_dir()
    test_dir_path.mkdir()
    try:
        test_file_path = test_dir_path / "test_hash_file.txt"
        with open(test_file_path, "w") as fobj:
            fobj.write("This is a testing file")
        test_hash = get_on_disk_file_hash(test_file_path)
        assert (
            test_hash
            == "411ebae6a2dc48d4125ba95a978fd27f030bcef8ae040685fa4e3806b8c4d3a9"
        )
    finally:
        shutil.rmtree(test_dir_path)


def test_girder_file_hash(default_girder_client, static_file_id):
    test_hash = get_girder_file_hash(default_girder_client, static_file_id)
    assert (
        test_hash == "30646dccdc85342957704a7902fb0946dd5451420feb92b76e347c721fc9d2d6"
    )
