# IMQCAM uploader
Code for the IMQCAM Girder instance (data.imqcam.org) file/data uploader

[![CI tests](https://github.com/imqcam/uploader/actions/workflows/ci_tests.yaml/badge.svg)](https://github.com/imqcam/uploader/actions/workflows/ci_tests.yaml)

## Installation

This package is managed using [poetry](https://python-poetry.org/), which you should install globally on your system. When you have that tool installed, though, you can then install this package and its dependencies in any environment of your choice.

### Install poetry with pipx

The easiest way to install poetry is using pipx. You can find the installation instructions for pipx [here](https://pipx.pypa.io/stable/installation/). You'll probably need to restart your shell/terminal window after installing it.

With pipx installed, you can then install poetry with:

    pipx install poetry

You'll want to make sure you're installing poetry on your bare system, so deactivate any conda environments, etc. before running the command above.

### Install the package and its dependencies

The example below assumes you use conda to manage environments, but you can use pyenv or really any other virtual environment manager. In fact, if you skip the "create and activate" step below, Poetry will automatically create a virtual environment associated with the project for you when you run `poetry install` below.

Create and activate a new conda environment:

    conda create -n imqcam-uploaders python -y
    conda activate imqcam-uploaders

Navigate to this repository's directory, and install the `imqcam_uploader` package with its dependencies:

    cd uploader
    poetry install

## Running programs

After installing this package, you can run the single-file uploader using a command line tool or by importing it in a Python script.

### From the command line

To upload a single file using the command line utility, run:

    upload_file [filepath] --relative_to [relative_to] --collection_name [collection_name] --root_folder_path [root_folder_path] --metadata_json [metadata_json]

Where:

- `[filepath]` is the path to the file to upload
- `[relative_to]` is the path to the directory that the file should be uploaded "relative to," as in, any directories beyond `[relative_to]` on the way to `[filepath]` will be replicated in Girder (they'll be created as public Folders if they don't already exist)
- `[collection_name]` is the name of the Girder Collection to which the file should be uploaded
- `[root_folder_path]` name of the Girder Folder inside `[collection_name]` that the file should be uploaded to. If `[relative_to]` was given, directories past that one will be created as public Girder Folders inside this Girder "root folder". You can give a path to specify any sub-Folder inside the Collection.
- `[metadata_json]` is a JSON-formatted string, or the path to a valid JSON file on disk, specifying the JSON metadata that should be associated with the uploaded file in Girder. The version of the uploader code that's running and a checksum hash will be added as metadata in addition to any parameters specified here.

To see the full list of options for running the program, add the `-h` flag to the command.

### In a Python script

To use the existing uploader in a Python script to upload individual files on disk, you can do something like this:

```python
# import the uploader
from imqcam_uploaders.uploaders.file_uploader import IMQCAMFileUploader

# create the uploader object (you'll need the API URL and Key that you can get from Maggie)
uploader = IMQCAMFileUploader(GIRDER_API_URL, GIRDER_API_KEY)

# upload a single file with some json-formatted metadata
# (you can run this in a loop to do many files, or
# traverse a directory tree on your system)
uploader.upload_file(
    path_to_file_on_disk,
    json_formatted_metadata_str,
    relative_to=optional_path_to_root_directory_on_disk,
    collection_name=collection_name,
    root_folder_path=girder_folder_name,
)
```

Please reach out to Maggie on the IMQCAM Slack for more details and help with your particular use case. See above about the command line use case for more explanation of the parameters referenced in the example.

## Running tests

You can pick up the optional dependencies needed for running CI tests with:

    poetry install --with test

And you can run all of the CI tests for the package with:

    poetry run pytest
