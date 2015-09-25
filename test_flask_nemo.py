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
        a = Nemo()

    def test_inventory_request(self):
        """ Check that endpoint are derived from nemo.api_endpoint setting
        """
        #  Test without inventory
        with patch('requests.get', return_value=self.getCapabilities) as patched_get:
            self.nemo.get_inventory()
            patched_get.assert_called_once_with(
                NemoTest.endpoint, params={
                    "request": "GetCapabilities"
                }
            )

        #  Test with inventory
        with patch('requests.get', return_value=self.getCapabilities) as patched_get:
            self.nemo.api_inventory = "annotsrc"
            self.nemo.get_inventory()
            patched_get.assert_called_once_with(
                NemoTest.endpoint, params={
                    "request": "GetCapabilities",
                    "inv": "annotsrc"
                }
            )
            self.nemo.api_inventory = None


    def test_inventory_parsing(self):
        """ Check that endpoint request leads to the creation of a TextInventory object
        """
        with patch('requests.get', return_value=self.getCapabilities) as patched_get:
            inventory = self.nemo.get_inventory()
            patched_get.assert_called_once_with(
                NemoTest.endpoint, params={
                    "request": "GetCapabilities"
                }
            )
            self.assertIs(len(inventory.textgroups), 4)

    def test_get_authors(self):
        """ Check that authors textgroups are returned with informations
        """
        with patch('requests.get', return_value=self.getCapabilities):
            tgs = self.nemo.get_textgroups()
            self.assertIs(len(tgs), 4)
            self.assertEqual("urn:cts:greekLit:tlg0003" in [str(tg.urn) for tg in tgs], True)

    def test_get_authors_with_collection(self):
        """ Check that authors textgroups are returned when filtered by collection
        """
        with patch('requests.get', return_value=self.getCapabilities):
            tgs_2 = self.nemo.get_textgroups("greekLIT")  # With nice filtering
            self.assertIs(len(tgs_2), 1)
            self.assertEqual("urn:cts:greekLit:tlg0003" in [str(tg.urn) for tg in tgs_2], True)

    def test_get_works_with_collection(self):
        """ Check that works are returned when filtered by collection and textgroup
        """
        with patch('requests.get', return_value=self.getCapabilities):
            works = self.nemo.get_works("greekLIT", "TLG0003")  # With nice filtering
            self.assertIs(len(works), 1)
            self.assertEqual("urn:cts:greekLit:tlg0003.tlg001" in [str(work.urn) for work in works], True)

            #  Check when it fails
            works = self.nemo.get_works("greekLIT", "TLGabc003")  # With nice filtering
            self.assertIs(len(works), 0)

    def test_get_works_without_filters(self):
        """ Check that all works are returned when not filtered
        """
        with patch('requests.get', return_value=self.getCapabilities):
            #  Check when it fails
            works = self.nemo.get_works()  # With nice filtering
            self.assertIs(len(works), 13)

    def test_get_works_with_one_filter(self):
        """ Check that error are raises
        """
        with self.assertRaises(ValueError):
            works = self.nemo.get_works("a", None)  # With nice filtering

        with self.assertRaises(ValueError):
            works = self.nemo.get_works(None, "a")

    def test_get_texts_with_all_filtered(self):
        """ Check that texts are filtered
        """
        with patch('requests.get', return_value=self.getCapabilities):
            texts = self.nemo.get_texts("greekLIT", "TLG0003", "tlg001")  # With nice filtering
            self.assertIs(len(texts), 1)
            self.assertEqual("urn:cts:greekLit:tlg0003.tlg001.perseus-grc2" in [str(text.urn) for text in texts], True)

            texts = self.nemo.get_texts("greekLIT", "TLG0003", "tlg002")  # With nice filtering
            self.assertIs(len(texts), 0)

    def test_get_texts_with_all_filtered(self):
        """ Check that texts are filtered
        """
        with patch('requests.get', return_value=self.getCapabilities):
            texts = self.nemo.get_texts()  # With nice filtering
            self.assertIs(len(texts), 15)
            self.assertEqual("urn:cts:greekLit:tlg0003.tlg001.perseus-grc2" in [str(text.urn) for text in texts], True)
            self.assertEqual("urn:cts:latinLit:phi1294.phi002.perseus-lat2" in [str(text.urn) for text in texts], True)
            self.assertEqual("urn:cts:latinLit:phi1294.phi002.perseus-lat3" in [str(text.urn) for text in texts], False)
