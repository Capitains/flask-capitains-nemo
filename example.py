# Import Flask and Nemo
from flask import Flask
from flask.ext.nemo import Nemo

# We create a Flask app
app = Flask(
    __name__,
    template_folder="data/templates",
    static_folder="data/static"
)
# We set up Nemo
nemo = Nemo(
    app=app,
    api_url="http://localhost:8080/exist/restxq/cts",
    base_url="/"
)
nemo.register_routes()
# We run the app
app.debug = True
app.run()
