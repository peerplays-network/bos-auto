#!/usr/bin/env python3

import click


@click.command()
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
@click.option(
    "--proposer"
)
@click.option(
    "--approver"
)
def main(port, host, debug, proposer, approver):
    """ Start the endpoint
    """
    from bookie.web import app
    app.config["BOOKIE_PROPOSER"] = proposer
    app.config["BOOKIE_APPROVER"] = approver
    app.run(
        host=host,
        port=port,
        debug=debug
    )


if __name__ == "__main__":
    main()
