" Testing the Girder utilities "

# pylint: disable=redefined-outer-name

# imports
import pathlib
import pytest
from imqcam_uploaders.utilities.girder import (
    get_girder_folder_id,
    get_girder_item_id,
    get_girder_item_and_file_id,
)

# pylint: disable=unused-import
from .fixtures import (
    default_girder_client,
    default_collection_name,
    ci_testing_girder_folder_name,
    ci_testing_girder_folder_id,
)


@pytest.fixture
def static_folder_name():
    return "do_not_delete"


@pytest.fixture
def static_folder_id():
    return "65e0c16a02ad536bd833df32"


def test_get_girder_folder_id_with_collection_name(
    default_girder_client,
    default_collection_name,
    ci_testing_girder_folder_name,
    static_folder_name,
    static_folder_id,
):
    test_folder_id = get_girder_folder_id(
        default_girder_client,
        pathlib.Path(ci_testing_girder_folder_name) / static_folder_name,
        collection_name=default_collection_name,
    )
    assert test_folder_id == static_folder_id


def test_get_girder_folder_id_with_root_folder_id(
    default_girder_client,
    ci_testing_girder_folder_id,
    static_folder_name,
    static_folder_id,
):
    test_folder_id = get_girder_folder_id(
        default_girder_client,
        static_folder_name,
        root_folder_id=ci_testing_girder_folder_id,
    )
    assert test_folder_id == static_folder_id


def test_get_girder_folder_id_arg_conflict(
    default_girder_client,
    default_collection_name,
    ci_testing_girder_folder_id,
    static_folder_name,
):
    with pytest.raises(ValueError):
        _ = get_girder_folder_id(
            default_girder_client,
            static_folder_name,
            root_folder_id=ci_testing_girder_folder_id,
            collection_name=default_collection_name,
        )


def test_get_girder_folder_id_missing_collection(
    default_girder_client, ci_testing_girder_folder_name, static_folder_name
):
    with pytest.raises(ValueError):
        _ = get_girder_folder_id(
            default_girder_client,
            pathlib.Path(ci_testing_girder_folder_name) / static_folder_name,
            collection_name="never_name_a_collection_this",
        )


def test_get_girder_folder_id_create_new(
    default_girder_client,
    ci_testing_girder_folder_id,
    static_folder_name,
):
    remove_folder_path = pathlib.Path(static_folder_name) / "subdir_testing_1"
    # make sure it doesn't already exist
    with pytest.raises(ValueError):
        _ = get_girder_folder_id(
            default_girder_client,
            remove_folder_path,
            root_folder_id=ci_testing_girder_folder_id,
        )
    # create two subdirs
    test_folder_id = get_girder_folder_id(
        default_girder_client,
        remove_folder_path / "subdir_testing_2",
        root_folder_id=ci_testing_girder_folder_id,
        create_if_not_found=True,
    )
    assert test_folder_id is not None
    # remove the folder if it exists
    remove_folder_id = None
    try:
        remove_folder_id = get_girder_folder_id(
            default_girder_client,
            remove_folder_path,
            root_folder_id=ci_testing_girder_folder_id,
        )
    except ValueError:
        pass
    if remove_folder_id is not None:
        _ = default_girder_client.delete(f"folder/{remove_folder_id}")


def test_get_girder_item_id(
    default_girder_client,
    ci_testing_girder_folder_id,
    static_folder_name,
):
    item_id = get_girder_item_id(
        default_girder_client,
        pathlib.Path(static_folder_name) / "do_not_delete_item",
        root_folder_id=ci_testing_girder_folder_id,
    )
    assert item_id == "65e0c88c02ad536bd833df33"


def test_get_girder_item_id_missing_item(
    default_girder_client,
    ci_testing_girder_folder_id,
    static_folder_name,
):
    with pytest.raises(ValueError):
        _ = get_girder_item_id(
            default_girder_client,
            pathlib.Path(static_folder_name) / "never_name_an_item_this",
            root_folder_id=ci_testing_girder_folder_id,
        )


def test_get_girder_item_and_file_id(
    default_girder_client,
    ci_testing_girder_folder_id,
    static_folder_name,
):
    item_id, file_id = get_girder_item_and_file_id(
        default_girder_client,
        pathlib.Path(static_folder_name) / "do_not_delete_file.txt",
        root_folder_id=ci_testing_girder_folder_id,
    )
    assert item_id == "65e0ca7e02ad536bd833df3c"
    assert file_id == "65e0ca7e02ad536bd833df3d"
