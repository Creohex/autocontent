import click
from .cli import grp


multi_group = click.CommandCollection(sources=[grp])
