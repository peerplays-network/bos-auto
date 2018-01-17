Configuration
=============

The default configuration looks like the following and is (by default)
stored in ``config.yaml``:

.. include:: ../config-example.yaml
   :literal:

Both, the API and the worker make use of the same configuration file.
We need to provide the wallet passphrase in order for the worker to be
able to propose changes to the blockchain objects according to the
messages received from the data feed.

.. autofunction:: bookied.config.loadConfig
