# -*- coding: utf-8 -*-
class QueryPrototype(object):
    """ Prototype for Nemo Query API Implementations
    :param name: The Name of this Query API
    :type name: str
    :param getreffs: callback function to retrieve a list of references given URN
    :type getreffs: function
    """

    MATCH_EXACT = "."
    MATCH_LOWER = ".%"
    MATCH_HIGHER = "%."
    MATCH_RANGE = "-"
    MATCH_ALL = "%.%"

    def __init__(self, getreffs, **kwargs):
        self.__getreffs__ = getreffs

    def getAnnotations(self, *urns, wildcard=".", include=None, exclude=None, limit=None, start=1, expand=False, **kwargs):
        """ Retrieve annotations from the query provider
        :param urns: The CTS URN(s) to query as the target of annotations
        :type urns: MyCapytain.common.reference.URN
        :param wildcard: Wildcard specifier for how to match the URN 
        :type wildcard: str ('.' to match exact,
                             '.%' to match exact plus lower in the hierarchy
                             '%.' to match exact + higher in the hierarchy 
                             '-' to match in the range 
                             '%.%' to match all )
        :param include: URI(s) of Annotation types to include in the results
        :type include: list(str)
        :param exclude: URI(s) of Annotation types to include in the results
        :type exclude: list(str)
        :param limit: The max number of results to return (Default is None for no limit)
        :type limit: int
        :param start: the starting record to return (Default is 1)
        :type start: int 
        :param expand: Flag to state whether Annotations are expanded (Default is False)
        :type expand: bool
    
        :return: Tuple representing the query results. The first element
                 The first element is the number of total Annotations found
                 The second element is the list of Annotations
        :rtype: (int, list(Annotation)
        """
        return (0,[])

class RetrieverPrototype(object):

    """ Prototype for a Retriever
    """
    def __init__(self,*args,**kwargs):
        pass

    @staticmethod
    def match(uri):
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
           
