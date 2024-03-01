""" Uploads a file to a Girder instance with some metadata """

# imports
import os
import importlib.metadata
from tqdm import tqdm
import girder_client
from openmsitoolbox import Runnable, LogOwner
from ..utilities.argument_parsing import IMQCAMArgumentParser
from ..utilities.hashing import get_on_disk_file_hash, get_girder_file_hash
from ..utilities.girder import get_girder_folder_id, get_girder_item_id


class IMQCAMFileUploader(Runnable, LogOwner):
    """Runnable that uploads a single file to a Girder instance.

    Args:
        api_url (str): the URL of the Girder instance to connect to
        api_key (str): the API key to use for connecting to Girder
        args (list): passed to super().__init__()
        kwargs (dict): passed to super().__init__()

    Raises:
        Exception: If authentication to the Girder instance fails
    """

    ARGUMENT_PARSER_TYPE = IMQCAMArgumentParser
    HASH_CHUNK_SIZE = 65536

    def __init__(self, api_url, api_key, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_url = api_url
        # create the girder client and authenticate to the instance
        try:
            self._girder_client = girder_client.GirderClient(apiUrl=self.api_url)
            self._girder_client.authenticate(apiKey=api_key)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            self.logger.error(
                f"ERROR: failed to authenticate to Girder at {api_url}!",
                exc_info=exc,
                reraise=True,
            )
        self._uploader_version = importlib.metadata.version("imqcam_uploaders")

    def upload_file(
        self,
        filepath,
        metadata=None,
        relative_to=None,
        root_folder_id=None,
        collection_name=None,
        root_folder_path=None,
    ):
        """Upload a file on disk to the Girder instance, with optional metadata.

        If the file already exists in Girder with the same size as on disk, it is
        not edited at all.

        Args:
            filepath (pathlib.Path): Path to the file that should be uploaded on disk
            metadata (dict, optional): dictionary of metadata to add to the uploaded file
            relative_to (pathlib.Path, optional): An existing directory that should be
                considered the "root" directory for the upload. The directory tree beyond
                this point will be replicated in Girder, creating new Folders if needed.
            root_folder_id (str, optional): The ID of the Girder Folder that should be
                considered the "root" for the upload on the destination side. Folders
                will be created inside this Folder as needed to replicate the directory
                structure of the uploaded file relative to its root directory. If this
                parameter is given, it supersedes both "collection_name" and
                "root_folder_path".
            collection_name (str, optional): The name of the Girder Collection under
                which the file should be uploaded. Superseded by "root_folder_id" if
                that argument is given.
            root_folder_path (pathlib.Path, optional): A Path representation of the
                Girder Folder (inside the "collection_name" Collection) that should
                be considered the "root" on the upload side. Superseded by
                "root_folder_id" if that argument is given.

        Raises:
            ValueError: If "filepath" is not relative to "relative_to"
        """
        # Log a warning if a root folder ID was given alongside
        # a collection name/root folder path
        if root_folder_id is not None and (
            collection_name is not None or root_folder_path is not None
        ):
            self.logger.warning(
                (
                    "WARNING: A root folder ID was given, so the collection name/root "
                    "folder path arguments are being superseded!"
                )
            )
        # If relative_to was given, make sure it can actually be used
        rel_filepath = filepath.relative_to(filepath.parent)
        if relative_to is not None:
            try:
                rel_filepath = filepath.relative_to(relative_to)
            except ValueError as exc:
                self.logger.error(
                    f"ERROR: {filepath} is not relative to {relative_to}!",
                    exc_info=exc,
                    reraise=True,
                )
        # check if the file already exists
        if self.__file_already_exists(
            filepath, rel_filepath, root_folder_id, collection_name, root_folder_path
        ):
            return
        # Get the ID of the Girder folder to upload the file to
        # If no root folder ID was given, find it based on the collection name
        # and root folder path
        if root_folder_id is None:
            root_folder_id = get_girder_folder_id(
                self._girder_client,
                root_folder_path,
                collection_name=collection_name,
            )
        # Create directories inside the root folder to match the relative filepath
        upload_folder_id = get_girder_folder_id(
            self._girder_client,
            rel_filepath.parent,
            root_folder_id=root_folder_id,
            create_if_not_found=True,
        )
        # Upload the file
        file_hash = get_on_disk_file_hash(filepath)
        self.logger.info(f"Uploading {filepath} to {self.api_url}")
        total_bytes = os.stat(filepath).st_size
        progress_bar = tqdm(
            desc=f"uploading {filepath.name}",
            total=total_bytes,
            ncols=120,
            unit="byte",
            unit_scale=True,
            ascii=True,
        )
        new_file = self._girder_client.uploadFileToFolder(
            upload_folder_id,
            filepath,
            progressCallback=lambda x: self.__upload_callback(x, progress_bar),
        )
        progress_bar.update(new_file["size"] - progress_bar.n)
        if metadata is None:
            metadata = {}
        metadata["uploaderVersion"] = self._uploader_version
        metadata["checksum"] = {"sha256": file_hash}
        self._girder_client.addMetadataToItem(new_file["itemId"], metadata)
        progress_bar.close()
        self.logger.info("Validating upload")
        progress_bar = tqdm(
            desc=f"validating {filepath.name}",
            total=total_bytes,
            ncols=120,
            unit="byte",
            unit_scale=True,
            ascii=True,
        )
        if (
            get_girder_file_hash(
                self._girder_client, new_file["_id"], pbar=progress_bar
            )
            != file_hash
        ):
            self.logger.error(
                f"Hash for {filepath} does not match what's on Girder after upload!",
                exc_type=ValueError,
            )
        if self._girder_client.getItem(new_file["itemId"])["meta"] != metadata:
            self.logger.error(
                f"Metadata for {filepath} does not match what's on Girder after upload!",
                exc_type=ValueError,
            )
        progress_bar.update(new_file["size"] - progress_bar.n)
        progress_bar.close()
        self.logger.info("Done!")

    def __file_already_exists(
        self, filepath, rel_filepath, root_folder_id, collection_name, root_folder_path
    ):
        try:
            if root_folder_id is not None:
                item_id = get_girder_item_id(
                    self._girder_client, rel_filepath, root_folder_id=root_folder_id
                )
            else:
                item_id = get_girder_item_id(
                    self._girder_client,
                    root_folder_path / rel_filepath,
                    collection_name=collection_name,
                )
            resp = self._girder_client.isFileCurrent(item_id, filepath.name, filepath)
            if resp is not None and resp[1]:
                self.logger.info(
                    f"{filepath} already exists in Girder and will be skipped"
                )
                return True
        except ValueError:
            pass
        return False

    def __upload_callback(self, info_dict, pbar):
        pbar.update(info_dict["current"] - pbar.n)

    @classmethod
    def get_command_line_arguments(cls):
        superargs, superkwargs = super().get_command_line_arguments()
        _ = superargs.pop(superargs.index("logger_file_path"))
        _ = superargs.pop(superargs.index("logger_file_level"))
        args = [
            "filepath",
            "api_url",
            "api_key",
            "metadata_json",
            "relative_to",
            "root_folder_id",
            "collection_name",
            "root_folder_path",
            *superargs,
        ]
        kwargs = {**superkwargs, "logger_file_path": None, "logger_file_level": None}
        return args, kwargs

    @classmethod
    def get_init_args_kwargs(cls, parsed_args):
        superargs, superkwargs = super().get_init_args_kwargs(parsed_args)
        args = [
            parsed_args.api_url,
            parsed_args.api_key,
            *superargs,
        ]
        return args, superkwargs

    @classmethod
    def run_from_command_line(cls, args=None):
        # make the argument parser
        parser = cls.get_argument_parser()
        args = parser.parse_args(args=args)
        # make the uploader
        init_args, init_kwargs = cls.get_init_args_kwargs(args)
        uploader = cls(*init_args, **init_kwargs)
        # upload the given file
        uploader.upload_file(
            args.filepath,
            metadata=args.metadata_json,
            relative_to=args.relative_to,
            root_folder_id=args.root_folder_id,
            collection_name=args.collection_name,
            root_folder_path=args.root_folder_path,
        )


def main(args=None):
    """Run the "run_from_command_line" method of the IMQCAMFileUploader

    Args:
        args (list): list of command-line arguments to send to run_from_command_line
    """
    IMQCAMFileUploader.run_from_command_line(args)
