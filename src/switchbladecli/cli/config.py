import os
from pathlib import Path

import click
from tomlkit import loads

CONFIG_FILE_NAMES = [".switchblade", "switchblade.toml"]

def find_config_file(verbose: bool, config_file: str) -> str:
    # If no config file is specified, locate it automatically
    if config_file is None:
        for name in CONFIG_FILE_NAMES:
            if os.path.exists(name):
                config_file = name
                break

    if not os.path.exists(config_file):
        raise click.ClickException(f"Configuration file not found: {config_file}")

    return config_file


def get_switchblade_config(verbose, project_dir: str, config_file: str):
    config_file = os.path.join(project_dir, config_file)
    if verbose:
        click.echo(f"Loading configuration from {config_file}")

    config = loads(Path(config_file).read_text(encoding="utf-8"))

    config["project_dir"] = project_dir
    config["config_file"] = config_file

    return config
