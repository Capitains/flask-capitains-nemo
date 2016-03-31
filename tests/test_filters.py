"""

Test file for filters.

"""

from flask import Flask
from flask_nemo import Nemo
from mock import patch, call, Mock
import MyCapytain
from .resources import NemoResource, RequestPatch, RequestPatchChained, create_test_app


class TestFilters(NemoResource):

    def test_f_order_author(self):
        """ Test ordering authors
        """
        a = MyCapytain.resources.inventory.TextGroup()
        b = MyCapytain.resources.inventory.TextGroup()
        c = MyCapytain.resources.inventory.TextGroup()
        d = MyCapytain.resources.inventory.TextGroup()
        e = MyCapytain.resources.inventory.TextGroup()
        f = MyCapytain.resources.inventory.TextGroup(
            urn="urn:cts:latinLit:phi1294.phi002.perseus-lat2"
        )
        a.metadata["groupname"]["eng"] = "Martial"
        b.metadata["groupname"]["eng"] = "Virgil"
        c.metadata["groupname"]["eng"] = "Cicero"
        d.metadata["groupname"]["eng"] = "Augustine"
        e.metadata["groupname"]["eng"] = "Suetone"
        f.metadata["groupname"]["eng"] = None
        sort = Nemo.f_order_author([a, b, c, d, e, f])
        self.assertEqual(
            sort,
            [d, c, a, e, b, f]
        )

    def test_f_active_link(self):
        """ Test checking if something is in the path
        """
        wrong = Nemo.f_active_link("phi003", {"collection": "latinLit"})
        wrong2 = Nemo.f_active_link("phi003", {"collection": "latinLit", "textgroup": "phi0003"})
        right = Nemo.f_active_link("phi003", {"collection": "latinLit", "textgroup": "phi0003", "work": "phi003"})
        self.assertEqual(wrong, "")
        self.assertEqual(wrong2, "")
        self.assertEqual(right, "active")

    def test_f_collection_i18n(self):
        """ Test internationalization of collection identifier
        """
        self.assertEqual(Nemo.f_collection_i18n("latinLit"), "Latin")
        self.assertEqual(Nemo.f_collection_i18n("greekLit"), "Ancient Greek")
        self.assertEqual(Nemo.f_collection_i18n("freLit"), "freLit")

    def test_f_formatting_passage_reference(self):
        """ Test split of passage range identifier
        """
        self.assertEqual(Nemo.f_formatting_passage_reference("1.1-1.2"), "1.1")
        self.assertEqual(Nemo.f_formatting_passage_reference("1.1"), "1.1")

    def test_f_i18n_iso(self):
        """ Test split of passage range identifier
        """
        self.assertEqual(Nemo.f_i18n_iso("eng"), "English")
        self.assertEqual(Nemo.f_i18n_iso("eng", "fre"), "anglais")
        self.assertEqual(Nemo.f_i18n_iso("eng", "ger"), "English")

    def test_f_order_text_edition_translation(self):
        """ Check the reordering filter
        """
        Text = MyCapytain.resources.inventory.Text
        a, b, c, d = Text(subtype="Translation"), Text(subtype="Edition"), Text(subtype="Edition"), Text(subtype="Translation")
        self.assertEqual(Nemo.f_order_text_edition_translation([a,b,c,d]), [b, c, a, d])

    def test_register_filter(self):
        app = Flask(__name__)
        self.nemo = Nemo(app=app)
        self.nemo.register_filters()
        self.assertEqual(self.nemo.app.jinja_env.filters["formatting_passage_reference"], Nemo.f_formatting_passage_reference)
        self.assertEqual(self.nemo.app.jinja_env.filters["collection_i18n"], Nemo.f_collection_i18n)
        self.assertEqual(self.nemo.app.jinja_env.filters["active_link"], Nemo.f_active_link)

    def test_f_hierarchical_passages(self):
        """Test for normal, simple passage hierarchical conversion
        :return:
        """
        reffs = [("1.5.8", "Line 8"), ("1.5.9", "Line 9"), ("1.6.8", "Line 7"), ("2.5.8", "Line 12")]
        citation_line = MyCapytain.common.reference.Citation(name="line")
        citation_poem = MyCapytain.common.reference.Citation(name="poem", child=citation_line)
        citation_book = MyCapytain.common.reference.Citation(name="book", child=citation_poem)
        text = MyCapytain.resources.inventory.Text()
        text.citation = citation_book
        converted = Nemo.f_hierarchical_passages(reffs, text)
        self.assertEqual(converted["%book|1%"]["%poem|5%"]["Line 8"], "1.5.8")
        self.assertEqual(converted["%book|1%"]["%poem|5%"]["Line 9"], "1.5.9")
        self.assertEqual(converted["%book|1%"]["%poem|6%"]["Line 7"], "1.6.8")
        self.assertEqual(converted["%book|2%"]["%poem|5%"]["Line 12"], "2.5.8")
        self.assertEqual(len(converted), 2)
        self.assertEqual(len(converted["%book|1%"]), 2)
        self.assertEqual(len(converted["%book|1%"]["%poem|5%"]), 2)
        self.assertEqual(len(converted["%book|1%"]["%poem|6%"]), 1)
        self.assertEqual(len(converted["%book|2%"]), 1)

    def test_f_hierarchical_range_passages(self):
        """Test for range passage hierarchical conversion
        :return:
        """
        reffs = [("1.5.8-1.5.9", "Line 8"), ("1.5.9-1.5.15", "Line 9"), ("1.6.8-2.9.16", "Line 7"), ("2.5.8-16.45.928", "Line 12")]
        citation_line = MyCapytain.common.reference.Citation(name="line")
        citation_poem = MyCapytain.common.reference.Citation(name="poem", child=citation_line)
        citation_book = MyCapytain.common.reference.Citation(name="book", child=citation_poem)
        text = MyCapytain.resources.inventory.Text()
        text.citation = citation_book
        converted = Nemo.f_hierarchical_passages(reffs, text)
        self.assertEqual(converted["%book|1%"]["%poem|5%"]["Line 8"], "1.5.8-1.5.9")
        self.assertEqual(converted["%book|1%"]["%poem|5%"]["Line 9"], "1.5.9-1.5.15")
        self.assertEqual(converted["%book|1%"]["%poem|6%"]["Line 7"], "1.6.8-2.9.16")
        self.assertEqual(converted["%book|2%"]["%poem|5%"]["Line 12"], "2.5.8-16.45.928")
        self.assertEqual(len(converted), 2)
        self.assertEqual(len(converted["%book|1%"]), 2)
        self.assertEqual(len(converted["%book|1%"]["%poem|5%"]), 2)
        self.assertEqual(len(converted["%book|1%"]["%poem|6%"]), 1)
        self.assertEqual(len(converted["%book|2%"]), 1)

    def test_f_is_str(self):
        """ Test string
        """
        self.assertEqual(Nemo.f_is_str("h"), True)
        self.assertEqual(Nemo.f_is_str([]), False)

    def test_f_i18n_citation_type(self):
        self.assertEqual(Nemo.f_i18n_citation_type("%book|1%"), "Book 1")
