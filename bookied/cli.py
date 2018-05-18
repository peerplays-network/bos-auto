#!/usr/bin/env python3

import click
from click_datetime import Datetime
from rq import Connection, Worker, use_connection, Queue
from .config import loadConfig
from .log import log
from prettytable import PrettyTable, ALL as ALLBORDERS
from dateutil import parser
from pprint import pprint

config = loadConfig()

INCIDENT_CALLS = [
    "create",
    "in_progress",
    "finish",
    "result"]


def format_incidents(event):
    incidents = PrettyTable(
        ["call", "status", "incident uid", "incident provider"],
    )
    incidents.align = 'l'
    for call, content in event.items():
        if "incidents" not in content:
            continue

        try:  # FIXME why can some incidents not be resolved?
            incidents.add_row([
                call,
                "\n".join(["{}: {}".format(k, v) for (k, v) in content["status"].items()]),
                "\n".join([x["unique_string"] for x in content["incidents"]]),
                "\n".join([x["provider_info"]["name"] for x in content["incidents"]])
            ])
        except:
            pass
    return incidents


@click.group()
def main():
    """ Main group for python-click so we can offer subcommands in a single cli
        tool
    """
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
@click.option(
    "--proposer"
)
@click.option(
    "--approver"
)
def api(port, host, debug, proposer, approver):
    """ Start the API endpoint
    """
    from bookied.web import app
    app.config["BOOKIE_PROPOSER"] = proposer
    app.config["BOOKIE_APPROVER"] = approver
    app.run(
        host=host,
        port=port,
        debug=debug
    )


@main.command()
@click.argument("queue", default="default")
def worker(queue):
    """ Start the (redis queue) worker to deal with the received messages
    """
    from .redis_con import get_redis
    from . import work
    work.unlock()
    with Connection(get_redis()):
        w = Worker([queue])
        w.work()


@main.command()
@click.option(
    "--proposer",
    default=config.get("BOOKIE_PROPOSER")
)
@click.option(
    "--approver",
    default=config.get("BOOKIE_APPROVER")
)
def approve(proposer, approver):
    """ Send an approve ticket to the queue
    """
    from .redis_con import get_redis
    from . import work
    redis = get_redis()
    work.unlock()
    use_connection(redis)
    q = Queue(connection=redis)
    q.enqueue(
        work.approve,
        args=(),
        kwargs=dict(
            proposer=proposer,
            approver=approver
        )
    )


@main.command()
@click.argument(
    "filename",
    type=click.File('rb'))
@click.option(
    "--proposer",
    default=config.get("BOOKIE_PROPOSER")
)
@click.option(
    "--approver",
    default=config.get("BOOKIE_APPROVER")
)
@click.option(
    "--call",
    default=None,
    type=click.Choice(INCIDENT_CALLS)
)
@click.option(
    "--dry-run/--no-dry-run",
    default=False)
@click.option(
    "--url",
    default="http://localhost:8010/trigger"
)
def replay(filename, proposer, approver, url, call, dry_run):
    """ Replay incidents from a file
    """
    from tqdm import tqdm
    import requests
    for line in tqdm(filename.readlines()):
        data = eval(line)
        data.update(dict(approver=approver, proposer=proposer))

        # Filter by "call"
        if call and call.lower() != data["call"]:
            continue

        # Print
        pprint(data)

        # Request
        if dry_run:
            log.warning("Skipping push fue to 'dry-run'")
            continue

        try:
            ret = requests.post(
                url,
                json=data,
                headers={'Content-Type': 'application/json'}
            )
            if ret.status_code != 200:
                raise Exception("Status code: {}: {}".format(
                    ret.status_code,
                    ret.text))
        except Exception as e:
            log.error("[Error] Failed pushing")
            log.error(str(e))


@main.command()
def scheduler():
    """ Test for postponed incidents and process them
    """
    from .schedule import scheduler
    scheduler()


@main.group()
def incidents():
    """ Incidents calls
    """
    pass


@main.group()
def events():
    """ Commands affecting multiple events
    """
    pass


@main.group()
def event():
    """ Event-specific calls commands
    """
    pass


@events.command()
def list():
    """ List events
    """
    from bos_incidents import factory
    t = PrettyTable(["identifier", "Incidents"], hrules=ALLBORDERS)
    t.align = 'l'

    storage = factory.get_incident_storage()

    for event in storage.get_events(resolve=False):
        t.add_row([
            event["id_string"],
            {x: len(event.get(x, [])) for x in INCIDENT_CALLS}
        ])
    click.echo(str(t))


@event.command()
@click.argument("identifier")
def show(identifier):
    """ List events
    """
    from bos_incidents import factory
    t = PrettyTable(["identifier", "Incidents"], hrules=ALLBORDERS)
    t.align = 'l'

    storage = factory.get_incident_storage()
    event = storage.get_event_by_id(identifier)
    incidents = format_incidents(event)
    id = event["id"]
    id["start_time"] = parser.parse(id["start_time"]).replace(
        tzinfo=None)
    t.add_row([
        "\n".join([
            id["sport"],
            id["event_group_name"],
            id["start_time"].strftime("%Y/%m/%d"),
            "home: {}".format(id["home"]),
            "away: {}".format(id["away"]),
        ]),
        str(incidents)
    ])
    click.echo(t)


@event.command()
@click.argument("identifier")
@click.argument("call", required=False, default="*")
@click.argument("status_name", required=False)
@click.option(
    "--url",
    default="http://localhost:8010/trigger"
)
def replay(identifier, call, status_name, url):
    """ replay from event
    """
    import requests
    from bos_incidents import factory
    storage = factory.get_incident_storage()
    event = storage.get_event_by_id(identifier, resolve=False)

    for incident_call, content in event.items():

        if not content or "incidents" not in content:
            continue

        if call and call != "*" and incident_call != call:
            continue

        if status_name and content["status"]["name"] != status_name:
            continue

        for _incident in content["incidents"]:
            incident = storage.resolve_to_incident(_incident)

            pprint(incident)
            incident.update(dict(skip_storage=True))

            try:
                ret = requests.post(
                    url,
                    json=incident,
                    headers={'Content-Type': 'application/json'}
                )
                if ret.status_code != 200:
                    raise Exception("Status code: {}: {}".format(
                        ret.status_code,
                        ret.text))
            except Exception as e:
                log.error("[Error] Failed pushing")
                log.error(str(e))


@incidents.command()
@click.argument("begin", required=False, type=Datetime(format='%Y/%m/%d'))
@click.argument("end", required=False, type=Datetime(format='%Y/%m/%d'))
def list(begin, end):
    """ List incidents from the bos-incidents store
    """
    from bos_incidents import factory
    t = PrettyTable(["identifier", "Incidents"], hrules=ALLBORDERS)
    t.align = 'l'

    storage = factory.get_incident_storage()

    for event in storage.get_events():

        # pprint(event)
        if not ("id" in event and event["id"]):
            continue
        id = event["id"]
        id["start_time"] = parser.parse(id["start_time"]).replace(
            tzinfo=None)

        # Limit time
        if begin and end and (id["start_time"] < begin or id["start_time"] > end):
            continue

        incidents = format_incidents(event)

        t.add_row([
            "\n".join([
                id["sport"],
                id["event_group_name"],
                id["start_time"].strftime("%Y/%m/%d"),
                "home: {}".format(id["home"]),
                "away: {}".format(id["away"]),
            ]),
            str(incidents)
        ])

    click.echo(t)


@incidents.command()
@click.argument("unique_string")
@click.argument("provider")
def show(unique_string, provider):
    """ Show the content of a specific incidents
    """
    from bos_incidents import factory
    storage = factory.get_incident_storage()
    incident = storage.get_incident_by_unique_string_and_provider(
        unique_string, provider)
    pprint(incident)


@incidents.command()
@click.argument("unique_string")
@click.argument("provider")
def rm(unique_string, provider):
    """ Remove an incident from the store
    """
    from bos_incidents import factory
    storage = factory.get_incident_storage()
    incident = storage.get_incident_by_unique_string_and_provider(
        unique_string, provider)
    storage.delete_incident(incident)


@incidents.command()
def purge():
    """ Purge the entire store
    """
    from bos_incidents import factory
    factory.get_incident_storage(purge=True)


@incidents.command()
@click.argument("unique_string")
@click.argument("provider")
@click.option(
    "--url",
    default="http://localhost:8010/trigger"
)
def resend(url, unique_string, provider):
    """ Resend one or more incidents from the store
    """
    from bos_incidents import factory
    import requests
    storage = factory.get_incident_storage()
    incident = storage.get_incident_by_unique_string_and_provider(
        unique_string, provider)
    pprint(incident)
    incident.update(dict(skip_storage=True))
    try:
        ret = requests.post(
            url,
            json=incident,
            headers={'Content-Type': 'application/json'}
        )
        if ret.status_code != 200:
            raise Exception("Status code: {}: {}".format(
                ret.status_code,
                ret.text))
    except Exception as e:
        log.error("[Error] Failed pushing")
        log.error(str(e))


@incidents.command()
@click.argument("call", required=False, default="*")
@click.argument("status_name", required=False)
@click.argument("begin", required=False, type=Datetime(format='%Y/%m/%d'))
@click.argument("end", required=False, type=Datetime(format='%Y/%m/%d'))
@click.option(
    "--url",
    default="http://localhost:8010/trigger"
)
def resendall(url, call, status_name, begin, end):
    """ Resend everything in the store that matches a call and status_name
    """
    from bos_incidents import factory
    import requests
    storage = factory.get_incident_storage()
    for event in storage.get_events(resolve=False):

        for incident_call, content in event.items():

            if not content or "incidents" not in content:
                continue

            if call and call != "*" and incident_call != call:
                continue

            if status_name and content["status"]["name"] != status_name:
                continue

            for _incident in content["incidents"]:
                incident = storage.resolve_to_incident(_incident)

                id = incident["id"]
                start_time = parser.parse(id["start_time"]).replace(
                    tzinfo=None)

                # Limit time
                if begin and end and (start_time < begin or start_time > end):
                    continue

                pprint(incident)
                incident.update(dict(skip_storage=True))

                try:
                    ret = requests.post(
                        url,
                        json=incident,
                        headers={'Content-Type': 'application/json'}
                    )
                    if ret.status_code != 200:
                        raise Exception("Status code: {}: {}".format(
                            ret.status_code,
                            ret.text))
                except Exception as e:
                    log.error("[Error] Failed pushing")
                    log.error(str(e))


if __name__ == "__main__":
    main()
