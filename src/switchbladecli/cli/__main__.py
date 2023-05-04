import os

import click

from switchbladecli.cli.config import find_config_file, get_switchblade_config
from switchbladecli.cli.lint import lint
from switchbladecli.cli.test import test
from switchbladecli.cli.update import update

ALIASES = {}


class AliasedGroup(click.Group):
    def get_command(self, ctx, cmd_name):
        try:
            cmd_name = ALIASES[cmd_name].name
        except KeyError:
            pass
        return super().get_command(ctx, cmd_name)


# We pass the project directory to all subcommands via the context
# so they can use it to find the switchblade.toml file
@click.group(cls=AliasedGroup)
@click.option("--config", "config_file", help="Path to Switchblade configuration file.")
@click.option("--verbose", is_flag=True, default=False, help="Show verbose output")
@click.pass_context
def switchbladecli(
    ctx, config_file, verbose
): 
    """Sentient Switchblade

    A part of the Beth Developer Toolbelt
    """
    config_file = find_config_file(verbose, config_file)

    project_dir = os.path.abspath(os.path.dirname(config_file))

    config = get_switchblade_config(verbose, project_dir, config_file)

    ctx.obj = {
        "config": config,
        "config_file": os.path.abspath(config_file),
        "project_dir": project_dir,
        "verbose": verbose,
    }


for command in [update, lint, test]:
    switchbladecli.add_command(command)


if __name__ == "__main__":
    switchbladecli(obj={})  # pylint: disable=no-value-for-parameter
