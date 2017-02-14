"""

Test only controllers functions, ie function that should not be accessible directly from http routes but are still
greatly tied to the app/blueprint instance

"""
from flask.ext.nemo import Nemo
from mock import patch, call, Mock
from lxml import etree
from flask import Markup, Flask

from MyCapytain.resources.prototypes.text import Passage
from MyCapytain.common.constants import Mimetypes
from MyCapytain.resources.prototypes.cts.inventory import PrototypeTextInventory, PrototypeText

from tests.test_resources import NemoResource
from flask_nemo.chunker import level_grouper
from tests.test_resources import NautilusDummy


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
                NemoTestControllers.endpoint.endpoint.endpoint, params={
                    "request": "GetCapabilities"
                }
            )

    def test_inventory_parsing(self):
        """ Check that endpoint request leads to the creation of a TextInventory object
        """
        with patch('requests.get', return_value=self.getCapabilities) as patched_get:
            inventory = self.nemo.get_inventory()
            patched_get.assert_called_once_with(
                NemoTestControllers.endpoint.endpoint.endpoint, params={
                    "request": "GetCapabilities"
                }
            )
            self.assertIs(len(inventory.textgroups), 4)

    def test_get_authors(self):
        """ Check that authors textgroups are returned with informations
        """
        with patch('requests.get', return_value=self.getCapabilities):
            tgs = self.nemo.get_inventory()
            self.assertIs(len(tgs.members), 4)
            self.assertEqual("urn:cts:greekLit:tlg0003" in [str(tg.id) for tg in tgs.members], True)

    def test_get_works_with_collection(self):
        """ Check that works are returned when filtered by collection and textgroup
        """
        with patch('requests.get', return_value=self.getCapabilities):
            works = self.nemo.get_collection("urn:cts:greekLit:tlg0003")
            self.assertIs(len(works), 1)
            self.assertIn(
                "urn:cts:greekLit:tlg0003.tlg001",
                [str(w.id) for w in works.descendants]
            )

            #  Check when it fails
            with self.assertRaises(KeyError):
                works = self.nemo.get_collection("urn:cts:greekLit:tlg000b3")

    def test_get_texts_with_all_filtered(self):
        """ Check that texts are filtered
        """
        with patch('requests.get', return_value=self.getCapabilities):
            texts = self.nemo.get_collection("urn:cts:greekLit:tlg0003.tlg001")
            self.assertIs(len(texts), 1)
            self.assertIn(
                "urn:cts:greekLit:tlg0003.tlg001.perseus-grc2",
                [str(text.id) for text in texts.descendants]
            )

            with self.assertRaises(KeyError):
                texts = self.nemo.get_collection("urn:cts:greekLit:tlg0003.tlg002")
                self.assertIs(len(texts), 0)

    def test_get_texts_with_work_not_filtered(self):
        """ Check that all textgroups texts are returned
        """
        with patch('requests.get', return_value=self.getCapabilities):
            texts = self.nemo.get_collection("urn:cts:latinLit:phi0959").readableDescendants
            self.assertIs(len(texts), 10)
            self.assertNotIn(
                "urn:cts:greekLit:tlg0003.tlg001.perseus-grc2",
                [str(text.id) for text in texts]
            )
            self.assertNotIn(
                "urn:cts:latinLit:phi0959.tlg001.perseus-lat2",
                [str(text.id) for text in texts]
            )

    def test_get_texts_raise(self):
        with patch('requests.get', return_value=self.getCapabilities):
            with self.assertRaises(KeyError):
                self.nemo.get_collection("latinLit")

    def test_get_single_text(self):
        """ Check that texts are filtered
        """
        with patch('requests.get', return_value=self.getCapabilities):
            texts = self.nemo.get_collection("urn:cts:greekLit:tlg0003.tlg001.perseus-grc2")
            self.assertIsInstance(texts, PrototypeText)
            self.assertEqual(str(texts.id), "urn:cts:greekLit:tlg0003.tlg001.perseus-grc2")

    def test_get_single_text_empty_because_no_work(self):
        """ Check that texts are filtered
        """
        with patch('requests.get', return_value=self.getCapabilities):
            with self.assertRaises(KeyError):
                texts = self.nemo.get_collection("urn:cts:latinLit:phi0959.phi011.perseus-lat2")

    def test_get_single_text_abort(self):
        """ Check that texts are filtered
        """
        with patch('requests.get', return_value=self.getCapabilities):
            with self.assertRaises(KeyError):
                texts = self.nemo.get_collection("urn:cts:greekLIT:TLG0003:tlg001:perseus-grc132")

    def test_get_validreffs_without_specific_callback(self):
        """ Try to get valid reffs
        """
        with patch('requests.get', return_value=self.getValidReff) as patched:
            text, reffs = self.nemo.get_reffs(
                "urn:cts:latinLit:phi1294.phi002.perseus-lat2",
                export_collection=True
            )
            self.assertIsInstance(text, PrototypeText)
            self.assertIsInstance(reffs, list)
            self.assertEqual(reffs[0], ("1.pr.1-1.pr.20", "1.pr.1-1.pr.20"))
            self.assertEqual(patched.mock_calls, [
                call(
                    NemoTestControllers.endpoint.endpoint.endpoint,
                    params={
                        "request": "GetCapabilities"
                    }
                ),
                call(
                    NemoTestControllers.endpoint.endpoint.endpoint,
                    params={
                        "request": "GetValidReff",
                        "level": "3",
                        "urn": "urn:cts:latinLit:phi1294.phi002.perseus-lat2"
                    }
                )
                ]
            )

    def test_get_passage(self):
        with patch('requests.get', return_value=self.getPassagePlus) as patched:
            passage = self.nemo.get_passage(
                "urn:cts:latinLit:phi1294.phi002.perseus-lat2",
                "1.pr"
            )
            self.assertIsInstance(passage, Passage)
            self.assertEqual(
                len(passage.export(Mimetypes.PYTHON.ETREE)
                    .xpath("//tei:l[@n]", namespaces={"tei": "http://www.tei-c.org/ns/1.0"})),
                6,
                "There should be six lines"
            )

    def test_get_siblings(self):
        """ Test first passage
        """
        app = Flask("Nemo")
        nemo = Nemo(
            app=app,
            base_url="",
            resolver=NautilusDummy,
            original_breadcrumb=False,
            chunker={"default": lambda x, y: level_grouper(x, y, groupby=20)}
        )
        # First range
        p = nemo.get_passage("urn:cts:latinLit:phi1294.phi002.perseus-lat2", "1.pr.1-1.pr.20")
        l, r = nemo.get_siblings("urn:cts:latinLit:phi1294.phi002.perseus-lat2", "1.pr.1-1.pr.20", p)
        self.assertEqual(l, None, "There should be nothing on the left")
        self.assertEqual(r, "1.pr.21-1.pr.22", "Next passage should not be 20 long")
        # Second range
        p = nemo.get_passage("urn:cts:latinLit:phi1294.phi002.perseus-lat2", "1.pr.21-1.pr.22")
        l, r = nemo.get_siblings("urn:cts:latinLit:phi1294.phi002.perseus-lat2", "1.pr.21-1.pr.22", p)
        self.assertEqual(l, "1.pr.1-1.pr.20", "There should be something on the left")
        self.assertEqual(r, "1.1.1-1.1.6", "Next passage should not be 20 long")
        # Last range
        p = nemo.get_passage("urn:cts:latinLit:phi1294.phi002.perseus-lat2", "14.223.1-14.223.2")
        l, r = nemo.get_siblings("urn:cts:latinLit:phi1294.phi002.perseus-lat2", "14.223.1-14.223.2", p)
        self.assertEqual(l, "14.222.1-14.222.2", "Previous passage does not have to be 20 long")
        self.assertEqual(r, None, "There should be nothing on the right")
        # Passage with unknown range
        p = nemo.get_passage("urn:cts:latinLit:phi1294.phi002.perseus-lat2", "1.11.1-1.11.2")
        l, r = nemo.get_siblings("urn:cts:latinLit:phi1294.phi002.perseus-lat2", "1.11.1-1.11.2", p)
        self.assertEqual(l, "1.10.3-1.10.4", "Passage should be computed specifically if texts have unknown range")
        self.assertEqual(r, "1.11.3-1.11.4", "Passage should be computed specifically if texts have unknown range")
