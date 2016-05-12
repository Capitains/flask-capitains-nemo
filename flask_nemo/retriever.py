# -*- coding: utf-8 -*-
class RetrieverPrototype(object):

    """ Prototype for a Retriever
    """
    def __init__(self,*args,**kwargs):


    def canRetrieve(uri):
    """ Check to see if this URI is retrievable by this Retriever implementation
    :param uri: the URI of the resource to be retrieved
    :type uri: str
    :return: True if it can be, False if not
    :rtype: bool
    """
       # prototype implementation can't retrieve anything!
       return False

    def read(self,uri):
    """ Retrieve the contents of the resource
    :param uri: the URI of the resource to be retrieved
    :type uri: str
    :return: the contents of the resource
    :rtype: str
    """
        return None
           

    
    

    
