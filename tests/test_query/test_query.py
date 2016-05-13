from unittest import TestCase
from flask_nemo.query.proto import QueryPrototype
from flask_nemo.query.annotation import Target, AnnotationResource
from flask_nemo.query.resolve import RetrieverPrototype, Resolver, UnresolvableURIError
import MyCapytain.common.reference


class TestQuery(TestCase):
    """ Test query
    """

    def setUp(self):
        self.fakegetreffs = lambda x:x
        self.retrieverproto = RetrieverPrototype()
        self.resolver = Resolver(self.retrieverproto)
        self.fakeurn = MyCapytain.common.reference.URN("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
        self.faketarget = self.fakeurn

    def test_query_prototype(self):
        """ Test that the query prototype returns nothing """
        self.assertEqual((0,[]), QueryPrototype(self.fakegetreffs).getAnnotations(self.fakeurn))

    def test_query_prototype_get_resource(self):
        """ Test that the query prototype returns nothing """
        self.assertEqual(None, QueryPrototype(self.fakegetreffs).getResource("any"))

    def test_retriever_prototype_read(self):
        """ Test that the retriever prototype reads nothing """
        self.assertEqual(None, self.retrieverproto.read("http://example.org"))

    def test_retriever_prototype_match(self):
        """ Test that the retriever prototype matches nothing """
        self.assertEqual(False, RetrieverPrototype().match("http://example.org"))

    def test_resolver(self):
        """ Test that the default resolver, configured with retriever prototype, raises an exception on resolve """
        with self.assertRaises(UnresolvableURIError, msg="Default resolver should raise exception"):
            self.resolver.resolve("http://example.org")
        
    def test_target_urn(self):
        """ Test that a target returns its urn property """
        self.assertEqual(self.fakeurn, Target(self.fakeurn).urn)

    def test_annotation_resource_read(self):
        """ Test that an annotation resource with default resolver raises an exception on read """
        annotation = AnnotationResource(
            "http://example.org/annotation",
            self.faketarget,
            "http://data.perseus.org/rdfvocab/fake",
            self.resolver
        )
        with self.assertRaises(UnresolvableURIError):
            annotation.read()

    def test_annotation_resource_expand(self):
        """ Test that an annotation resource expands to empty list """
        annotation = AnnotationResource(
            "http://example.org/annotation",
            self.faketarget,
            "http://data.perseus.org/rdfvocab/fake",
            self.resolver
        )
        self.assertEqual(
            [], annotation.expand(),
            "Expand should return a list"
        )

    def test_annotation_resource_expandable_property(self):
        """ Test that an annotation resource is not expandable """
        annotation = AnnotationResource(
            "http://example.org/annotation",
            self.faketarget,
            "http://data.perseus.org/rdfvocab/fake",
            self.resolver
        )
        self.assertFalse(annotation.expandable, msg="Default annotation should not be expandable")

    def test_annotation_resource_uri_property(self):
        """ Test that an annotation resource returns its uri """

        annotation = AnnotationResource(
            "http://example.org/annotation",
            self.faketarget,
            "http://data.perseus.org/rdfvocab/fake",
            self.resolver
        )
        self.assertEqual(
            "http://example.org/annotation", annotation.uri,
            "Annotation uri property should read correctly"
        )

    def test_annotation_resource_type_uri_property(self):
        """ Test that an annotation resource returns its uri type"""
        annotation = AnnotationResource(
            "http://example.org/annotation",
            self.faketarget,
            "http://data.perseus.org/rdfvocab/fake",
            self.resolver
        )
        self.assertEqual(
            "http://data.perseus.org/rdfvocab/fake", annotation.type_uri,
            "Annotation type_uri should read correctly"
        )

    def test_annotation_resource_slug_property(self):
        """ Test that an annotation resource returns its slug"""
        annotation = AnnotationResource(
            "http://example.org/annotation",
            self.faketarget,
            "http://data.perseus.org/rdfvocab/fake",
            self.resolver
        )
        self.assertEqual(
            "annotation", annotation.slug,
            "Annotation slug should read correctly"
        )
