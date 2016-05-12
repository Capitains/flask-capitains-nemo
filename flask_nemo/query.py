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

    def __init__(self, name=None, getreffs, **kwargs):
        self.__instance_name__ = name
        if not name:
            self.__instance_name__ = type(self).__name__
        self.getreffs = getreffs

    def getAnnotations(self, *urn=None, wildcard=".", *include=None, *exclude=None, limit=None, start=1, expand=False, **kwargs)
        """ Retrieve annotations from the query provider
        :param urn: The CTS URN(s) to query as the target of annotations
        :type urn: URN
        :param wildcard: Wildcard specifier for how to match the URN 
        :type wildcard: str ('.' to match exact,
                             '.%' to match exact plus lower in the hierarchy
                             '%.' to match exact + higher in the hierarchy 
                             '-' to match in the range 
                             '%.%' to match all )
        :param include: URI(s) of Annotation types to include in the results
        :type include: str
        :param exclude: URI(s) of Annotation types to include in the results
        :type exclude: str
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

