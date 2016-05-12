# -*- coding: utf-8 -*-
class AnnotationResource(object):

    """ AnnotationResource
    :param uri: URI identifier for the AnnotationResource
    :type uri: str
    :param target: the Target of the Annotation
    :type target: Target
    :param type_uri: the URI identifying the underlying datatype of the Annotation
    :type type_uri: str
    :param resolver: Resolver providing access to the annotation
    :type resolver: AnnotationResolver
    """

    SLUG="annotation"

    def __init__(self, uri, target, type_uri, resolver, **kwargs):
        self.__uri__ = uri
        self.__target__ = target
        self.__type_uri__ = type_uri
        self.__resolver__ = resolver 


    def read(self):
    """ Read the contents of the Annotation Resource
    :rtype: str
    """
        return self.__resolver__.resolve(uri)
 
    def expand(self): 
    """ Expand the contents of the Annotation if it is expandable 
      (i.e. if it references  multiple resources)
    :rtype: list(AnnotationResource)
    """
        # default AnnotationResource type
        # doesn't expand
        return []

    @property
    def type_uri(self):
        return self.__expandable__

    @property
    def slug(self):
      return SLUG

    @property
    def expandable(self):
        # default AnnotationResource type is not expandable
        return False



class Target(object):
    """ AnnotationTarget
    :param urn: URN targeted by an Annotation
    :type urn: URN
    """

    def __init__(self, urn, *args, **kwargs):
        self.__urn__ = urn

    @property
    def urn(self)
        return self.__urn__
     
