#!/usr/bin/env python3


def run():
    from bookie.web import app
    app.run(debug=True)


if __name__ == "__main__":
    run()
