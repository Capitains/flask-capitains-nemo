# -*- coding: utf-8 -*-
class Resolver(object):

    """ Resolver
    :param retriever: Retriever(s) to use to resolve resources passed to this resolver
    :type retriever: Retriever
    """
    

    def __init__(self,*retrievers,**kwargs):
        self.__retrievers__  = retrievers


    def resolve(self,uri):
    """ Resolve a Resource identified by URI
    :param uri: The URI of the resource to be resolved
    :type uri: str
    :return: the contents of the resource as a string
    :rtype: str
    """
        for r in self.__retrievers__:
            if r.canRetrieve(uri):
                return r.read(uri)
                break
           

    
    

    
