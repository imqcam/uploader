" Functions dealing with hashes of files "

# imports
from hashlib import sha256


def get_file_hash(filepath, chunk_size=65536):
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
