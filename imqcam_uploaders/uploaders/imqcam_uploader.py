""" Uploads a file to a Girder instance with some metadata """

# imports
import os
from tqdm import tqdm
import girder_client
from openmsitoolbox import Runnable, LogOwner
from ..utilities.argument_parsing import IMQCAMArgumentParser


class IMQCAMUploader(Runnable, LogOwner):

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
                f"ERROR: failed to authenticate to Girder at {api_url}!", exc_info=exc
            )

    def upload_file(
        self,
        filepath,
        relative_to=None,
        root_folder_id=None,
        collection_name=None,
        root_folder_path=None,
    ):
        # If relative_to was given, make sure it can actually be used
        if relative_to is not None:
            try:
                rel_filepath = filepath.relative_to(relative_to)
            except ValueError as exc:
                self.logger.error(
                    f"ERROR: {filepath} is not relative to {relative_to}!", exc_info=exc
                )
        else:
            rel_filepath = filepath.relative_to(filepath.parent)
        # Get the ID of the Girder folder to upload the file to
        upload_folder_id = self.__get_upload_folder_id(
            rel_filepath, root_folder_id, collection_name, root_folder_path
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
        progress_bar.close()
        self.logger.info("Done!")

    def __get_upload_folder_id(
        self, rel_filepath, root_folder_id, collection_name, root_folder_path
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
        # If no root folder ID was given, find it based on the collection name
        # and root folder path
        if root_folder_id is None:
            root_folder_id = self.__get_root_folder_id(
                collection_name, root_folder_path
            )
        # Create directories inside the root folder to match the relative filepath
        upload_folder_id = root_folder_id
        for new_folder_name in rel_filepath.parent.parts:
            exists = False
            # if a folder with the name already exists, just set the ID and continue
            for resp in self._girder_client.listFolder(upload_folder_id):
                if resp["_modelType"] == "folder" and resp["name"] == new_folder_name:
                    upload_folder_id = resp["_id"]
                    exists = True
                    break
            if exists:
                continue
            # otherwise, create the new folder
            infomsg = (
                f"Creating new public folder '{new_folder_name}' inside "
                f"{self._girder_client.getFolder(upload_folder_id)['name']}"
            )
            self.logger.info(infomsg)
            new_folder = self._girder_client.createFolder(
                upload_folder_id,
                new_folder_name,
                parentType="folder",
                public=True,
            )
            upload_folder_id = new_folder["_id"]
        return upload_folder_id

    def __get_root_folder_id(self, collection_name, root_folder_path):
        # get the collection ID
        collection_id = None
        for resp in self._girder_client.listCollection():
            if resp["_modelType"] == "collection" and resp["name"] == collection_name:
                collection_id = resp["_id"]
        if collection_id is None:
            errmsg = (
                f"ERROR: Could not find a Collection called {collection_name} "
                f"in {self.api_url}!"
            )
            self.logger.error(errmsg, exc_type=ValueError)
        # get the root folder ID
        folder_id = collection_id
        root_folder_split = root_folder_path.split("/")
        for idepth, folder_name in enumerate(root_folder_split):
            pftype = "collection" if idepth == 0 else "folder"
            found = False
            for resp in self._girder_client.listFolder(
                folder_id, parentFolderType=pftype
            ):
                if resp["_modelType"] == "folder" and resp["name"] == folder_name:
                    found = True
                    folder_id = resp["_id"]
                    break
            if not found:
                errmsg = (
                    f"ERROR: Could not find a matching Folder in the "
                    f"{collection_name} Collection at "
                    f"{'/'.join(root_folder_split[:idepth+1])}"
                )
                self.logger.error(errmsg, exc_type=ValueError)
        return folder_id

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
            relative_to=args.relative_to,
            root_folder_id=args.root_folder_id,
            collection_name=args.collection_name,
            root_folder_path=args.root_folder_path,
        )


def main(args=None):
    IMQCAMUploader.run_from_command_line(args)


if __name__ == "__main__":
    main()
