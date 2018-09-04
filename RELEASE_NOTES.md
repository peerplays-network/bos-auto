Release 0.1.9
-------------

* Worker restart purges redis and replays incidents from mongo store.
* The default scheduler time has been raised from 60s to 1h to reduce
  stress on queue.
* Fix library stop after "broken pipe" error

Release 0.1.8
-------------

* The scheduler no longer needs to be started manually but is spawn
  automatically by the API process. Optionally, the api can be started
  with `--no-scheduler` to prevent the scheduler from being spawn.
