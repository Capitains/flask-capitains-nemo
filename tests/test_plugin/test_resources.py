from flask import Flask
from flask_nemo import Nemo
from tests.test_resources import NautilusDummy
from flask_nemo.chunker import level_grouper


def make_client(*args, **kwargs):
    app = Flask("Nemo")
    app.debug = True
    if len(args):
        nemo = Nemo(
            app=app,
            base_url="",
            resolver=NautilusDummy,
            chunker={"default": lambda x, y: level_grouper(x, y, groupby=30)},
            plugins=list(args),
            **kwargs
        )
    else:
        nemo = Nemo(
            app=app,
            base_url="",
            resolver=NautilusDummy,
            chunker={"default": lambda x, y: level_grouper(x, y, groupby=30)},
            plugins=None,
            **kwargs
        )
    return app.test_client()