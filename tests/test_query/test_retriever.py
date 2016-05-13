from flask_nemo.query.resolve import Resolver, CTSRetriever, HTTPRetriever, LocalRetriever
from ..resources import NautilusDummy
from unittest import TestCase
from mock import patch


def mocked_response(content):
    class MockResponse(object):
        def __init__(self, data):
            self.data = data

        @property
        def text(self):
            return self.data

    return MockResponse(content)


class TestCTSRetrievers(TestCase):
    def test_matching(self):
        """ Test the CTS retriever matching
        """
        tests = [
            ("urn:cts:latinLit:phi1294:phi002.perseus-lat2", True),
            ("https://foo.com/bar", False)
        ]
        i = len(tests)
        for uri, matching in tests:
            i -= 1
            if matching:
                msg = "CTS URNs should match"
            else:
                msg = "URI which are not cts urn should not match"

            self.assertEqual(
                CTSRetriever.match(uri), matching,
                msg
            )

        self.assertEqual(
            i, 0,
            "All tests should have been run"
        )

    def test_retrieve_resource(self):
        """ Ensure CTSRetriever actually get resource
        """
        ret = CTSRetriever(NautilusDummy)
        passage = ret.read("urn:cts:latinLit:phi1294.phi002:1.pr.1")
        self.assertIn(
            "GetPassage", passage,
            "GetPassage is visible as a tag"
        )
        self.assertIn(
            "Spero me secutum in libellis meis tale temperamen", passage,
            "Text of the passage is retrieved"
        )


class TestHTTPRetrievers(TestCase):
    """ Tests for the HTTP retriever
    """

    def test_matching(self):
        """ Test the HTTP retriever matching
        """
        tests = [
            ("urn:cts:latinLit:phi1294:phi002.perseus-lat2", False),
            ("https://foo.com/bar", True)
        ]
        i = len(tests)
        for uri, matching in tests:
            i -= 1
            if matching:
                msg = "HTTP should match"
            else:
                msg = "URI which are not HTTP should not match"

            self.assertEqual(
                HTTPRetriever.match(uri), matching,
                msg
            )

        self.assertEqual(
            i, 0,
            "All tests should have been run"
        )

    def test_retrieve_resource(self):
        """ Ensure HTTPRetriever actually get resource
        """
        ret = HTTPRetriever()
        uris = [
            ("http://foo.bar/com", "I am some content")
        ]
        i = len(uris)
        for uri, content in uris:
            i -= 1
            with patch("flask_nemo.query.resolve.request", return_value=mocked_response(content)) as request:
                data = ret.read(uri)
                request.assertCalledWith(uri, "The URL should have been called")
                self.assertEqual(
                    data, content,
                    "Content should be read correctly"
                )

        self.assertEqual(
            i, 0,
            "All tests should have been run"
        )

