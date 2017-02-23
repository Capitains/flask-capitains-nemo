# Import Flask and Nemo
# This script can take a first argument giving a configuration from examples.py
from flask import Flask
from flask_nemo import Nemo
from flask_caching import Cache
from flask_nemo.chunker import level_grouper
from MyCapytain.resolvers.cts.local import CTSCapitainsLocalResolver
from MyCapytain.resources.collections.cts import TextInventory
from MyCapytain.resources.prototypes.cts.inventory import TextInventoryCollection
from MyCapytain.resolvers.utils import CollectionDispatcher
import logging

# We create a Flask app
app = Flask(
    __name__
)

tic = TextInventoryCollection()
latin = TextInventory("urn:perseus:latinLit", parent=tic)
latin.set_label("Classical Latin", "eng")
farsi = TextInventory("urn:perseus:farsiLit", parent=tic)
farsi.set_label("Farsi", "eng")
gc = TextInventory("urn:perseus:greekLit", parent=tic)
gc.set_label("Ancient Greek", "eng")
gc.set_label("Grec Ancien", "fre")

dispatcher = CollectionDispatcher(tic)


@dispatcher.inventory("urn:perseus:latinLit")
def dispatchLatinLit(collection, path=None, **kwargs):
    if collection.id.startswith("urn:cts:latinLit:"):
        return True
    return False


@dispatcher.inventory("urn:perseus:farsiLit")
def dispatchfFarsiLit(collection, path=None, **kwargs):
    if collection.id.startswith("urn:cts:farsiLit:"):
        return True
    return False


@dispatcher.inventory("urn:perseus:greekLit")
def dispatchGreekLit(collection, path=None, **kwargs):
    if collection.id.startswith("urn:cts:greekLit:"):
        return True
    return False

cache = Cache()

NautilusDummy = CTSCapitainsLocalResolver(
    resource=[
        #"../../canonicals/First1KGreek",
        "repositories/canonical-latinLit",
        "repositories/canonical-greekLit",
        "repositories/canonical-farsiLit",
        #"./tests/test_data/nautilus/farsiLit",
        #"./tests/test_data/nautilus/latinLit"
    ],
    dispatcher=dispatcher
)
NautilusDummy.logger.setLevel(logging.ERROR)

nemo = Nemo(
    app=app,
    base_url="",
    resolver=NautilusDummy,
    chunker={"default": lambda x, y: level_grouper(x, y, groupby=20)},
    plugins=None,
    cache=cache,
    transform={
        "default": "/home/thibault/dev/perseus_nemo_ui/aperire_ui/data/assets/static/xslt/epidocShort.xsl"
    }
)

cache.init_app(app)

if __name__ == "__main__":
    app.run()
