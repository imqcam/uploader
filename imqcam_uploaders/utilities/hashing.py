" Functions dealing with hashes of files "

# imports
from hashlib import sha256


def get_on_disk_file_hash(filepath, chunk_size=65536):
    """Return the hexdigest of the sha256 hash of a file on disk.

    Args:
        filepath (pathlib.Path): the path to the file on disk
        chunk_size (int, optional): the chunk size to use in incrementally reading
            the file from disk

    Returns:
        str: The hexdigest of the sha256 hash of the file at "filepath"
    """
    file_hash = sha256()
    with open(filepath, "rb") as fobj:
        while True:
            data = fobj.read(chunk_size)
            if not data:
                break
            file_hash.update(data)
    return file_hash.hexdigest()


def get_girder_file_hash(client, file_id, pbar=None):
    """Return the hexdigest of the sha256 hash of a file on Girder, streaming the file
    contents from the server (i.e., not just checking the metadata item with the hash).

    Args:
        client (girder_client.GirderClient): the authenticated client to use in
            connecting to Girder
        file_id (str): ID of the file to get the hash of
        pbar (tqdm.tqdm, optional): if not None, this progress bar will be updated with
            each chunk read iteratively from the server
    """
    file_hash = sha256()
    for chunk in client.downloadFileAsIterator(file_id):
        file_hash.update(chunk)
        if pbar is not None:
            pbar.update(len(chunk))
    return file_hash.hexdigest()
