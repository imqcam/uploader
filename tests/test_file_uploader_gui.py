" Test the GUI for the IMQCAM FileUploader "

# pylint: disable=redefined-outer-name

# imports
import pathlib
import shutil
import importlib
import json
import tkinter as tk
from tkinter import filedialog
import pytest
from imqcam_uploaders.utilities.hashing import (
    get_on_disk_file_hash,
    get_girder_file_hash,
)
from imqcam_uploaders.utilities.girder import (
    get_girder_item_and_file_id,
    get_girder_folder_id,
)
from imqcam_uploaders.guis.file_uploader_gui import FileUploaderGUI

# pylint: disable=wrong-import-order, unused-import
from .fixtures import (
    local_tests_dir,
    default_girder_client,
    default_collection_name,
    ci_testing_girder_folder_name,
    random_100_kb,
    random_json_string,
)


def test_set_filepath(monkeypatch):
    def mock_askopenfilename():
        return "/path/to/file.txt"

    monkeypatch.setattr(filedialog, "askopenfilename", mock_askopenfilename)
    gui = FileUploaderGUI()
    gui.set_filepath()
    assert gui.filepath_entry.get() == "/path/to/file.txt"
    assert gui.relative_to_entry.get() == "/path/to"
    assert gui.run_upload_button["state"] == "normal"


def test_set_relative_to(monkeypatch):
    def mock_askdirectory():
        return "/path/to/folder"

    monkeypatch.setattr(filedialog, "askdirectory", mock_askdirectory)
    gui = FileUploaderGUI()
    gui.set_relative_to()
    assert gui.relative_to_entry.get() == "/path/to/folder"


def test_run_upload(
    monkeypatch,
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
    test_dir = local_tests_dir / test_run_upload.__name__
    test_subdir = test_dir / "subdir"
    test_filepath = test_subdir / "test_file.bin"
    girder_filepath = pathlib.Path(root_folder_name) / test_filepath.relative_to(
        test_dir.parent
    )
    with pytest.raises(ValueError):
        _, _ = get_girder_item_and_file_id(
            client, girder_filepath, collection_name=collection_name
        )

    # set up the patches for the user interaction functions
    def mock_askopenfilename():
        return str(test_filepath)

    def mock_askdirectory():
        return str(test_dir.parent)

    monkeypatch.setattr(filedialog, "askopenfilename", mock_askopenfilename)
    monkeypatch.setattr(filedialog, "askdirectory", mock_askdirectory)
    # create the test directory and file
    assert not test_dir.is_dir()
    test_subdir.mkdir(parents=True)
    try:
        with open(test_filepath, "wb") as fp:
            fp.write(random_100_kb)
        # run the file uploader from the GUI
        gui = FileUploaderGUI()
        gui.set_filepath()
        gui.arg_entries["metadata_json"].delete(0, tk.END)
        gui.arg_entries["metadata_json"].insert(0, random_json_string)
        gui.set_relative_to()
        gui.arg_entries["root_folder_path"].delete(0, tk.END)
        gui.arg_entries["root_folder_path"].insert(0, root_folder_name)
        gui.run_upload()
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
        file_hash = get_on_disk_file_hash(test_filepath)
        ref_metadata["checksum"] = {"sha256": file_hash}
        assert ref_metadata == metadata_read_back
        hash_read_back = get_girder_file_hash(client, file_id)
        assert hash_read_back == file_hash
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
