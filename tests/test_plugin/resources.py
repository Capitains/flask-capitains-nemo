from flask import Flask
from flask_nemo import Nemo
from tests.resources import NautilusDummy

def make_client(*args, **kwargs):
    app = Flask("Nemo")
    app.debug = True
    if len(args):
        nemo = Nemo(
            app=app,
            base_url="",
            retriever=NautilusDummy,
            chunker={"default": lambda x, y: Nemo.level_grouper(x, y, groupby=30)},
            plugins=list(args),
            **kwargs
        )
    else:
        nemo = Nemo(
            app=app,
            base_url="",
            retriever=NautilusDummy,
            chunker={"default": lambda x, y: Nemo.level_grouper(x, y, groupby=30)},
            plugins=None,
            **kwargs
        )
    return app.test_client()