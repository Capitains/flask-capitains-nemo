from flask_nemo.query.interface import SimpleQuery
from flask_nemo.query.annotation import AnnotationResource
from flask_nemo.query.resolve import Resolver, LocalRetriever
from flask_nemo import Nemo
from unittest import TestCase
from flask import Flask
from MyCapytain.common.reference import URN
from MyCapytain.resolvers.cts.local import CtsCapitainsLocalResolver
from werkzeug.exceptions import NotFound
import logging


def dict_list(l):
    return [(a.uri, a.target.objectId, a.target.subreference, a.type_uri) for a in l]


class TestSimpleQuery(TestCase):
    """ Test simple query interface """
    def setUp(self):
        self.resolver = Resolver(LocalRetriever(path="./tests/test_data/"))
        self.one = (URN("urn:cts:latinLit:phi1294.phi002.perseus-lat2:6.1"), "interface/treebanks/treebank1.xml", "dc:treebank")
        self.two = (URN("urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.5"), "interface/treebanks/treebank2.xml", "dc:treebank")
        self.three = (URN("urn:cts:latinLit:phi1294.phi002.perseus-lat2:6.1"), "interface/images/N0060308_TIFF_145_145.tif", "dc:image")
        self.four = AnnotationResource(
            "interface/researchobject/researchobject.json",
            type_uri="dc:researchobject",
            target=URN("urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.1"),
            resolver=self.resolver
        )
        self.one_anno = AnnotationResource(
            self.one[1],
            type_uri=self.one[2],
            target=self.one[0],
            resolver=self.resolver
        )
        self.two_anno = AnnotationResource(
            self.two[1],
            type_uri=self.two[2],
            target=self.two[0],
            resolver=self.resolver
        )
        self.three_anno = AnnotationResource(
            self.three[1],
            type_uri=self.three[2],
            target=self.three[0],
            resolver=self.resolver
        )
        self.fourth_anno = AnnotationResource(
            self.three[1],
            type_uri=self.three[2],
            target=("urn:cts:latinLit:phi1294.phi002.perseus-lat2", "1-2"),
            resolver=self.resolver
        )
        self.app = Flask("app")
        logger = logging.getLogger('my-logger')
        logger.propagate = False
        self.nautilus = CtsCapitainsLocalResolver(["tests/test_data/interface/latinLit"], logger=logger)
        self.nemo = Nemo(app=self.app, resolver=self.nautilus, base_url="/")
        self.query = SimpleQuery(
            [
                self.one,
                self.two,
                self.three,
                self.four
            ],  # List of annotations
            self.resolver
        )
        self.query.process(self.nemo)

    def test_process(self):
        """ Check that all annotations are taken care of"""
        self.assertEqual(len(self.query.annotations), 4, "There should be 4 annotations")

    def test_get_all(self):
        """ Check that get all returns 3 annotations """
        hits, annotations = self.query.getAnnotations(None)
        self.assertEqual(hits, 4, "There should be 4 annotations")
        self.assertCountEqual(dict_list(annotations), dict_list(
            [
                self.one_anno,
                self.two_anno,
                self.three_anno,
                self.four
            ]), "There should be all three annotation")

    def test_get_exact_match(self):
        """ Ensure exact match works """
        # Higher level annotation or same match
        hits, annotations = self.query.getAnnotations(("urn:cts:latinLit:phi1294.phi002.perseus-lat2", "6.1"))
        self.assertEqual(hits, 2, "There should be 2 annotations")
        self.assertCountEqual(
            [anno.uri for anno in annotations],
            [
                "interface/images/N0060308_TIFF_145_145.tif",
                "interface/treebanks/treebank1.xml"
            ],
            "Only 2 annotation s having 6.1 should match"
        )

        # Deep Annotations
        hits, annotations = self.query.getAnnotations(("urn:cts:latinLit:phi1294.phi002.perseus-lat2", "1.pr.1"))
        self.assertEqual(annotations[0], self.four, "Deepest node should match as well")

        # It should take URNs as well
        hits, annotations = self.query.getAnnotations(URN("urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.1"))
        self.assertEqual(annotations[0], self.four, "Deepest node should match as well")

    def test_get_range_match(self):
        """ Ensure range match as well """
        # Higher level annotation or same match
        hits, annotations = self.query.getAnnotations(("urn:cts:latinLit:phi1294.phi002.perseus-lat2", "6.1-6.2"))
        self.assertEqual(hits, 2, "There should be 2 annotations")
        self.assertCountEqual(
            [anno.uri for anno in annotations],
            [
                "interface/images/N0060308_TIFF_145_145.tif",
                "interface/treebanks/treebank1.xml"
            ],
            "Only 2 annotation s having 6.1 should match"
        )

    def test_deep_first(self):
        # Deep Annotations
        hits, annotations = self.query.getAnnotations(URN("urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.1-1.pr.3"))
        self.assertEqual(annotations[0], self.four, "Deepest node should match as well")
        # Test with tuple
        hits, annotations = self.query.getAnnotations(("urn:cts:latinLit:phi1294.phi002.perseus-lat2", "1.pr.1-1.pr.3"))
        self.assertEqual(annotations[0], self.four, "Deepest node should match as well")

    def test_get_resource(self):
        resource = self.query.getResource("0f9a85344190c3a0376f67764f7e193ffb175c1b59fefb0017c15a5cd8baaa33")
        self.assertEqual(resource, self.four, "Getting one resource should work")

        with self.assertRaises(NotFound, msg="Getting a resource for an unknown sha should raise NotFound from werkzeug"):
            self.query.getResource("sasfd")
