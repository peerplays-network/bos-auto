.. Bookied documentation master file, created by
   sphinx-quickstart on Thu Nov  9 12:48:47 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Bookied's documentation!
===================================

`bookied` comes with a worker and an API to receive notifications of a
feed data provider. The API receives those messages, validates them, and
queues them for a worker to perform corresponding tasks. Since the
queuing is performed via `redis <https://redis.io>`_, a redis backend
must be present.

Outline
-------
.. toctree::
   :maxdepth: 3

   config
   cli
   schema
   web
   worker

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
