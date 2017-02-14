from flask_nemo.query.resolve import Resolver, CTSRetriever, HTTPRetriever, LocalRetriever, UnresolvableURIError
from tests.test_resources import NautilusDummy
from unittest import TestCase
from mock import patch


def mocked_response(content, mime):
    class MockResponse(object):
        def __init__(self, data, mime="text"):
            self.data = data
            self.mime = mime

        @property
        def text(self):
            return self.data

        @property
        def content(self):
            return self.data

        @property
        def headers(self):
            return {
                "Content-Type": self.mime
            }

    return MockResponse(content, mime)


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
                CTSRetriever(NautilusDummy).match(uri), matching,
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
        passage, mime = ret.read("urn:cts:latinLit:phi1294.phi002:1.pr.1")
        self.assertEqual(mime, "text/xml", "Mime type of CTS should be text/xml")
        self.assertIn(
            '<TEI xmlns="http://www.tei-c.org/ns/1.0">', passage,
            "TEI is visible as a tag"
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
                HTTPRetriever().match(uri), matching,
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
            ("http://foo.bar/com", "I am some content", "application/html")
        ]
        i = len(uris)
        for uri, content, mime in uris:
            i -= 1
            with patch("flask_nemo.query.resolve.request", return_value=mocked_response(content, mime)) as request:
                data, mimetype = ret.read(uri)
                request.assert_called_with("GET", uri)
                self.assertEqual(
                    data, content,
                    "Content should be read correctly"
                )
                self.assertEqual(mimetype, "application/html", "Mime is correctly read from headers")

        self.assertEqual(
            i, 0,
            "All tests should have been run"
        )


class TestLocalRetrievers(TestCase):
    """ Tests for the Local retriever
    """

    def test_matching(self):
        """ Test the Local retriever matching
        """
        localretriever = LocalRetriever(path="./tests/test_data")
        tests = [
            ("urn:cts:latinLit:phi1294:phi002.perseus-lat2", False, "URN should not match"),
            ("http://foo.com/bar", False, "URL should not match"),
            ("../test_data/empty.js", True, "File match and exists"),
            ("assets/fake.png", True, "File match and exists"),
            ("./something.html", False, "File is not in path"),
            ("../setup.py", False, "File out of path should not match"),
            ("something.html", False, "File does not exist")
        ]
        i = len(tests)
        for uri, matching, msg in tests:
            i -= 1

            self.assertEqual(
                localretriever.match(uri), matching,
                msg
            )

        self.assertEqual(
            i, 0,
            "All tests should have been run"
        )

    def test_retrieve_resource(self):
        """ Ensure LocalRetriever actually get resource
        """
        ret = LocalRetriever(path="./tests/test_data")
        uris = [
            ("../test_data/empty.js", "var empty = True;", "application/javascript", False),
            ("assets/fake.png", "fake", "image/png", True),
        ]
        i = len(uris)
        for uri, content, mime, sendfile in uris:
            i -= 1
            if sendfile:
                with patch("flask_nemo.query.resolve.send_file", return_value=content) as patched:
                    data, mimetype = ret.read(uri)
                    patched.assert_called_with(ret.__absolute__(uri))
            else:
                data, mimetype = ret.read(uri)

            self.assertIn(
                data, content,
                "Content of the file should be read"
            )

            self.assertEqual(
                mimetype, mime,
                "Mime should be correctly guessed"
            )

        self.assertEqual(
            i, 0,
            "All tests should have been run"
        )


class TestResolverWithRetriever(TestCase):
    """ Ensure retrievers stacks well
    """
    def setUp(self):
        self.resolver = Resolver(
            CTSRetriever(resolver=NautilusDummy),
            HTTPRetriever(),
            LocalRetriever(path="./tests/test_data")
        )

    def test_stack(self):
        uris = [
            ("urn:cts:latinLit:phi1294.phi002.perseus-lat2", "CTS Retriever should be resolved", CTSRetriever),
            ("http://foo.com/bar", "HTTP retriever should match the URI", HTTPRetriever),
            ("../test_data/empty.js", "Local Retriever should match complex URIs", LocalRetriever),
            ("assets/fake.png", "Local Retriever should match simple URIs", LocalRetriever)
        ]
        i = len(uris)
        for uri, msg, type_retriever in uris:
            self.assertEqual(
                type(self.resolver.resolve(uri)), type_retriever,
                msg
            )
            i -= 1
        self.assertEqual(i, 0, "All tests have been run")

    def test_stack_fails(self):
        """ Ensure that it still raises for unaccepted
        """
        with self.assertRaises(UnresolvableURIError, msg="Not safe file should fail"):
            self.resolver.resolve("../setup.py")
