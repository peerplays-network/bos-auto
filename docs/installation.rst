*****************************
Setup of Bookie Oracle Suite
*****************************

This article explains how the Bookie Oracle Suite (BOS) is installed,
tested and maintained. We start with installation and step-wise testing
and then go over to installing BOS-MINT (Manual intervention module) and
also show how to use the command line tool for inspections.

Overall Structure
=================

 .. image:: _static/flow.jpg
    :width: 600 px
    :alt: BOS Flow
    :align: center

Installation of bos-auto
============================

In this step, we install everything we will need going forward.

Install dependencies (as root/sudo)
---------------------

::

    apt-get install libffi-dev libssl-dev python-dev python3-pip
    pip3 install virtualenv
    
Note that virtualenv is a best practice for python, but installation can also be on a user/global level.

Install databases (as root/sudo)
-----------------

* `mongodb` - interaction between BOS-auto and MINT. You can find
  tutorials on how to install mongodb on your distribution in the
  internet
* `redis` - worker queue. Please find guides and installation
  instructions for your Linux distribution in the internet.

For Ubuntu 16.04. installation for mongodb is

::

    apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv EA312927
    echo "deb http://repo.mongodb.org/apt/ubuntu xenial/mongodb-org/3.2 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-3.2.list
    apt-get update
    apt-get install -y mongodb-org
    
and for redis 

:: 

    apt-get install build-essential
    apt-get install redis-server

It is highly recommended to ensure that both daemons are started on
powerup, e.g.

::

    systemctl enable mongod
    systemctl enable redis


Install bos-auto
-----------------

For production use install bos-auto via pip3. Suggested is a seperate user

::
    cd ~
    mkdir bos-auto
    cd bos-auto
    virtualenv -p python3 env
    source env/bin/activate
    pip3 install bos-auto
    
For development use, checkout from github and install dependencies manually

::
    cd ~	
    git checkout https://github.com/pbsa/bos-auto
    cd bos-auto
    virtualenv -p python3 env
    source env/bin/activate
    pip3 install -r requirements.txt



Configuration of bos-auto
=========================

We now proceed with the steps required to setup bos-auto properly.

.. warning:: At this point is is crucial to set the default witness node to
        your own server (ideally running in ``localhost``, see below config.yaml) using ``peerplays set node
        ws://ip:port``. If this step is skip, the setup will not work or work
        with very high latency at best.

Setup your python-peerplays wallet
----------------------------------

::
    # you will be asked to provide a new wallet passphrase. Later in the
    # tutorial you will be asked to store that password in a file
    # (config.yaml)
    peerplays createwallet

    # to add the key we need to make the node known (preferably on localhost)
    peerplays set node ws://localhost:8090
    
    peerplays addkey
    # You will be prompted to enter your active private key for the witness

Funding the account
-------------------

Since your witness account is going to create and approve proposals
automatically, you need to ensure that the witness account is funded
with PPY.

Modify configuration
--------------------

We now need to configure bos-auto.

::
   wget https://raw.githubusercontent.com/PBSA/bos-auto/master/config-example.yaml 
   mv config-example.yaml config.yaml
   # modify config.yaml

The variables are described below:

.. include:: ../config-example.yaml
   :literal:

Spinning up bos-auto
====================

In the following, we are spinning up bos-auto and see if it works
properly. To do so, we need to start an endpoint that takes incident
reports from the data proxy and stores them in mongodb as well as issues
work for the worker via redis. The worker then takes those incidents and
processes those. Postponed incidents are handled separately with a
scheduler.

Start the Endpoint
------------------
::

    cd bos-auto
    python3 cli.py api --host 0.0.0.0 --port 8010        [--help for more information]

After this, you will see the following messages if correctly set up:::

  INFO     | Opening Redis connection (redis://localhost/6379)
  * Running on http://0.0.0.0:8010/ (Press CTRL+C to quit)


This means that you can send incidents to `http://0.0.0.0:8010/``.

Testing
_______

You can test that the endpoint is properly running by::

    curl http://localhost:8010

In that case, the `api` daemon should print the following line::

     127.0.0.1 - - [26/Apr/2018 14:19:45] "GET / HTTP/1.1" 404 -

At this point, we are done with setting up the endpoint and can go
further setting up the actual worker.

Delivery to Data Proxies
________________________

Data proxies are interested in this particular endpoint as they will
push incidents to it. This means that you need to provide them with your
ip address as well as the port that you have opened above.

Advanced Setup
______________

The above setup is basic. Going forward, a witness may want to deploy
UWSGI with parallel workers for the endpoint, create a local socket and
hide it behind an SSL supported nginx that deals with a simple domain
isntead of ``ip:port`` pair, like ``https://dataproxy.mywitness.com/trigger``.

Start worker
------------

.. warning:: At this point is is cruciual to set the default witness node to
        your own server (ideally running in ``localhost``) using ``peerplays set node
        ws://ip:port``. If this step is skip, the setup will not work or work
        with very high latency at best.

We start the worker with::

    cd bos-auto
    python3 cli.py worker      [--help for more information]

It will already try to use the provided password to unlock the wallet
and, if successfull, present the following text to you::

    INFO     | Opening Redis connection (redis://localhost/6379)
    unlocking wallet ...
    14:21:53 RQ worker 'rq:worker:YOURHOSTNAME.554' started, version 0.9.2
    14:21:53 Cleaning registries for queue: default
    14:21:53 
    14:21:53 *** Listening on default...

Nothing else needs to be done at this point

Testing
_______

.. warning:: For testing, we highly recommend that you set the
           ``nobroadcast`` flag in ``config.yaml`` to ``True``!

For testing, we need do actually throw a properly formated incident at
the endpoint. To simplify this for witnesses, you can take the following
ones::

       {'provider_info': {'pushed': '2018-03-10T00:06:23Z', 'name': '5e2cdc120c9404f2609936aa3a8d49e4'}, 'call': 'create', 'timestamp': '2018-04-25T10:54:10.495868Z', 'arguments': {'unsure': True, 'season': '2018'}, 'unique_string': '2018-03-16t230000z-ice-hockey-nhl-regular-season-washington-capitals-new-york-islanders-create-2018-true', 'id': {'away': 'New York Islanders', 'event_group_name': 'NHL Regular Season', 'start_time': '2018-03-16T23:00:00Z', 'home': 'Washington Capitals', 'sport': 'Ice Hockey'}}
       {'provider_info': {'pushed': '2018-03-10T00:06:23Z', 'name': '5e2cdc1safasf4f2609936aa3a8d49e4'}, 'call': 'create', 'timestamp': '2018-04-25T10:54:10.495868Z', 'arguments': {'unsure': True, 'season': '2018'}, 'unique_string': '2018-03-16t230000z-ice-hockey-nhl-regular-season-washington-capitals-new-york-islanders-create-2018-true', 'id': {'away': 'New York Islanders', 'event_group_name': 'NHL Regular Season', 'start_time': '2018-03-16T23:00:00Z', 'home': 'Washington Capitals', 'sport': 'Ice Hockey'}}

store this in a file called ``replay.txt`` and run the following call::

    python3 cli.py replay --url http://localhost:8010/trigger replay.txt


.. note:: Please note the ``trigger`` at the end of the endpoint URL.

This will show you the incident and a load indicator at 100% once the
incident has been successfully sent to the endpoint.
   
This should cause your endpoint to print the following::

  INFO     | Forwarded incident create to worker via redis
  127.0.0.1 - - [26/Apr/2018 14:25:43] "POST /trigger HTTP/1.1" 200 -

and your worker to print something along the lines of (once for each
incident above)::

      14:23:38 default: bookied.work.process({'provider_info': {'pushed': '2018-03-10T00:06:23Z', 'name': '5e2cdc120c9404f2609936aa3a8d49e4'}, 'call': 'create', 'timestamp': '2018-04-25T10:54:10.495868Z', 'arguments': {'unsure': True, 'season': '2018'}, 'unique_string': '2018-03-16t230000z-ice-hockey-nhl-regular-season-washington-capitals-new-york-islanders-create-2018-true', 'id': {'away': 'New York Islanders', 'event_group_name': 'NHL Regular Season', 'start_time': '2018-03-16T23:00:00Z', 'home': 'Washington Capitals', 'sport': 'Ice Hockey'}, 'approver': 'init0', 'proposer': 'init0'}, approver=None, proposer=None) (a2f4eaaf-e750-4934-8c73-5481fe32df94)
        INFO     | processing create call with args {'unsure': True, 'season': '2018'}
        INFO     | Creating a new event ...
        INFO     | Creating event with teams ['Washington Capitals', 'New York Islanders'] in group NHL Regular Season.
        INFO     | Object "NHL Regular Season/Washington Capitals/New York Islanders" has pending update proposal. Approving {'pid': '1.10.413', 'oid': 0, 'proposal': <Proposal 1.10.413>}
        INFO     | Approval Map: {'1.10.224': '0.0', '1.10.413': '25.0', '1.10.414': '0.0', '1.10.416': '0.0'}
        INFO     | Object "New York Islanders @ Washington Capitals/Moneyline" has pending update proposal. Approving {'pid': '1.10.413', 'oid': 1, 'proposal': <Proposal 1.10.413>}
        INFO     | Approval Map: {'1.10.224': '0.0', '1.10.413': '50.0', '1.10.414': '0.0', '1.10.416': '0.0'}
        INFO     | Updating Betting Markets ...
        INFO     | Updating Betting Market New York Islanders ...
        INFO     | Object "Moneyline/New York Islanders" has pending update proposal. Approving {'pid': '1.10.413', 'oid': 2, 'proposal': <Proposal 1.10.413>}
        INFO     | Approval Map: {'1.10.224': '0.0', '1.10.413': '75.0', '1.10.414': '0.0', '1.10.416': '0.0'}
        INFO     | Updating Betting Market Washington Capitals ...
        INFO     | Object "Moneyline/Washington Capitals" has pending update proposal. Approving {'pid': '1.10.413', 'oid': 3, 'proposal': <Proposal 1.10.413>}
        INFO     | Approval Map: {'1.10.224': '0.0', '1.10.413': '100.0', '1.10.414': '0.0', '1.10.416': '0.0'}
        INFO     | Proposal 1.10.413 has already been approved by init0
        INFO     | Skipping dynamic BMG: New York Islanders @ Washington Capitals/Handicap
        INFO     | Skipping dynamic BMG: New York Islanders @ Washington Capitals/Over/Under {OU} pts
      14:23:45 default: Job OK (a2f4eaaf-e750-4934-8c73-5481fe32df94)
      14:23:45 Result is kept for 500 seconds
      14:23:45
      14:23:45 *** Listening on default...
      14:23:45 default: bookied.work.approve(approver=None, proposer=None) (cb914014-3bc1-4db7-b684-723826ce3c09)
        INFO     | Testing for pending proposals created by init0 that we could approve by init0
      14:23:45 default: Job OK (cb914014-3bc1-4db7-b684-723826ce3c09)
      14:23:45 Result is kept for 500 seconds
      14:23:45

.. note:: Each incident results in **two** work items, namely a
          ``bookied.work.process()`` as well as a
          ``bookied.work.approve()`` call. The former does the heavy
          lifting and may produce a proposal, while the latter approves
          proposals that we have created on our own.


Start Scheduler
===============

The schedulers task is to rerun incidents after a certain expiration
time. This may happen in cases where an event is postponed from being
opened because it would not add value until 2 weeks before the actual
match will happen. Those incidents are marked ``postoned`` internally
and will be retriggered into the worker with the scheduler:::

    cd bos-auto
    python3 cli.py scheduler   [--help for more information]

Command Line Intervention
#########################

With the ``cli.py`` tool, we can connect to the mongodb and inspect the
incidents that we have inserted above::

    python3 cli.py incidents list

The output should look like::

    +------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
    | identifier                   | Incidents                                                                                                                                                             |
    +------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
    | Ice Hockey                   | +--------+------------+----------------------------------------------------------------------------------------------------------+----------------------------------+ |
    | NHL Regular Season           | | call   | status     | incident uid                                                                                             | incident provider                | |
    | 2018-03-16T23:00:00Z         | +--------+------------+----------------------------------------------------------------------------------------------------------+----------------------------------+ |
    | home: Washington Capitals    | | create | name: done | 2018-03-16t230000z-ice-hockey-nhl-regular-season-washington-capitals-new-york-islanders-create-2018-true | 5e2cdc117c9404f2609936aa3a8d49e4 | |
    | away: New York Islanders     | |        |            | 2018-03-16t230000z-ice-hockey-nhl-regular-season-washington-capitals-new-york-islanders-create-2018-true | 5e2cdc120c9404f2609936aa3a8d49e4 | |
    |                              | +--------+------------+----------------------------------------------------------------------------------------------------------+----------------------------------+ |
    +------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+

It tells you that **two** incidents for that particular match came in
that both proposed to **create** the incident. The status tells us that
the incidents have been processed.

We can now read the actual incidents with::

    python3 cli.py incidents show 2018-03-16t230000z-ice-hockey-nhl-regular-season-washington-capitals-new-york-islanders-create-2018-true 5e2cdc117c9404f2609936aa3a8d49e4

and replay any of the two incidents by using::

    python3 cli.py incidents resend 2018-03-16t230000z-ice-hockey-nhl-regular-season-washington-capitals-new-york-islanders-create-2018-true 5e2cdc117c9404f2609936aa3a8d49e4

This should again cause your worker to start working.

Manual Intervention
###################

Bos-mint is a web-based manual intervention module that allows you to
do with all sorts of manual interactions with the blockchain. It comes
with it's own documentation at: http://bos-mint.readthedocs.io/
