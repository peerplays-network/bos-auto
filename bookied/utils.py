import socket


def resolve_hostnames(l):
    r = list()
    if not l:
        return r
    for line in l:
        r.append(socket.gethostbyname(line.strip()))
    return r
