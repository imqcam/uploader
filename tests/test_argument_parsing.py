" Test the IMQCAM Argument Parser callbacks and behavior "

# pylint: disable=redefined-outer-name

# imports
import pathlib
import shutil
import json
import pytest
from faker import Faker
from imqcam_uploaders.utilities.argument_parsing import json_str_or_filepath

# pylint: disable=wrong-import-order, unused-import
from fixtures import random_json_string


@pytest.fixture
def random_not_json_string():
    fake = Faker()
    valid = False
    while not valid:
        text = fake.text()
        try:
            json.loads(text)
        except json.decoder.JSONDecodeError:
            valid = True
    return text


def test_json_str_or_filepath_with_str(random_json_string):
    loaded = json.loads(random_json_string)
    retval = json_str_or_filepath(random_json_string)
    assert loaded == retval


def test_json_str_or_filepath_fail_with_str(random_not_json_string):
    with pytest.raises(ValueError):
        _ = json_str_or_filepath(random_not_json_string)


def test_json_str_or_filepath_with_filepath(random_json_string):
    test_file_path = (
        pathlib.Path(__file__).parent
        / test_json_str_or_filepath_with_filepath.__name__
        / "test_file.json"
    )
    assert not test_file_path.parent.is_dir()
    test_file_path.parent.mkdir()
    try:
        with open(test_file_path, "w") as fp:
            fp.write(random_json_string)
        loaded = json.loads(random_json_string)
        retval = json_str_or_filepath(test_file_path)
        assert loaded == retval
    finally:
        shutil.rmtree(test_file_path.parent)


def test_json_str_or_filepath_fail_with_filepath(random_not_json_string):
    test_file_path = (
        pathlib.Path(__file__).parent
        / test_json_str_or_filepath_with_filepath.__name__
        / "test_file.json"
    )
    assert not test_file_path.parent.is_dir()
    test_file_path.parent.mkdir()
    try:
        with open(test_file_path, "w") as fp:
            fp.write(random_not_json_string)
        with pytest.raises(ValueError):
            _ = json_str_or_filepath(test_file_path)
    finally:
        shutil.rmtree(test_file_path.parent)
