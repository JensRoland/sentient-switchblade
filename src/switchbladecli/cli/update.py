import click

from switchbladecli.cli.bundle_cache import Bundle
from switchbladecli.cli.config import get_switchblade_config


@click.command()
@click.pass_context
def update(ctx):
    project_dir = ctx.obj["project_dir"]
    config_file = ctx.obj["config"]
    verbose = ctx.obj["verbose"]
    update_command(verbose, project_dir, config_file)


def update_command(verbose: bool, project_dir: str, config_file: str):
    config = get_switchblade_config(verbose, project_dir, config_file)
    # Instantiating a Bundle object will fetch the latest bundle from the source or cache
    latest_bundle = Bundle(config)
