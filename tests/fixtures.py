" Fixtures used in more than one test "

# imports
import pytest
import json
from faker import Faker


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
