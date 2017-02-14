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

    def getAnnotations(self, targets, wildcard=".", include=None, exclude=None, limit=None, start=1, expand=False,
                       **kwargs):
        """ Retrieve annotations from the query provider

        :param targets: The CTS URN(s) to query as the target of annotations
        :type targets: [MyCapytain.common.reference.URN], URN or None
        :param wildcard: Wildcard specifier for how to match the URN
        :type wildcard: str
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

        .. note::

            Wildcard should be one of the following value

            - '.' to match exact,
            - '.%' to match exact plus lower in the hierarchy
            - '%.' to match exact + higher in the hierarchy
            - '-' to match in the range
            - '%.%' to match all

        """
        return 0, []

    def getResource(self, sha):
        """ Retrieve a single annotation resource by sha

        :param sha: The sha of the resource
        :type sha: str
        :return: the requested annotation resource
        :rtype: AnnotationResource
        """
        return None
