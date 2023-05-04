import os
import pytest

from pathlib import Path
from tomlkit import loads

from switchbladecli.exceptions import MissingConfiguration, MissingRequiredConfigKey, InvalidConfigValue, UnrecognizedConfigKey
from switchbladecli.cli.config import find_config_file, get_switchblade_config
from switchbladecli.modes.tool_runner import get_tool_runner

@pytest.mark.parametrize('config_file_name', [".switchblade", "switchblade.toml"])
def test_finds_config_file(project_with_config_file_name):
    _project_dir, config_file_name = project_with_config_file_name
    config_file = find_config_file(False, None)
    assert os.path.basename(config_file) == config_file_name
 
    config_parsed = loads(Path(config_file).read_text(encoding="utf-8"))

    # Config file contains the correct data
    assert config_parsed["switchblade"]["mode"] == "python-poetry"


@pytest.mark.parametrize('bad_config_file', [None])
def test_fails_on_missing_config_file(project_with_bad_config):
    with pytest.raises(MissingConfiguration):
        find_config_file(False, None)


@pytest.mark.parametrize('bad_config_file', ["missing_field.switchblade"])
def test_fails_on_missing_required_field(project_with_bad_config):
    with pytest.raises(MissingRequiredConfigKey):
        config_file = find_config_file(False, None)
        get_switchblade_config(False, str(project_with_bad_config), config_file)


@pytest.mark.parametrize('bad_config_file', ["invalid_value.switchblade"])
def test_fails_on_invalid_value(project_with_bad_config):
    with pytest.raises(InvalidConfigValue):
        config_file = find_config_file(False, None)
        config = get_switchblade_config(False, str(project_with_bad_config), config_file)
        get_tool_runner(config)

