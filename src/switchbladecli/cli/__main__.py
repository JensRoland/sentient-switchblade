import os

import click

from switchbladecli.cli.update import update
from switchbladecli.cli.lint import lint

ALIASES = {}

CONFIG_FILE_NAMES = [".switchblade", "switchblade.toml"]


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
@click.option("--config", help="Path to Switchblade configuration file.")
@click.option("--verbose", is_flag=True, default=False, help="Show verbose output")
@click.pass_context
def switchbladecli(
    ctx, config, verbose
): 
    """Sentient Switchblade

    A part of the Beth Developer Toolbelt
    """
    # Locate the correct Kegstand configuration file
    if config is None:
        for name in CONFIG_FILE_NAMES:
            if os.path.exists(name):
                config = name
                break

    if not os.path.exists(config):
        raise click.ClickException(f"Configuration file not found: {config}")

    project_dir = os.path.abspath(os.path.dirname(config))
    ctx.obj = {
        "config": os.path.abspath(config),
        "project_dir": project_dir,
        "verbose": verbose,
    }


for command in [update, lint]:
    switchbladecli.add_command(command)


if __name__ == "__main__":
    switchbladecli(obj={})  # pylint: disable=no-value-for-parameter
