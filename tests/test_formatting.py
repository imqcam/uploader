" Make sure that the package and test code are all Black formatted "

# pylint: disable=redefined-outer-name

# imports
import pathlib
import subprocess
import pytest


@pytest.fixture
def local_package_dir():
    return pathlib.Path(__file__).parent.parent / "imqcam_uploaders"


@pytest.fixture
def local_tests_dir():
    return pathlib.Path(__file__).parent


def test_package_formatting(local_package_dir):
    package_check = subprocess.run(
        ["black", "--check", str(local_package_dir)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if package_check.returncode != 0:
        errmsg = (
            "Package code is not fully formatted. Output:\n"
            f"{package_check.stdout.decode()}{package_check.stderr.decode()}"
        )
        raise RuntimeError(errmsg)


def test_tests_formatting(local_tests_dir):
    tests_check = subprocess.run(
        ["black", "--check", str(local_tests_dir)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if tests_check.returncode != 0:
        errmsg = (
            "Test code is not fully formatted. Output:\n"
            f"{tests_check.stdout.decode()}{tests_check.stderr.decode()}"
        )
        raise RuntimeError(errmsg)
