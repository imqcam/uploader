" Make sure that all of the defined scripts exist and can be run "

# imports
import pathlib
import importlib
import pytest
import toml


def get_script_paths_from_pyproject_toml():
    pyproject_toml_path = pathlib.Path(__file__).parent.parent / "pyproject.toml"
    if not pyproject_toml_path.exists():
        raise FileNotFoundError("pyproject.toml not found")
    with open(pyproject_toml_path, "r") as fp:
        pyproject_toml_data = toml.load(fp)
    scripts = pyproject_toml_data.get("tool", {}).get("poetry", {}).get("scripts", {})
    return list(scripts.values())


@pytest.mark.parametrize("script_path", get_script_paths_from_pyproject_toml())
def test_console_scripts_exist(script_path):
    # Make sure the path to the script exists
    module_name, _, function_name = script_path.rpartition(":")
    try:
        module = importlib.import_module(module_name)
    except ImportError:
        pytest.fail(f"Failed to import module '{module_name}'")
    if not hasattr(module, function_name):
        pytest.fail(f"Function '{function_name}' not found in module '{module_name}'")
    function = getattr(module, function_name)
    assert callable(
        function
    ), f"Function '{function_name}' in module '{module_name}' is not callable"
