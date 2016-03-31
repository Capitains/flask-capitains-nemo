"""

Test only controllers functions, ie function that should not be accessible directly from http routes but are still
greatly tied to the app/blueprint instance

"""
from flask.ext.nemo import Nemo
from mock import patch, call, Mock
import MyCapytain
from lxml import etree
from flask import Markup, Flask

from .resources import NemoResource

class NemoTestControllers(NemoResource):

    def test_flask_nemo(self):
        """ Testing Flask Nemo is set up"""
        a = Nemo()
        self.assertIsInstance(a, Nemo)
        a = Nemo()

    def test_without_inventory_request(self):
        """ Check that endpoint are derived from nemo.api_endpoint setting
        """
        #  Test without inventory
        with patch('requests.get', return_value=self.getCapabilities) as patched_get:
            self.nemo.get_inventory()
            patched_get.assert_called_once_with(
                NemoTestControllers.endpoint, params={
                    "request": "GetCapabilities"
                }
            )

    def test_with_inventory_request(self):
        """ Check that endpoint are derived from nemo.api_endpoint setting
        """
        with patch('requests.get', return_value=self.getCapabilities) as patched_get:
            #  Test with inventory
            self.nemo.api_inventory = "annotsrc"
            self.nemo.get_inventory()
            patched_get.assert_called_once_with(
                NemoTestControllers.endpoint, params={
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
                NemoTestControllers.endpoint, params={
                    "request": "GetCapabilities"
                }
            )
            self.assertIs(len(inventory.textgroups), 4)

    def test_get_collection(self):
        with patch('requests.get', return_value=self.getCapabilities) as patched_get:
            collections = self.nemo.get_collections()
            patched_get.assert_called_once_with(
                NemoTestControllers.endpoint, params={
                    "request": "GetCapabilities"
                }
            )
            self.assertEqual(collections, {"latinLit", "greekLit"})

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

    def test_get_texts_with_none_filtered(self):
        """ Check that texts are filtered
        """
        with patch('requests.get', return_value=self.getCapabilities):
            texts = self.nemo.get_texts()  # With nice filtering
            self.assertIs(len(texts), 14)
            self.assertEqual("urn:cts:greekLit:tlg0003.tlg001.perseus-grc2" in [str(text.urn) for text in texts], True)
            self.assertEqual("urn:cts:latinLit:phi1294.phi002.perseus-lat2" in [str(text.urn) for text in texts], True)
            self.assertEqual("urn:cts:latinLit:phi1294.phi002.perseus-lat3" in [str(text.urn) for text in texts], False)

    def test_get_texts_with_work_not_filtered(self):
        """ Check that all textgroups texts are returned
        """
        with patch('requests.get', return_value=self.getCapabilities):
            texts = self.nemo.get_texts("latinLit", "phi0959")  # With nice filtering
            self.assertIs(len(texts), 10)
            self.assertEqual("urn:cts:greekLit:tlg0003.tlg001.perseus-grc2" in [str(text.urn) for text in texts], False)
            self.assertEqual("urn:cts:latinLit:phi0959.tlg001.perseus-lat2" in [str(text.urn) for text in texts], False)

    def test_get_texts_raise(self):
        with self.assertRaises(
                ValueError):
            self.nemo.get_texts("latinLit")

    def test_get_single_text(self):
        """ Check that texts are filtered
        """
        with patch('requests.get', return_value=self.getCapabilities):
            texts = self.nemo.get_text("greekLIT", "TLG0003", "tlg001", "perseus-grc2")  # With nice filtering
            self.assertIsInstance(texts, MyCapytain.resources.inventory.Text)
            self.assertEqual(str(texts.urn), "urn:cts:greekLit:tlg0003.tlg001.perseus-grc2")

    def test_get_single_text_empty_because_no_work(self):
        """ Check that texts are filtered
        """
        with patch('requests.get', return_value=self.getCapabilities):
            with patch('flask_nemo.abort') as abort:
                texts = self.nemo.get_text("latinLit", "phi0959", "phi011", "perseus-lat2")   # With nice filtering
                abort.assert_called_once_with(404)

    def test_get_single_text_abort(self):
        """ Check that texts are filtered
        """
        with patch('requests.get', return_value=self.getCapabilities):
            with patch('flask_nemo.abort') as abort:
                texts = self.nemo.get_text("greekLIT", "TLG0003", "tlg001", "perseus-grc132")  # With nice filtering
                abort.assert_called_once_with(404)

    def test_get_validreffs_without_specific_callback(self):
        """ Try to get valid reffs
        """
        self.nemo = Nemo(api_url=NemoTestControllers.endpoint, inventory="annotsrc")
        with patch('requests.get', return_value=self.getValidReff) as patched:
            text, callback = self.nemo.get_reffs("latinLit", "phi1294", "phi002", "perseus-lat2")
            self.assertIsInstance(text, MyCapytain.resources.inventory.Text)

            reffs = callback(level=3)
            self.assertIsInstance(reffs, list)
            self.assertEqual(reffs[0], "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.1")
            self.assertEqual(patched.mock_calls, [
                call(
                    NemoTestControllers.endpoint,
                    params={
                        "inv": "annotsrc",
                        "request": "GetCapabilities"
                    }
                ),
                call(
                    NemoTestControllers.endpoint,
                    params={
                        "inv": "annotsrc",
                        "request": "GetValidReff",
                        "level": "3",
                        "urn": "urn:cts:latinLit:phi1294.phi002.perseus-lat2"
                    }
                )
                ]
            )

    def test_get_passage(self):
        self.nemo = Nemo(api_url=NemoTestControllers.endpoint, inventory="annotsrc")
        with patch('requests.get', return_value=self.getPassage) as patched:
            passage = self.nemo.get_passage("latinLit", "phi1294", "phi002", "perseus-lat2", "1.pr")
            self.assertIsInstance(passage, MyCapytain.resources.texts.api.Passage)
            self.assertEqual(len(passage.xml.xpath("//tei:l[@n]", namespaces={"tei":"http://www.tei-c.org/ns/1.0"})), 6)
