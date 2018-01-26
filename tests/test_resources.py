import unittest
from flask_nemo import Nemo
from flask import Markup, Flask
from MyCapytain.resolvers.cts.local import CtsCapitainsLocalResolver
from MyCapytain.resolvers.cts.api import HttpCtsResolver
from MyCapytain.retrievers.cts5 import HttpCtsRetriever
from MyCapytain.resources.collections.cts import XmlCtsTextInventoryMetadata
from MyCapytain.resources.prototypes.cts.inventory import CtsTextInventoryCollection
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
    encoding = "utf-8"

    def __init__(self, f):
        self.__text = f.read()

    @staticmethod
    def raise_for_status():
        return None

    @property
    def text(self):
        return self.__text


class RequestPatchChained(RequestPatch):
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
    endpoint = HttpCtsResolver(HttpCtsRetriever("http://website.com/cts/api"))
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

tic = CtsTextInventoryCollection()
latin = XmlCtsTextInventoryMetadata("urn:perseus:latinLit")
latin.parent = tic
latin.set_label("Classical Latin", "eng")
farsi = XmlCtsTextInventoryMetadata("urn:perseus:farsiLit")
farsi.parent = tic
farsi.set_label("Farsi", "eng")
gc = XmlCtsTextInventoryMetadata("urn:perseus:greekLit")
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

NautilusDummy = CtsCapitainsLocalResolver(
    resource=[
        "./tests/test_data/nautilus/farsiLit",
        "./tests/test_data/nautilus/latinLit"
    ],
    dispatcher=dispatcher
)
NautilusDummy.logger.setLevel(logging.ERROR)
