" Fixtures used in more than one test "

# imports
import pathlib, os
import json
import pytest
from faker import Faker
import girder_client
from imqcam_uploaders.utilities.argument_parsing import IMQCAMArgumentParser


@pytest.fixture
def local_tests_dir():
    return pathlib.Path(__file__).parent


@pytest.fixture
def random_100_kb():
    return os.urandom(100000)


@pytest.fixture
def random_json_string():
    fake = Faker()
    data = {
        "name": fake.name(),
        "address": fake.address(),
        "phone_number": fake.phone_number(),
        "email": fake.email(),
        "job": fake.job(),
        "company": fake.company(),
    }
    return json.dumps(data)


@pytest.fixture
def default_girder_client():
    def_api_url = IMQCAMArgumentParser.ARGUMENTS["api_url"][1]["default"]
    def_api_key = IMQCAMArgumentParser.ARGUMENTS["api_key"][1]["default"]
    if def_api_key is None:
        errmsg = (
            "Failed to find the default value of the Girder API key! "
            "Is the environment variable set?"
        )
        raise RuntimeError(errmsg)
    try:
        client = girder_client.GirderClient(apiUrl=def_api_url)
        client.authenticate(apiKey=def_api_key)
    except Exception as exc:
        raise RuntimeError(
            "Failed to authenticate to Girder client with default API URL/key!"
        ) from exc
    return client


@pytest.fixture
def default_collection_name():
    return IMQCAMArgumentParser.ARGUMENTS["collection_name"][1]["default"]


@pytest.fixture
def ci_testing_girder_folder_name():
    return "uploaders_ci_testing"


@pytest.fixture
def ci_testing_girder_folder_id():
    return "65dfc5f002ad536bd833df10"


@pytest.fixture
def static_file_name():
    return "do_not_delete_file.txt"


@pytest.fixture
def static_file_id():
    return "65e0ca7e02ad536bd833df3d"
