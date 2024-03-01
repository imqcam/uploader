" Make sure that all of the defined scripts exist and can be run "

# imports
import pathlib
import subprocess
import pytest
import toml


def get_script_names_from_pyproject_toml():
    pyproject_toml_path = pathlib.Path(__file__).parent.parent / "pyproject.toml"
    if not pyproject_toml_path.exists():
        raise FileNotFoundError("pyproject.toml not found")
    with open(pyproject_toml_path, "r") as fp:
        pyproject_toml_data = toml.load(fp)
    scripts = pyproject_toml_data.get("tool", {}).get("poetry", {}).get("scripts", {})
    return list(scripts.keys())


@pytest.mark.parametrize("script_name", get_script_names_from_pyproject_toml())
def test_console_scripts_exist(script_name):
    # Try running the script with -h option to check if it's installed correctly
    try:
        subprocess.run([f"{script_name}", "-h"], check=True)
    except subprocess.CalledProcessError as e:
        pytest.fail(f"Failed to execute script '{script_name}': {e}")
