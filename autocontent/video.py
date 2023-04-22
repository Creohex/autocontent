
import click


@click.command()
def a():
    print("a")

@click.group
def grp():
    pass

grp.add_command(a)
