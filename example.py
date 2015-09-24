# Import Flask and Nemo
from flask import Flask
from flask.ext.nemo import Nemo

# We create a Flask app
app = Flask(
    __name__,
    static_folder="data/static"
)
# We set up Nemo
nemo = Nemo(
    app=app,
    api_url="http://services2.perseids.org/exist/restxq/cts",
    base_url="",
    inventory="nemo"
)
nemo.register_routes()
nemo.register_filters()
# We run the app
app.debug = True
app.run()
