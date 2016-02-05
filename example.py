# Import Flask and Nemo
# This script can take a first argument giving a configuration from examples.py
from flask import Flask
from flask.ext.nemo import Nemo
from examples.configs import configs, classes
from sys import argv
from pkg_resources import resource_filename


if __name__ == "__main__":
    # We select a configuration, see more in examples/configs
    key = "default"
    port = 5000
    if len(argv) > 1 and argv[1] in configs:
        key = argv[1]
        Nemo = classes[key]
        if len(argv) > 2:
            port = int(argv[2])

    # We create a Flask app
    app = Flask(
        __name__
    )

    # We set up Nemo
    nemo = Nemo(
        app=app,
        name="nemo",
        **configs[key]
    )
    # We register its routes
    nemo.register_routes()
    # We register its filters
    nemo.register_filters()


    # We run the app
    app.debug = True

    app.run(port=port)
