import click
from .cli import grp
# from .utils import Config


multi_group = click.CommandCollection(sources=[grp])
# config = Config()
