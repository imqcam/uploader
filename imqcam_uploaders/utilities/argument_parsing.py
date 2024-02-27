" A central location to specify command-line arguments for programs "

# imports
import os
from openmsitoolbox import OpenMSIArgumentParser
from openmsitoolbox.argument_parsing.parser_callbacks import existing_file, existing_dir


class IMQCAMArgumentParser(OpenMSIArgumentParser):
    """An OpenMSI-style ArgumentParser for IMQCAM uploader programs"""

    ARGUMENTS = {
        **OpenMSIArgumentParser.ARGUMENTS,
        "filepath": [
            "positional",
            {
                "type": existing_file,
                "help": "Path to the file to upload",
            },
        ],
        "relative_to": [
            "optional",
            {
                "type": existing_dir,
                "help": (
                    "Upload the file relative to this directory: Create extra folders "
                    "in Girder as necessary to replicate the rest of the filepath "
                    "beyond this location. If this argument isn't given, the file will "
                    "be uploaded directly to the root folder."
                ),
            },
        ],
        "api_url": [
            "optional",
            {
                "default": "https://data.imqcam.org/api/v1",
                "help": "The full URL of the REST API for the Girder instance",
            },
        ],
        "api_key": [
            "optional",
            {
                "default": os.getenv("IMQCAM_API_KEY"),
                "help": (
                    "The API key to authenticate to the Girder instance. This argument "
                    "must be given on the command line, or stored as an environment "
                    "variable called 'IMQCAM_API_KEY'"
                ),
            },
        ],
        "root_folder_id": [
            "optional",
            {
                "help": (
                    "The ID of the Girder Folder relative to which files should be "
                    "uploaded. If this argument is given, it will supersede both of the "
                    "'collection_name' and 'root_folder_path' arguments."
                ),
            },
        ],
        "collection_name": [
            "optional",
            {
                "default": "Test",
                "help": (
                    "The name of the top-level Collection to which files should be "
                    "uploaded. Superseded if 'root_folder_id' is given."
                ),
            },
        ],
        "root_folder_path": [
            "optional",
            {
                "default": "Test",
                "help": (
                    "The name of the Folder inside the top-level Collection relative to "
                    "which files should be uploaded. A path to a subdirectory in the "
                    "Collection can be given using forward slashes. "
                    "Superseded if 'root_folder_id' is given."
                ),
            },
        ],
    }
