""" Uploads a file to a Girder instance with some metadata """

# imports
import os
from tqdm import tqdm
import girder_client
from openmsitoolbox import Runnable, LogOwner
from ..utilities.argument_parsing import IMQCAMArgumentParser
from ..utilities.girder import get_girder_folder_id, get_girder_item_id


class IMQCAMFileUploader(Runnable, LogOwner):

    ARGUMENT_PARSER_TYPE = IMQCAMArgumentParser

    def __init__(self, api_url, api_key, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_url = api_url
        # create the girder client and authenticate to the instance
        try:
            self._girder_client = girder_client.GirderClient(apiUrl=self.api_url)
            self._girder_client.authenticate(apiKey=api_key)
        except Exception as exc:
            self.logger.error(
                f"ERROR: failed to authenticate to Girder at {api_url}!",
                exc_info=exc,
                reraise=True,
            )

    def upload_file(
        self,
        filepath,
        metadata=None,
        relative_to=None,
        root_folder_id=None,
        collection_name=None,
        root_folder_path=None,
    ):
        # Log a warning if a root folder ID was given alongside
        # a collection name/root folder path
        if root_folder_id is not None and (
            collection_name is not None or root_folder_path is not None
        ):
            warnmsg = (
                "WARNING: A root folder ID was given, so the collection name/root "
                "folder path arguments are being superseded!"
            )
            self.logger.warning(warnmsg)
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
                return
        except ValueError:
            pass
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
        self.logger.info(f"Uploading {filepath} to {self.api_url}")
        total_bytes = os.stat(filepath).st_size
        progress_bar = tqdm(
            desc=filepath.name,
            total=total_bytes,
            ncols=100,
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
        if metadata is not None:
            self._girder_client.addMetadataToItem(new_file["itemId"], metadata)
        progress_bar.close()
        self.logger.info("Done!")

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
    IMQCAMFileUploader.run_from_command_line(args)
