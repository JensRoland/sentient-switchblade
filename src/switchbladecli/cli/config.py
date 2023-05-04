import os
from pathlib import Path

import click
from tomlkit import loads

from switchbladecli.exceptions import MissingConfiguration, MissingRequiredConfigKey

CONFIG_FILE_NAMES = [".switchblade", "switchblade.toml"]
REQUIRED_CONFIG_KEYS = {
    "switchblade": ["mode", "bundle"]
}

def find_config_file(verbose: bool, config_file: str) -> str:
    # If no config file is specified, locate it automatically
    if config_file is None:
        for name in CONFIG_FILE_NAMES:
            if os.path.exists(name):
                config_file = name
                break

    if config_file is None or not os.path.exists(config_file):
        raise MissingConfiguration(f"Configuration file not found. Allowed config file names: {CONFIG_FILE_NAMES}")

    return config_file


def get_switchblade_config(verbose, project_dir: str, config_file: str):
    config_file = os.path.join(project_dir, config_file)
    if verbose:
        click.echo(f"Loading configuration from {config_file}")

    config = loads(Path(config_file).read_text(encoding="utf-8"))

    config["project_dir"] = project_dir
    config["config_file"] = config_file

    # Validate config
    if "switchblade" not in config:
        raise MissingRequiredConfigKey("Missing [switchblade] section in config file")

    for section in REQUIRED_CONFIG_KEYS:
        if section not in config:
            raise MissingRequiredConfigKey(f"Required configuration section not found: [{section}]")
        for key in REQUIRED_CONFIG_KEYS[section]:
            if key not in config[section]:
                raise MissingRequiredConfigKey(f"Required configuration key not found: [{section}].{key}")

    return config
