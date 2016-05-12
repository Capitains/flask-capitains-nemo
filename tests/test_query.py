from unittest import TestCase
from flask_nemo.query import QueryPrototype
import MyCapytain.common.reference


class TestQuery(TestCase):
    """ Test query
    """

    def setUp(self):
        self.query_api = QueryPrototype        

    def test_prototype(self):
        """ Test that prototype returns nothing """
        self.assertEqual((0,[]), self.query_api.getAnnotations(MyCapytain.common.reference.URN("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")))
        
