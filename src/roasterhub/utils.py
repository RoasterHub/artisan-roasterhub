import pickle
import typing.io


def read_alog(file: typing.io) -> dict:
    with open('/home/skater/Documents/20-04-25_0931.alog', 'rb') as f:
        data = f.read()
    return eval(data)

