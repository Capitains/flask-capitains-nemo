from unittest import TestCase
from flask_nemo.query.proto import QueryPrototype, RetrieverPrototype
from flask_nemo.query.annotation import Resolver, Target, AnnotationResource
import MyCapytain.common.reference


class TestQuery(TestCase):
    """ Test query
    """
    def setUp(self):
       self.fakegetreffs = lambda x:x
       self.retrieverproto = RetrieverPrototype()
       self.resolver = Resolver(self.retrieverproto)
       self.fakeurn = MyCapytain.common.reference.URN("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
       self.faketarget = Target(self.fakeurn)
      

    def test_query_prototype(self):
        """ Test that the query prototype returns nothing """
        self.assertEqual((0,[]), QueryPrototype(self.fakegetreffs).getAnnotations(self.fakeurn))

    def test_retriever_prototype_read(self):
        """ Test that the retriever prototype reads nothing """
        self.assertEqual(None, self.retrieverproto.read("http://example.org"))

    def test_retriever_prototype_match(self):
        """ Test that the retriever prototype matches nothing """
        self.assertEqual(False, RetrieverPrototype.match("http://example.org"))

    def test_resolver(self):
        """ Test that the default resolver, configured with retriever prototype, raises an exception on resolve """
        self.assertRaises(Exception,self.resolver.resolve,"http://example.org")
        
    def test_target_urn(self):
        """ Test that a target returns its urn property """
        self.assertEqual(self.fakeurn,self.faketarget.urn)

    def test_annotation_resource_read(self):
        """ Test that an annotation resource with default resolver raises an exception on read """
        self.assertRaises(Exception,AnnotationResource("http://example.org/annotation",self.faketarget,"http://data.perseus.org/rdfvocab/fake",self.resolver).read)

    def test_annotation_resource_expand(self):
        """ Test that an annotation resource expands to empty list """
        self.assertEqual([],AnnotationResource("http://example.org/annotation",self.faketarget,"http://data.perseus.org/rdfvocab/fake",self.resolver).expand())

    def test_annotation_resource_expandable_property(self):
        """ Test that an annotation resource is not expandable """
        self.assertFalse(AnnotationResource("http://example.org/annotation",self.faketarget,"http://data.perseus.org/rdfvocab/fake",self.resolver).expandable)

    def test_annotation_resource_uri_property(self):
        """ Test that an annotation resource returns its uri """
        self.assertEqual("http://example.org/annotation",AnnotationResource("http://example.org/annotation",self.faketarget,"http://data.perseus.org/rdfvocab/fake",self.resolver).uri)

    def test_annotation_resource_type_uri_property(self):
        """ Test that an annotation resource returns its uri type"""
        self.assertEqual("http://data.perseus.org/rdfvocab/fake",AnnotationResource("http://example.org/annotation",self.faketarget,"http://data.perseus.org/rdfvocab/fake",self.resolver).type_uri)

    def test_annotation_resource_slug_property(self):
        """ Test that an annotation resource returns its slug"""
        self.assertEqual("annotation",AnnotationResource("http://example.org/annotation",self.faketarget,"http://data.perseus.org/rdfvocab/fake",self.resolver).slug)
