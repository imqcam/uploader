" Test the single-file uploader "

# pylint: disable=redefined-outer-name

# imports
import os
import pathlib
import json
import requests
import shutil
import importlib.metadata
import pytest
from imqcam_uploaders.utilities.hashing import get_file_hash
from imqcam_uploaders.utilities.girder import (
    get_girder_folder_id,
    get_girder_item_and_file_id,
)
from imqcam_uploaders.uploaders.file_uploader import IMQCAMFileUploader, main

# pylint: disable=wrong-import-order, unused-import
from .fixtures import (
    local_tests_dir,
    default_girder_client,
    default_collection_name,
    ci_testing_girder_folder_name,
    ci_testing_girder_folder_id,
    random_json_string,
)


@pytest.fixture
def random_100_kb():
    return os.urandom(100000)


def test_file_uploader(
    local_tests_dir,
    default_girder_client,
    default_collection_name,
    ci_testing_girder_folder_name,
    random_100_kb,
    random_json_string,
):
    # make sure the test file hasn't already been uploaded
    client = default_girder_client
    collection_name = default_collection_name
    root_folder_name = ci_testing_girder_folder_name
    test_dir = local_tests_dir / test_file_uploader.__name__
    test_subdir = test_dir / "subdir"
    test_filepath = test_subdir / "test_file.bin"
    girder_filepath = pathlib.Path(root_folder_name) / test_filepath.relative_to(
        test_dir.parent
    )
    with pytest.raises(ValueError):
        _, _ = get_girder_item_and_file_id(
            client, girder_filepath, collection_name=collection_name
        )
    # create the test directory and file
    assert not test_dir.is_dir()
    test_subdir.mkdir(parents=True)
    try:
        with open(test_filepath, "wb") as fp:
            fp.write(random_100_kb)
        # run the file uploader
        args = [
            str(test_filepath),
            "--metadata_json",
            random_json_string,
            "--relative_to",
            str(test_dir.parent),
            "--root_folder_path",
            root_folder_name,
        ]
        IMQCAMFileUploader.run_from_command_line(args)
        # run again and let the program return no problem
        IMQCAMFileUploader.run_from_command_line(args)
        # make sure the item and file exist
        item_id, file_id = get_girder_item_and_file_id(
            client,
            girder_filepath,
            collection_name=collection_name,
        )
        # make sure the file contents and metadata match
        metadata_read_back = client.getItem(item_id)["meta"]
        ref_metadata = json.loads(random_json_string)
        ref_metadata["uploaderVersion"] = importlib.metadata.version("imqcam_uploaders")
        ref_metadata["checksum"] = {"sha256": get_file_hash(test_filepath)}
        assert ref_metadata == metadata_read_back
        filepath_read_back = test_dir / "test_file_read_back.bin"
        client.downloadFile(file_id, str(filepath_read_back))
        with open(test_filepath, "rb") as ref_fp:
            ref_bytestring = ref_fp.read()
        with open(filepath_read_back, "rb") as test_fp:
            test_bytestring = test_fp.read()
        assert test_bytestring == ref_bytestring
    finally:
        # delete the testing folder in Girder
        girder_test_folder_id = None
        try:
            girder_test_folder_id = get_girder_folder_id(
                client,
                pathlib.Path(root_folder_name) / test_dir.name,
                collection_name=collection_name,
            )
        except ValueError:
            pass
        if girder_test_folder_id is not None:
            _ = client.delete(f"folder/{girder_test_folder_id}")
        # delete the local testing folder
        shutil.rmtree(test_dir)


def test_file_uploader_bad_credentials():
    with pytest.raises(requests.exceptions.ConnectionError):
        _ = IMQCAMFileUploader(
            "https://this_is_not_a_girder_instance",
            "this_is_not_an_api_key",
        )


def test_file_uploader_root_folder_id(
    local_tests_dir,
    default_girder_client,
    ci_testing_girder_folder_id,
    random_100_kb,
):
    # make sure the test file hasn't already been uploaded
    client = default_girder_client
    test_dir = local_tests_dir / test_file_uploader_root_folder_id.__name__
    test_filepath = test_dir / "test_file_2.bin"
    girder_filepath = test_filepath.relative_to(test_dir.parent)
    with pytest.raises(ValueError):
        _, _ = get_girder_item_and_file_id(
            client,
            girder_filepath,
            root_folder_id=ci_testing_girder_folder_id,
        )
    # create the test directory and file
    assert not test_dir.is_dir()
    test_filepath.parent.mkdir()
    try:
        with open(test_filepath, "wb") as fp:
            # write a bigger file to test the progress bar
            for _ in range(1000):
                fp.write(random_100_kb)
        # run the file uploader
        args = [
            str(test_filepath),
            "--relative_to",
            str(test_dir.parent),
            "--root_folder_id",
            ci_testing_girder_folder_id,
            "--root_folder_path",
            "unused",
        ]
        # run it from the "main" function instead
        main(args)
        # make sure the item and file exist
        item_id, file_id = get_girder_item_and_file_id(
            client,
            girder_filepath,
            root_folder_id=ci_testing_girder_folder_id,
        )
        # make sure the file contents and metadata match
        metadata_read_back = client.getItem(item_id)["meta"]
        ref_metadata = {}
        ref_metadata["uploaderVersion"] = importlib.metadata.version("imqcam_uploaders")
        ref_metadata["checksum"] = {"sha256": get_file_hash(test_filepath)}
        assert ref_metadata == metadata_read_back
        filepath_read_back = test_dir / "test_file_read_back.bin"
        client.downloadFile(file_id, str(filepath_read_back))
        with open(test_filepath, "rb") as ref_fp:
            ref_bytestring = ref_fp.read()
        with open(filepath_read_back, "rb") as test_fp:
            test_bytestring = test_fp.read()
        assert test_bytestring == ref_bytestring
    finally:
        # delete the testing folder in Girder
        girder_test_folder_id = None
        try:
            girder_test_folder_id = get_girder_folder_id(
                client,
                test_dir.name,
                root_folder_id=ci_testing_girder_folder_id,
            )
        except ValueError:
            pass
        if girder_test_folder_id is not None:
            _ = client.delete(f"folder/{girder_test_folder_id}")
        # delete the local testing folder
        shutil.rmtree(test_dir)


def test_file_uploader_bad_relative_to(
    local_tests_dir,
    default_girder_client,
    ci_testing_girder_folder_id,
    random_100_kb,
    random_json_string,
):
    client = default_girder_client
    test_dir = local_tests_dir / test_file_uploader_bad_relative_to.__name__
    test_filepath = test_dir / "test_file_3.bin"
    relative_to_dir = test_dir / "not_relative_to_this"
    # create the test directory and file
    assert not test_dir.is_dir()
    test_filepath.parent.mkdir()
    assert not relative_to_dir.is_dir()
    relative_to_dir.mkdir()
    try:
        with open(test_filepath, "wb") as fp:
            fp.write(random_100_kb)
        # make sure running the file uploader fails
        args = [
            str(test_filepath),
            "--metadata_json",
            random_json_string,
            "--relative_to",
            str(relative_to_dir),
            "--root_folder_id",
            ci_testing_girder_folder_id,
        ]
        with pytest.raises(ValueError):
            IMQCAMFileUploader.run_from_command_line(args)
    finally:
        # delete the testing folder in Girder
        girder_test_folder_id = None
        try:
            girder_test_folder_id = get_girder_folder_id(
                client,
                test_dir.name,
                root_folder_id=ci_testing_girder_folder_id,
            )
        except ValueError:
            pass
        if girder_test_folder_id is not None:
            _ = client.delete(f"folder/{girder_test_folder_id}")
        # delete the local testing folder
        shutil.rmtree(test_dir)
