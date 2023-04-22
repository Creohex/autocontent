#!/Users/creohex/github/autocontent/.venv/bin/python

import click
from autocontent import groups

if __name__ == "__main__":
    grp = click.CommandCollection(sources=groups)
    grp()
