" Test the single-file uploader "

# pylint: disable=redefined-outer-name

# imports
import os
import pathlib
import json
import shutil
import pytest
import girder_client
from imqcam_uploaders.utilities.argument_parsing import IMQCAMArgumentParser
from imqcam_uploaders.uploaders.file_uploader import IMQCAMFileUploader

# pylint: disable=wrong-import-order, unused-import
from fixtures import random_json_string


@pytest.fixture
def random_100_kb():
    return os.urandom(100000)


def get_girder_folder_id(client, collection_name, folder_path):
    if isinstance(folder_path, str):
        folder_path = pathlib.Path(folder_path)
    collection_id = None
    for resp in client.listCollection():
        if resp["_modelType"] == "collection" and resp["name"] == collection_name:
            collection_id = resp["_id"]
    if collection_id is None:
        raise ValueError(
            f"Failed to find a Girder Collection called {collection_name}!"
        )
    current_folder_id = collection_id
    for idepth, folder_name in enumerate(folder_path.parts):
        pftype = "collection" if idepth == 0 else "folder"
        found = False
        for resp in client.listFolder(
            current_folder_id, parentFolderType=pftype, name=folder_name
        ):
            found = True
            current_folder_id = resp["_id"]
        if not found:
            errmsg = (
                "ERROR: failed to find the Girder Folder "
                f"{'/'.join(folder_path.parts[:idepth+1])} in the "
                f"{collection_name} Collection!"
            )
            raise ValueError(errmsg)
    return current_folder_id


def get_girder_item_and_file_id(client, collection_name, file_path):
    folder_id = get_girder_folder_id(client, collection_name, file_path.parent)
    item_id = None
    for resp in client.listItem(folder_id, name=file_path.name):
        item_id = resp["_id"]
    if item_id is None:
        errmsg = (
            f"Failed to find an Item called {file_path.name} in "
            f"{collection_name}/{file_path.parent}"
        )
        raise ValueError(errmsg)
    file_id = None
    for resp in client.listFile(item_id):
        file_id = resp["_id"]
    if file_id is None:
        errmsg = (
            f"Failed to find an File called {file_path.name} in the Item at "
            f"{collection_name}/{file_path}"
        )
        raise ValueError(errmsg)
    return item_id, file_id


def test_file_uploader(random_100_kb, random_json_string):
    # first make sure we can authenticate to Girder
    def_api_url = IMQCAMArgumentParser.ARGUMENTS["api_url"][1]["default"]
    def_api_key = IMQCAMArgumentParser.ARGUMENTS["api_key"][1]["default"]
    if def_api_key is None:
        errmsg = (
            "Failed to find the default value of the Girder API key! "
            "Is the environment variable set?"
        )
        raise RuntimeError(errmsg)
    try:
        client = girder_client.GirderClient(apiUrl=def_api_url)
        client.authenticate(apiKey=def_api_key)
    except Exception as exc:
        raise RuntimeError(
            "Failed to authenticate to Girder client with default API URL/key!"
        ) from exc
    # make sure the test file hasn't already been uploaded
    collection_name = IMQCAMArgumentParser.ARGUMENTS["collection_name"][1]["default"]
    root_folder_name = "uploaders_ci_testing"
    test_dir = pathlib.Path(__file__).parent / test_file_uploader.__name__
    test_subdir = test_dir / "subdir"
    test_filepath = test_subdir / "test_file.bin"
    girder_filepath = pathlib.Path(root_folder_name) / test_filepath.relative_to(
        test_dir.parent
    )
    with pytest.raises(ValueError):
        _, _ = get_girder_item_and_file_id(client, collection_name, girder_filepath)
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
        # make sure the item and file exist
        item_id, file_id = get_girder_item_and_file_id(
            client, collection_name, girder_filepath
        )
        # make sure the file contents and metadata match
        metadata_read_back = client.getItem(item_id)["meta"]
        assert json.loads(random_json_string) == metadata_read_back
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
                client, collection_name, pathlib.Path(root_folder_name) / test_dir.name
            )
        except ValueError:
            pass
        if girder_test_folder_id is not None:
            _ = client.delete(f"folder/{girder_test_folder_id}")
        # delete the local testing folder
        shutil.rmtree(test_dir)
