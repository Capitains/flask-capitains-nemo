from unittest import TestCase
from flask_nemo.query.proto import QueryPrototype, RetrieverPrototype
import MyCapytain.common.reference


class TestQuery(TestCase):
    """ Test query
    """
    def setUp(self):
       self.fakegetreffs = lambda x:x
      

    def test_query_prototype(self):
        """ Test that the query prototype returns nothing """
        self.assertEqual((0,[]), QueryPrototype(self.fakegetreffs).getAnnotations(MyCapytain.common.reference.URN("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")))

    def test_retriever_prototype_read(self):
        """ Test that the retriever prototype reads nothing """
        self.assertEqual(None, RetrieverPrototype().read("http://example.org"))

    def test_retriever_prototype_match(self):
        """ Test that the retriever prototype matches nothing """
        self.assertEqual(False, RetrieverPrototype.match("http://example.org"))

        
