import unittest
from flask.ext.nemo import Nemo
from mock import patch


class RequestPatch(object):
    """ Request patch object to deal with patching reply in flask.ext.nemo
    """
    def __init__(self, f):
        self.f = f
        self.__text = f.read()

    @property
    def text(self):
        return self.__text


class NemoTest(unittest.TestCase):
    """ Test Suite for Nemo
    """
    endpoint = "http://website.com/cts/api"
    def setUp(self):
        with open("testing_data/getcapabilities.xml", "r") as f:
            self.getCapabilities = RequestPatch(f)
        self.nemo = Nemo(
            api_url=NemoTest.endpoint
        )

    def test_flask_nemo(self):
        """ Testing Flask Nemo is set up"""
        a = Nemo()
        self.assertIsInstance(a, Nemo)

        #  Test the right endpoint was called

    def test_request_endpoint(self):
        """ Check that endpoint are derived from nemo.api_endpoint setting
        """
        with patch('requests.get', return_value=self.getCapabilities) as patched_get:
            self.nemo.get_inventory()
            patched_get.assert_called_once_with(
                NemoTest.endpoint, params={
                    "request": "GetCapabilities"
                }
            )

