import unittest
from flask_nemo import Nemo
from flask import Markup, Flask
from MyCapytain.resolvers.cts.local import CTSCapitainsLocalResolver
from MyCapytain.resolvers.cts.api import HttpCTSResolver
from MyCapytain.retrievers.cts5 import CTS
from MyCapytain.resources.collections.cts import TextInventory
from MyCapytain.resources.prototypes.cts.inventory import TextInventoryCollection
from MyCapytain.resolvers.utils import CollectionDispatcher
import logging


def create_test_app(debug=False, config=None):
    app = Flask(__name__)
    app.debug = debug

    if config:
        app.config.update(**config)
    return app


class RequestPatch(object):
    """ Request patch object to deal with patching reply in flask.ext.nemo
    """
    def __init__(self, f):
        self.__text = f.read()

    @property
    def text(self):
        return self.__text


class RequestPatchChained(object):
    """ Request patch object to deal with patching reply in flask.ext.nemo
    """
    def __init__(self, requests):
        self.resource = [other.text for other in requests]

    @property
    def text(self):
        return self.resource.pop(0)


class NemoResource(unittest.TestCase):
    """ Test Suite for Nemo
    """
    endpoint = HttpCTSResolver(CTS("http://website.com/cts/api"))
    body_xsl = "tests/test_data/xsl_test.xml"

    def setUp(self):
        with open("tests/test_data/getcapabilities.xml", "r") as f:
            self.getCapabilities = RequestPatch(f)

        with open("tests/test_data/getvalidreff.xml", "r") as f:
            self.getValidReff_single = RequestPatch(f)
            self.getValidReff = RequestPatchChained([self.getCapabilities, self.getValidReff_single])

        with open("tests/test_data/getpassage.xml", "r") as f:
            self.getPassage = RequestPatch(f)
            self.getPassage_Capabilities = RequestPatchChained([self.getCapabilities, self.getPassage])

        with open("tests/test_data/getpassageplus.xml", "r") as f:
            self.getPassagePlus = RequestPatch(f)

        with open("tests/test_data/getprevnext.xml", "r") as f:
            self.getPrevNext = RequestPatch(f)
            self.getPassage_Route = RequestPatchChained([self.getCapabilities, self.getPassage, self.getPrevNext])

        self.nemo = Nemo(
            resolver=NemoResource.endpoint,
            app=Flask(__name__)
        )

tic = TextInventoryCollection()
latin = TextInventory("urn:perseus:latinLit")
latin.parent = tic
latin.set_label("Classical Latin", "eng")
farsi = TextInventory("urn:perseus:farsiLit")
farsi.parent = tic
farsi.set_label("Farsi", "eng")
gc = TextInventory("urn:perseus:greekLit")
gc.parent = tic
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

NautilusDummy = CTSCapitainsLocalResolver(
    resource=[
        "./tests/test_data/nautilus/farsiLit",
        "./tests/test_data/nautilus/latinLit"
    ],
    dispatcher=dispatcher
)
NautilusDummy.logger.setLevel(logging.ERROR)
