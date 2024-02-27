# IMQCAM uploader
Code for the IMQCAM Girder instance (data.imqcam.org) file/data uploader

## Installation

This package is managed using [poetry](https://python-poetry.org/), which you should install globally on your system. When you have that tool installed, though, you can then install this package and its dependencies in any environment of your choice.

### Install poetry with pipx

The easiest way to install poetry is using pipx. You can find the installation instructions for pipx [here](https://pipx.pypa.io/stable/installation/). You'll probably need to restart your shell/terminal window after installing it.

With pipx installed, you can then install poetry with:

    pipx install poetry

You'll want to make sure you're installing poetry on your bare system, so deactivate any conda environments, etc. before running the command above.

### Install the package and its dependencies

The example below assumes you use conda to manage environments, but you can use pyenv or really any other virtual environment manager.

Create and activate a new conda environment:

    conda create -n imqcam-uploaders python -y
    conda activate imqcam-uploaders

Navigate to this repository's directory, and install the `imqcam_uploader` package with its dependencies:

    cd uploader
    poetry install

You can pick up the optional dependencies needed for running CI tests with:

    poetry install --with test
