import click

from switchbladecli.cli.bundle_cache import Bundle


@click.command()
@click.pass_context
def update(ctx):
    project_dir = ctx.obj["project_dir"]
    config = ctx.obj["config"]
    verbose = ctx.obj["verbose"]
    update_command(verbose, project_dir, config)


def update_command(verbose: bool, project_dir: str, config: dict):
    # Instantiating a Bundle object will fetch the latest bundle from the source or cache
    latest_bundle = Bundle(config)
