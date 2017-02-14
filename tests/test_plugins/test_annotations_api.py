import json
from tests.test_plugin.test_resources import make_client
from unittest import TestCase
from flask_nemo.plugins.annotations_api import AnnotationsApiPlugin
from flask_nemo.query.proto import QueryPrototype
from flask_nemo.query.annotation import AnnotationResource
from flask import Response


class MockQueryInterface(QueryPrototype):
    ANNOTATION = AnnotationResource(
        "uri", ("urn:cts:latinLit:phi1294.phi002.perseus-lat2", "1"), "http://foo.bar/treebank",
        resolver=None,  # Overwriting this one for the purpose of the test
        mimetype="application/xml", slug="treebank"
    )
    ANNOTATION2 = AnnotationResource(
        "uri2", ("urn:cts:latinLit:phi1294.phi002.perseus-lat2", "2"), "http://foo.bar/treebank",
        resolver=None,  # Overwriting this one for the purpose of the test
        mimetype="application/json", slug="treebank"
    )

    def getAnnotations(self, targets, wildcard=".", include=None, exclude=None, limit=None, start=1, expand=False,
                       **kwargs):
        if targets == None:
            return 2, [
                type(self).ANNOTATION,
                type(self).ANNOTATION2
            ]
        else:
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
        self.maxDiff = 50000

    def test_route_by_target(self):
        """ Check error response for improper urn
        """
        response = self.client.get("/api/annotations?target=urn:cts:latinLit:phi1294.phi002.perseus-lat2:1")
        data = json.loads(response.data.decode("utf-8"))
        self.assertEqual(
            data,
            {
              "@context": {
                "": "http://www.w3.org/ns/anno.jsonld",
                "dc": "http://purl.org/dc/terms/",
                "owl": "http://www.w3.org/2002/07/owl#",
                'nemo': 'https://capitains.github.io/flask-capitains-nemo/ontology/#'
              },
              "id": "/api/annotations?start=1",
              "startIndex": 1,
              "total": 1,
              "type": "AnnotationCollection",
              "items": [
                {
                  "body": "/api/annotations/922fffd1bd6fdaa95b4545df7a78754f6d67c2272b2900aa3ccd5e9da3dbb179/body",
                  "id": "/api/annotations/922fffd1bd6fdaa95b4545df7a78754f6d67c2272b2900aa3ccd5e9da3dbb179",
                  "target": {
                    "source": "urn:cts:latinLit:phi1294.phi002.perseus-lat2",
                    "selector": {
                        "type": "FragmentSelector",
                        "conformsTo": "http://ontology-dts.org/terms/subreference",
                        "value": "1"
                    }
                  },
                  "type": "Annotation",
                  "dc:type": "http://foo.bar/treebank",
                  "nemo:slug": "treebank",
                  "owl:sameAs": [
                    "uri"
                  ]
                }
              ]
            },
            "Response of the api should work with default annotation"
        )
        self.assertEqual(200, response.status_code, "HTTP Code for valid request is 200")

    def test_all_annotation(self):
        """ Check error response for improper urn
        """
        response = self.client.get("/api/annotations")
        data = json.loads(response.data.decode("utf-8"))
        self.assertEqual(
            data,
            {
              "@context": {
                "": "http://www.w3.org/ns/anno.jsonld",
                "dc": "http://purl.org/dc/terms/",
                "owl": "http://www.w3.org/2002/07/owl#",
                'nemo': 'https://capitains.github.io/flask-capitains-nemo/ontology/#'
              },
              "id": "/api/annotations?start=1",
              "startIndex": 1,
              "total": 2,
              "type": "AnnotationCollection",
              "items": [
                {
                  "body": "/api/annotations/922fffd1bd6fdaa95b4545df7a78754f6d67c2272b2900aa3ccd5e9da3dbb179/body",
                  "id": "/api/annotations/922fffd1bd6fdaa95b4545df7a78754f6d67c2272b2900aa3ccd5e9da3dbb179",
                  "target": {
                    "source": "urn:cts:latinLit:phi1294.phi002.perseus-lat2",
                    "selector": {
                        "type": "FragmentSelector",
                        "conformsTo": "http://ontology-dts.org/terms/subreference",
                        "value": "1"
                    }
                  },
                  "type": "Annotation",
                  "dc:type": "http://foo.bar/treebank",
                  "nemo:slug": "treebank",
                  "owl:sameAs": [
                    "uri"
                  ]
                },
                {
                  "body": "/api/annotations/15c0c44af733054c9df420d046b871ef2263df0f1181b663bd7ba04c05032509/body",
                  "id": "/api/annotations/15c0c44af733054c9df420d046b871ef2263df0f1181b663bd7ba04c05032509",
                  "target": {
                    "source": "urn:cts:latinLit:phi1294.phi002.perseus-lat2",
                    "selector": {
                        "type": "FragmentSelector",
                        "conformsTo": "http://ontology-dts.org/terms/subreference",
                        "value": "2"
                    }
                  },
                  "type": "Annotation",
                  "dc:type": "http://foo.bar/treebank",
                  "nemo:slug": "treebank",
                  "owl:sameAs": [
                    "uri2"
                  ]
                }
              ]
            },
            "Response of the api should work with default annotation"
        )
        self.assertEqual(200, response.status_code, "HTTP Code for valid request is 200")

    def test_route_get_content_response(self):
        """ Check error response for improper urn
        """
        response = self.client.get("/api/annotations/abc/body")
        data = response.data.decode("utf-8")
        self.assertEqual(
            data,
            "a",
            "Content of the response should be forwarded"
        )
        self.assertEqual("text/plain", response.headers["Content-Type"], "Response mimetype should be forwarded")

    def test_route_get_content(self):
        """ Check error response for improper urn
        """
        response = self.client.get("/api/annotations/abc")
        data = response.data.decode("utf-8")
        self.assertEqual(
            json.loads(data),
            {
                "@context": {
                    "": "http://www.w3.org/ns/anno.jsonld",
                    "dc": "http://purl.org/dc/terms/",
                    "owl": "http://www.w3.org/2002/07/owl#",
                    'nemo': 'https://capitains.github.io/flask-capitains-nemo/ontology/#'
                },
                "body": "/api/annotations/922fffd1bd6fdaa95b4545df7a78754f6d67c2272b2900aa3ccd5e9da3dbb179/body",
                "id": "/api/annotations/922fffd1bd6fdaa95b4545df7a78754f6d67c2272b2900aa3ccd5e9da3dbb179",
                "target": {
                    "source": "urn:cts:latinLit:phi1294.phi002.perseus-lat2",
                    "selector": {
                        "type": "FragmentSelector",
                        "conformsTo": "http://ontology-dts.org/terms/subreference",
                        "value": "1"
                    }
                },
                "type": "Annotation",
                "dc:type": "http://foo.bar/treebank",
                "nemo:slug": "treebank",
                "owl:sameAs": [
                    "uri"
                ]
            },
            "Annotation route should return "
        )
        self.assertEqual("application/json", response.headers["Content-Type"], "Response should be json")

    def test_route_get_content_normal(self):
        """ Check error response for improper urn
        """
        response = self.client.get("/api/annotations/def/body")
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
        response = self.client.get("/api/annotations?target=urn:cts:greekLit:tlg0012.tlg001.grc1")
        self.assertEqual({"annotations": [], "count": 0}, json.loads(response.get_data().decode("utf-8")))
        self.assertEqual(200, response.status_code)

    def test_route_by_target_invalid_urn(self):
        """ Check error response for improper urn
        """
        response = self.client.get("/api/annotations?target=foo")
        self.assertEqual(b"invalid urn", str(response.data))
        self.assertEqual(400, response.status_code)

    def test_route_get(self):
        """ Check not found response for valid urn target (given prototype query interface which knows nothing)
        """
        response = self.client.get("/api/annotations/foo")
        self.assertEqual("b'invalid resource uri'", str(response.data))
        self.assertEqual(404, response.status_code)

    def test_route_get_body(self):
        """ Check not found response for valid urn target (given prototype query interface which knows nothing)
        """
        response = self.client.get("/api/annotations/foo/body")
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
        response = self.client.get("/api/annotations?target=urn:cts:greekLit:tlg0012.tlg001.grc1")
        self.maxDiff = 20000
        self.assertEqual(
            json.loads(response.get_data().decode("utf-8")),
            {
                '@context': {
                    '': 'http://www.w3.org/ns/anno.jsonld',
                    'dc': 'http://purl.org/dc/terms/',
                    'owl': 'http://www.w3.org/2002/07/owl#',
                    'nemo': 'https://capitains.github.io/flask-capitains-nemo/ontology/#'
                },
                'id': '/api/annotations?start=1',
                'items': [],
                'startIndex': 1,
                'total': 0,
                'type': 'AnnotationCollection'
             }
        )
        self.assertEqual(200, response.status_code)

    def test_route_by_target_invalid_urn(self):
        """ Check error response for improper urn
        """
        response = self.client.get("/api/annotations?target=foo")
        self.assertEqual("b'invalid urn'", str(response.data))
        self.assertEqual(400, response.status_code)

    def test_route_get(self):
        """ Check not found response for valid urn target (given prototype query interface which knows nothing)
        """
        response = self.client.get("/api/annotations/foo")
        self.assertEqual("b'invalid resource uri'", str(response.data))
        self.assertEqual(404, response.status_code)

    def test_route_get_body(self):
        """ Check not found response for valid urn target (given prototype query interface which knows nothing)
        """
        response = self.client.get("/api/annotations/foo/body")
        self.assertEqual("b'invalid resource uri'", str(response.data))
        self.assertEqual(404, response.status_code)

