import socket


def resolve_hostnames(l):
    r = list()
    assert isinstance(l, (list, set))
    for line in l:
        r.append(socket.gethostbyname(line.strip()))
    return r


def dList2Dict(l):
    return {v[0]: v[1] for v in l}


def dict2dList(l):
    return [[k, v] for k, v in l.items()]
