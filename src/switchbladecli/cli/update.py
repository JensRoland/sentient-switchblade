import click

from operator import itemgetter
from switchbladecli.cli.bundle_cache import Bundle


@click.command()
@click.pass_context
def update(ctx):
    project_dir, config, verbose = itemgetter("project_dir", "config", "verbose")(ctx.obj)
    cmd_update(verbose, project_dir, config)


def cmd_update(verbose: bool, project_dir: str, config: dict):
    # Instantiating a Bundle object will fetch the latest bundle from the source or cache
    Bundle(config)
