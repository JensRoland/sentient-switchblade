import click

class MissingConfiguration(click.ClickException):
    pass

class MissingRequiredConfigKey(click.ClickException):
    pass

class InvalidConfigValue(click.ClickException):
    pass

class UnrecognizedConfigKey(click.ClickException):
    pass
