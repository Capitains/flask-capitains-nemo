import unittest
from flask.ext.nemo import Nemo
from flask import Markup, Flask
from capitains_nautilus.mycapytain import NautilusEndpoint

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
    endpoint = "http://website.com/cts/api"
    body_xsl = "testing_data/xsl_test.xml"

    def setUp(self):
        with open("testing_data/getcapabilities.xml", "r") as f:
            self.getCapabilities = RequestPatch(f)

        with open("testing_data/getvalidreff.xml", "r") as f:
            self.getValidReff_single = RequestPatch(f)
            self.getValidReff = RequestPatchChained([self.getCapabilities, self.getValidReff_single])

        with open("testing_data/getpassage.xml", "r") as f:
            self.getPassage = RequestPatch(f)
            self.getPassage_Capabilities = RequestPatchChained([self.getCapabilities, self.getPassage])

        with open("testing_data/getprevnext.xml", "r") as f:
            self.getPrevNext = RequestPatch(f)
            self.getPassage_Route = RequestPatchChained([self.getCapabilities, self.getPassage, self.getPrevNext])

        self.nemo = Nemo(
            api_url=NemoResource.endpoint
        )

NautilusDummy = NautilusEndpoint(folders=["./tests/test_data/nautilus/farsiLit", "./tests/test_data/nautilus/latinLit"])
