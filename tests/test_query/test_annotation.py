from unittest import TestCase
from flask_nemo.query.annotation import AnnotationResource, Target
from MyCapytain.common.reference import URN
from flask_nemo.query.resolve import Resolver
import json


class RetrieverMock(object):
    @staticmethod
    def match(uri):
        return True

    @staticmethod
    def read(uri):
        return "{} has been read".format(uri), "mimetype"


class WTarget(Target):
    def __init__(self, param_dict):
        super(WTarget, self).__init__(objectId=param_dict["urn"])


class TestTarget(TestCase):
    """ Test method / values specific to the basic Target implementation
    """

    def setUp(self):
        self.alias = Target
        self.target_1 = "urn:cts:latinLit:phi1294.phi002.perseus-lat2"
        self.target_1_export = {"source":"urn:cts:latinLit:phi1294.phi002.perseus-lat2"}
        self.target_2 = URN("urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.1.1")
        self.target_2_export = {
            "source": "urn:cts:latinLit:phi1294.phi002.perseus-lat2",
            "selector": {
                "type": "FragmentSelector",
                "conformsTo": "http://ontology-dts.org/terms/subreference",
                "value": "1.1.1"
            }
        }
        self.target_3 = "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.1.1"
        self.target_3_export = {
            "source": "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.1.1"
        }

    def test_init(self):
        """ Assert initation takes into account params
        """
        self.assertEqual(
            self.alias("urn:cts:latinLit:phi1294.phi002.perseus-lat2").objectId,
            "urn:cts:latinLit:phi1294.phi002.perseus-lat2",
            "String are taken as parameter"
        )
        self.assertEqual(
            self.alias(URN("urn:cts:latinLit:phi1294.phi002.perseus-lat2")).objectId,
            "urn:cts:latinLit:phi1294.phi002.perseus-lat2",
            "URN are taken as parameter"
        )

    def test_to_json(self):
        """ Assert json-serializable is produced by the given resource is produced
        """
        self.assertEqual(
            json.loads(json.dumps(self.alias(self.target_1).to_json())),
            self.target_1_export,
            "JSON of basic target is a plain string"
        )
        self.assertEqual(
            json.loads(json.dumps(self.alias(self.target_2).to_json())),
            self.target_2_export,
            "JSON of basic target is a plain string"
        )


class TestAnnotationResource(TestCase):
    def setUp(self):
        self.resolver = Resolver(
            RetrieverMock
        )

        self.params_1 = [
            "http://localhost",
            URN("urn:cts:latinLit:phi1294.phi002.perseus-lat2"),
            "http://foo.bar/treebank",
            self.resolver,
            Target,
            "application/xml",
            "treebank"
        ]
        self.params_2 = [
            "http://localhost1",
            {"urn": URN("urn:cts:latinLit:phi1294.phi002.perseus-lat2")},
            "http://foo.bar/treebank1",
            self.resolver,
            WTarget,
            "application/xml1",
            "treebank1"
        ]

    def test_init_and_properties(self):
        """ Ensure init values are taken into account
        """
        anno = AnnotationResource(
            *self.params_1
        )
        self.assertEqual(
            anno.mimetype, "application/xml",
            "Mimetype should be set with init params"
        )
        self.assertEqual(
            anno.slug, "treebank",
            "Slug should be set with init params"
        )
        self.assertEqual(
            anno.sha, "a076083ce9233ea6bb5263109d05d0780261c992c83c0a5787d79d9f62c71266",
            "Sha should be set with init params"
        )
        self.assertEqual(
            anno.type_uri, "http://foo.bar/treebank",
            "Type URI should be set with init params"
        )
        self.assertEqual(
            anno.uri, "http://localhost",
            "URI should be set with init params"
        )
        self.assertEqual(
            str(anno.target.objectId), "urn:cts:latinLit:phi1294.phi002.perseus-lat2",
            "Target should be set with init params"
        )
        self.assertIsInstance(
            anno.target, Target,
            "Target alias should be used"
        )
        self.assertEqual(
            anno.expandable, False,
            "Default annotation resource are not expandable"
        )

    def test_target_alias(self):
        """ Ensure alias class can be overwritten
        """
        anno = AnnotationResource(
            *self.params_2
        )
        self.assertIsInstance(
            anno.target, WTarget,
            "Target should be built through annotation alias class target_class param"
        )

    def test_target_expand(self):
        """ Ensure existing method and default behaviour
        """
        anno = AnnotationResource(
            *self.params_2
        )
        self.assertEqual(
            anno.expand(), [],
            "Default annotation should expand to an eempty list"
        )

    def test_read(self):
        """ Ensure existing method and default behaviour

        See the mocked resolver at the beginning of the file
        """
        anno = AnnotationResource(
            *self.params_2
        )
        self.assertEqual(
            anno.read(), anno.uri+" has been read",
            "Default annotation should expand to an empty list"
        )
        self.assertEqual(
            anno.mimetype, "mimetype",
            ".read() should update mimetype"
        )
