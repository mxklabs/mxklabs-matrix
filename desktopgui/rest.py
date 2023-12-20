from inspect import getfullargspec
import pickle
import base64
import json
import pathlib
from enum import Enum

from flask import Flask, request
import requests

class RequestType(str, Enum):
    GET = "GET"
    POST = "POST"

def serialize(x):
    return base64.b64encode(pickle.dumps(x)).decode("utf-8")

def deserialize(x):
    return pickle.loads(base64.b64decode(x.encode("utf-8") if type(x) == str else x))

with open(pathlib.Path(__file__).parents[0] / "config.json", "r") as f:
    CONFIG = json.load(f)

SERVER_STRING = f"http://{CONFIG['connectToIP4Addr']}:{CONFIG['port']}"

def client_api(api):
    for i in dir(api):
        if i.startswith("__"):
            continue
        f = getattr(api, i)
        if not hasattr(f, "is_endpoint"):
            continue
        sig = getfullargspec(f)
        def wrapper_to_keep_f_constant(f=f, sig=sig):
            def newfunc(*args, **kwargs):
                data = {}

                for i,arg in enumerate(args):
                    name = sig.args[i+1]
                    data[name] = serialize(arg)

                for k,v in kwargs:
                    data[k] = serialize(v)
                if f.rtype == RequestType.GET:
                    res = requests.get(SERVER_STRING + f.path, params=data)
                if f.rtype == RequestType.POST:
                    res = requests.post(SERVER_STRING + f.path, json=data)
                return deserialize(res.content)
            return newfunc
        setattr(api, i, wrapper_to_keep_f_constant())
    return api

def server_api(api):
    api.app = Flask(__name__)
    for i in dir(api):
        if i.startswith("__"):
            continue
        f = getattr(api, i)
        if not hasattr(f, "is_endpoint"):
            continue
        sig = getfullargspec(f)
        def wrappingfunc(f=f, sig=sig):
            if f.rtype == RequestType.POST:
                data = request.json
            else:
                data = request.args
            kwargs = {}
            for k,v in data.items():
                argtype = sig.annotations[k]
                kwargs[k] = deserialize(v)
            res = f(**kwargs)
            return serialize(res)
        wrappingfunc.__name__ = f.__name__
        api.app.route(f.path, methods=[f.rtype])(wrappingfunc)
    return api

def endpoint(rtype: RequestType, path):
    def wrapper(func):
        func.path = path
        func.is_endpoint = True
        func.rtype = rtype
        return func
    return wrapper
