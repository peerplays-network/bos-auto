#!/usr/bin/env python3

import sys
from rq import Connection, Worker


with Connection():
    w = Worker(sys.argv[1:] or ['default'])
    w.work()
