import json
from .resources import make_client
from unittest import TestCase
from flask_nemo.plugins.annotations_api import AnnotationsApiPlugin
from flask_nemo.query.proto import QueryPrototype
from flask_nemo.query.annotation import AnnotationResource
from flask import Response


class MockQueryInterface(QueryPrototype):
    ANNOTATION = AnnotationResource(
        "uri", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1", "http://foo.bar/treebank",
        resolver=None,  # Overwriting this one for the purpose of the test
        mimetype="application/xml", slug="treebank"
    )

    def getAnnotations(self,
            *urns,
            wildcard=".", include=None, exclude=None,
            limit=None, start=1,
            expand=False, **kwargs
        ):
        return 1, [
            type(self).ANNOTATION
        ]

    def getResource(self, sha):
        annotation = type(self).ANNOTATION
        if sha == "abc":
            annotation.read = lambda: Response("a", headers={"Content-Type": "text/plain"})
            annotation.read = lambda: Response("a", headers={"Content-Type": "text/plain"})
        else:
            annotation.__mimetype__ = "application/xml"
            annotation.read = lambda: "123"
        return annotation


class RetrieverMock(object):
    @staticmethod
    def match(uri):
        return True

    @staticmethod
    def read(uri):
        return "{} has been read".format(uri), "mimetype"


class AnnotationsApiPluginDummyInterfaceTest(TestCase):
    """ Test Suite for Annotations Api Plugin with a mock of query interface
    """

    def setUp(self):
        self.ann_plugin = AnnotationsApiPlugin(name="testplugin", queryinterface=MockQueryInterface(lambda x: x))
        self.client = make_client(self.ann_plugin)

    def test_route_by_target(self):
        """ Check error response for improper urn
        """
        response = self.client.get("/api/annotations/target/urn:cts:latinLit:phi1294.phi002.perseus-lat2:1")
        data = json.loads(response.data.decode("utf-8"))
        self.assertEqual(
            data,
            {
                "annotations": [
                    {
                        'slug': 'treebank',
                        'target': 'urn:cts:latinLit:phi1294.phi002.perseus-lat2:1',
                        'type': 'http://foo.bar/treebank',
                        'uri': 'uri',
                        'url': '/api/annotations/resource/922fffd1bd6fdaa95b4545df7a78754f6d67c2272b2900aa3ccd5e9da3dbb179'
                    }
                ],
                'count': 1
            },
            "Response of the api should work with default annotation"
        )
        self.assertEqual(200, response.status_code, "HTTP Code for valid request is 200")

    def test_route_get_content_response(self):
        """ Check error response for improper urn
        """
        response = self.client.get("/api/annotations/resource/abc")
        data = response.data.decode("utf-8")
        self.assertEqual(
            data,
            "a",
            "Content of the response should be forwarded"
        )
        self.assertEqual("text/plain", response.headers["Content-Type"], "Response mimetype should be forwarded")

    def test_route_get_content_normal(self):
        """ Check error response for improper urn
        """
        response = self.client.get("/api/annotations/resource/def")
        self.assertEqual(
            response.data,
            b"123",
            "Content of the response should be forwarded"
        )
        self.assertEqual("application/xml", response.headers["Content-Type"], "Read() mimetype should be forwarded")


class AnnotationsApiPluginTest(TestCase):
    """ Test Suite for Annotations Api Plugin in empty case
    """

    def setUp(self):
        self.ann_plugin = AnnotationsApiPlugin(name="testplugin", queryinterface=QueryPrototype(lambda x: x))
        self.client = make_client(self.ann_plugin)

    def test_route_by_target_valid_urn(self):
        """ Check empty response for valid urn target (given prototype query interface which knows nothing)
        """
        response = self.client.get("/api/annotations/target/urn:cts:greekLit:tlg0012.tlg001.grc1")
        self.assertEqual({"annotations": [], "count": 0}, json.loads(response.get_data().decode("utf-8")))
        self.assertEqual(200, response.status_code)

    def test_route_by_target_invalid_urn(self):
        """ Check error response for improper urn
        """
        response = self.client.get("/api/annotations/target/foo")
        self.assertEqual(b"invalid urn", str(response.data))
        self.assertEqual(400, response.status_code)

    def test_route_get(self):
        """ Check not found response for valid urn target (given prototype query interface which knows nothing)
        """
        response = self.client.get("/api/annotations/resource/foo")
        self.assertEqual("b'invalid resource uri'", str(response.data))
        self.assertEqual(404, response.status_code)


class AnnotationsApiPluginTest(TestCase):
    """ Test Suite for Annotations Api Plugin in empty case
    """

    def setUp(self):
        self.ann_plugin = AnnotationsApiPlugin(name="testplugin", queryinterface=QueryPrototype(lambda x: x))
        self.client = make_client(self.ann_plugin)

    def test_route_by_target_valid_urn(self):
        """ Check empty response for valid urn target (given prototype query interface which knows nothing)
        """
        response = self.client.get("/api/annotations/target/urn:cts:greekLit:tlg0012.tlg001.grc1")
        self.assertEqual({"annotations": [], "count": 0}, json.loads(response.get_data().decode("utf-8")))
        self.assertEqual(200, response.status_code)

    def test_route_by_target_invalid_urn(self):
        """ Check error response for improper urn
        """
        response = self.client.get("/api/annotations/target/foo")
        self.assertEqual("b'invalid urn'", str(response.data))
        self.assertEqual(400, response.status_code)

    def test_route_get(self):
        """ Check not found response for valid urn target (given prototype query interface which knows nothing)
        """
        response = self.client.get("/api/annotations/resource/foo")
        self.assertEqual("b'invalid resource uri'", str(response.data))
        self.assertEqual(404, response.status_code)


