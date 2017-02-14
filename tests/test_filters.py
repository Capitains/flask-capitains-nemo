"""

Test file for filters.

"""

from unittest import TestCase
from flask import Flask
from flask_nemo import Nemo
from flask_nemo.filters import f_formatting_passage_reference, f_annotation_filter,\
    f_hierarchical_passages, f_i18n_citation_type, f_i18n_iso, f_is_str, f_order_resource_by_lang
from MyCapytain.common.reference import Citation
from tests.test_resources import NemoResource


class TestFilters(NemoResource, TestCase):

    def test_f_formatting_passage_reference(self):
        """ Test split of passage range identifier
        """
        self.assertEqual(f_formatting_passage_reference("1.1-1.2"), "1.1")
        self.assertEqual(f_formatting_passage_reference("1.1"), "1.1")

    def test_f_i18n_iso(self):
        """ Test split of passage range identifier
        """
        self.assertEqual(f_i18n_iso("eng"), "English")
        self.assertEqual(f_i18n_iso("eng", "fre"), "anglais")
        self.assertEqual(f_i18n_iso("eng", "ger"), "English")

    def test_register_filter(self):
        app = Flask(__name__)
        self.nemo = Nemo(app=app)
        self.nemo.register_filters()
        self.assertEqual(self.nemo.app.jinja_env.filters["formatting_passage_reference"], f_formatting_passage_reference)
        self.assertEqual(self.nemo.app.jinja_env.filters["order_resource_by_lang"], f_order_resource_by_lang)
        self.assertEqual(self.nemo.app.jinja_env.filters["hierarchical_passages"], f_hierarchical_passages)

    def test_f_hierarchical_passages(self):
        """Test for normal, simple passage hierarchical conversion
        :return:
        """
        reffs = [("1.5.8", "Line 8"), ("1.5.9", "Line 9"), ("1.6.8", "Line 7"), ("2.5.8", "Line 12")]
        citation_line = Citation(name="line")
        citation_poem = Citation(name="poem", child=citation_line)
        citation_book = Citation(name="book", child=citation_poem)
        converted = f_hierarchical_passages(reffs, citation_book)
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
        citation_line = Citation(name="line")
        citation_poem = Citation(name="poem", child=citation_line)
        citation_book = Citation(name="book", child=citation_poem)
        converted = f_hierarchical_passages(reffs, citation_book)
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
        self.assertEqual(f_is_str("h"), True)
        self.assertEqual(f_is_str([]), False)

    def test_f_i18n_citation_type(self):
        self.assertEqual(f_i18n_citation_type("%book|1%"), "Book 1")

    def test_annotation_filter(self):
        class Annotation(object):
            def __init__(self, type_uri):
                self.type_uri = type_uri

        a = Annotation("1")
        b = Annotation("2")
        c = Annotation("3")
        d = Annotation("2")

        self.assertEqual(
            f_annotation_filter([a, b, c, d], "1", 1), a,
            "We should get only one of type 1"
        )

        self.assertEqual(
            f_annotation_filter([a, b, c, d], "4", 1), None,
            "We should get nothing"
        )

        self.assertEqual(
            f_annotation_filter([a, b, c, d], "2", 2), d,
            "We should get the second item"
        )