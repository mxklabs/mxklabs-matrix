from inspect import getfullargspec

from flask import Flask, request
import requests

def serialize(x, argtype):
    if argtype == int:
        return str(x)
    if argtype == str:
        return x
    raise NotImplementedError(f"Type {argtype} not supported.")

def deserialize(x, argtype):
    if argtype == int:
        return int(x)
    if argtype == str:
        return x
    raise NotImplementedError(f"Type {argtype} not supported.")

SERVER_STRING = "http://127.0.0.1:5000"

class ClientAPI:
    def __new__(self):
        for i in dir(self):
            if i.startswith("__"):
                continue
            f = getattr(self, i)
            if not hasattr(f, "is_endpoint"):
                continue
            sig = getfullargspec(f)
            def newfunc(*args, **kwargs):
                print(args, kwargs)
                data = {}

                for i,arg in enumerate(args):
                    name = sig.args[i+1]
                    argtype = sig.annotations[name]
                    data[name] = serialize(arg, argtype)

                for k,v in kwargs:
                    argtype = sig.annotations[k]
                    data[k] = serialize(v, argtype)
                requests.post(SERVER_STRING + f.path, json=data)
            setattr(self, i, newfunc)
        return self

class ServerAPI:
    def __init__(self):
        self.app = Flask(__name__)
        for i in dir(self):
            if i.startswith("__"):
                continue
            f = getattr(self, i)
            if not hasattr(f, "is_endpoint"):
                continue
            sig = getfullargspec(f)
            @self.app.route(f.path, methods=['GET', 'POST'])
            def wrappingfunc():
                data = request.json
                kwargs = {}
                for k,v in data.items():
                    argtype = sig.annotations[k]
                    kwargs[k] = deserialize(v, argtype)
                return f(**kwargs)

    def run(self):
        self.app.run()

def endpoint(path):
    def wrapper(func):
        func.path = path
        func.is_endpoint = True
        return func
    return wrapper
