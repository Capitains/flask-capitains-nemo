# Import Flask and Nemo
from flask import Flask
from flask.ext.nemo import Nemo

# We create a Flask app
app = Flask(
    __name__,
    static_folder="data/static"
)
chunker = {
    # The default chunker takes care of book, poem, lines
    # but it would be cool to have 30 lines group for Nemo
    "urn:cts:latinLit:phi1294.phi002.perseus-lat2": lambda text, cb: [(reff.split(":")[-1], reff.split(":")[-1]) for reff in cb(2)],
    "default": Nemo.scheme_chunker  # lambda text, cb: Nemo.line_grouper(text, cb, 50)
}
# We set up Nemo
nemo = Nemo(
    app=app,
    api_url="http://services2.perseids.org/exist/restxq/cts",
    base_url="",
    inventory="nemo",
    xslt="/home/thibault/Dropbox/Thèse/corpus/xsl/viz-ms1.xsl",  # Use default epidoc XSLT
    css=["/home/thibault/dev/capitains/flask-capitains-nemo/examples/ciham.css"],
    chunker=chunker
)
nemo.register_routes()
nemo.register_filters()
# We run the app
app.debug = True
app.run()
