#!/usr/bin/env python3

import click


@click.group()
def main():
    pass


@main.command()
@click.option(
    "--port",
    type=int,
    default=8010
)
@click.option(
    "--host",
    type=str,
    default="127.0.0.1"
)
@click.option(
    "--host",
    type=str,
    default="127.0.0.1"
)
@click.option(
    '--debug',
    is_flag=True,
    default=False
)
def start(port, host, debug):
    """ Start the webendpoint
    """
    from bookie.web import app
    app.run(
        host=host,
        port=port,
        debug=debug
    )


if __name__ == "__main__":
    main()
