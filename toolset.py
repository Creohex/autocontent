#!/Users/creohex/github/autocontent/.venv/bin/python

import click
from autocontent import groups


if __name__ == "__main__":
    multi_group = click.CommandCollection(sources=groups)
    multi_group()
