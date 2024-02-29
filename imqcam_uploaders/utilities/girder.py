" Some utility functions for interacting with Girder "

# imports
import pathlib

def get_girder_folder_id(
    client,
    folder_rel_path,
    root_folder_id=None,
    collection_name=None,
    create_if_not_found=False,
    create_as_public=True,
):
    if (root_folder_id is not None and collection_name is not None) or (
        root_folder_id is None and collection_name is None
    ):
        raise ValueError(
            "Must specify exactly one of root_folder_id or collection_name"
        )
    if isinstance(folder_rel_path, str):
        folder_rel_path = pathlib.Path(folder_rel_path)
    if root_folder_id is not None:
        current_folder_id = root_folder_id
        init_pftype = "folder"
    else:
        collection_id = None
        for resp in client.listCollection():
            if resp["_modelType"] == "collection" and resp["name"] == collection_name:
                collection_id = resp["_id"]
        if collection_id is None:
            raise ValueError(
                f"Failed to find a Girder Collection called {collection_name}!"
            )
        current_folder_id = collection_id
        init_pftype = "collection"
    for idepth, folder_name in enumerate(folder_rel_path.parts):
        pftype = init_pftype if idepth == 0 else "folder"
        found = False
        for resp in client.listFolder(
            current_folder_id, parentFolderType=pftype, name=folder_name
        ):
            found = True
            current_folder_id = resp["_id"]
        if not found:
            if create_if_not_found:
                new_folder = client.createFolder(
                    current_folder_id,
                    folder_name,
                    parentType=pftype,
                    public=create_as_public,
                )
                current_folder_id = new_folder["_id"]
            else:
                errmsg = (
                    "ERROR: failed to find the Girder Folder "
                    f"{'/'.join(folder_rel_path.parts[:idepth+1])} in the "
                    f"{collection_name} Collection!"
                )
                raise ValueError(errmsg)
    return current_folder_id


def get_girder_item_id(client, file_path, root_folder_id=None, collection_name=None):
    folder_id = get_girder_folder_id(
        client,
        file_path.parent,
        root_folder_id=root_folder_id,
        collection_name=collection_name,
    )
    item_id = None
    for resp in client.listItem(folder_id, name=file_path.name):
        item_id = resp["_id"]
    if item_id is None:
        errmsg = (
            f"Failed to find an Item called {file_path.name} in "
            f"{collection_name}/{file_path.parent}"
        )
        raise ValueError(errmsg)
    return item_id


def get_girder_item_and_file_id(
    client, file_path, root_folder_id=None, collection_name=None
):
    item_id = get_girder_item_id(
        client,
        file_path,
        root_folder_id=root_folder_id,
        collection_name=collection_name,
    )
    for resp in client.listFile(item_id):
        file_id = resp["_id"]
    return item_id, file_id
