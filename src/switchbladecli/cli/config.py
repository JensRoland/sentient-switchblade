import os
from pathlib import Path

import click
from tomlkit import loads


def get_switchblade_config(verbose, project_dir: str, config_file: str):
    config_file = os.path.join(project_dir, config_file)
    if verbose:
        click.echo(f"Loading configuration from {config_file}")

    config = loads(Path(config_file).read_text(encoding="utf-8"))

    config["project_dir"] = project_dir
    config["config_file"] = config_file

    return config
