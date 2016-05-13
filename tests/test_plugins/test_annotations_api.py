from .resources import make_client
from unittest import TestCase
from flask_nemo.plugins.annotations_api import AnnotationsApiPlugin
from flask_nemo.query.proto import QueryPrototype


class AnnotationsApiPluginTest(TestCase):
    """ Test Suite for Annotations Api Plugin
    """

    def setUp(self):
        self.ann_plugin = AnnotationsApiPlugin(name="testplugin",queryinterface=QueryPrototype(lambda x:x))
        self.client = make_client(self.ann_plugin)


    def test_route_by_target_valid_urn(self):
        """ Check empty response for valid urn target (given prototype query interface which knows nothing)
        """
        response = self.client.get("/annotations/api/target/urn:cts:greekLit:tlg0012.tlg001.grc1")
        self.assertEqual("b'{\\n  \"annotations\": {},\\n  \"count\": 0\\n}'", str(response.data))
        self.assertEqual(200,response.status_code)

    def test_route_by_target_invalid_urn(self):
        """ Check error response for improper urn
        """
        response = self.client.get("/annotations/api/target/foo")
        self.assertEqual("b'invalid urn'", str(response.data))
        self.assertEqual(400,response.status_code)

    def test_route_get(self):
        """ Check not found response for valid urn target (given prototype query interface which knows nothing)
        """
        response = self.client.get("/annotations/api/resources/foo")
        self.assertEqual("b'invalid resource uri'", str(response.data))
        self.assertEqual(404,response.status_code)


