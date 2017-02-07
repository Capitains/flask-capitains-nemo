from flask import Flask
from flask_nemo import Nemo


def make_client(*args, **kwargs):
    app = Flask("Nemo")
    app.debug = True
    if len(args):
        nemo = Nemo(
            app=app,
            base_url="",
            plugins=list(args),
            **kwargs
        )
    else:
        nemo = Nemo(
            app=app,
            base_url="",
            plugins=None,
            **kwargs
        )
    return app.test_client()
