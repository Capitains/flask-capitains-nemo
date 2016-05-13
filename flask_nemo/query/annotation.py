# -*- coding: utf-8 -*-
from copy import deepcopy


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

    SLUG = "annotation"

    def __init__(self, uri, target, type_uri, resolver, **kwargs):
        self.__uri__ = uri
        self.__target__ = target
        self.__type_uri__ = type_uri
        self.__slug__ = deepcopy(type(self).SLUG)

        self.__content__ = None
        self.__resolver__ = resolver
        self.__retriever__ = None

    def read(self):
        """ Read the contents of the Annotation Resource

        :return: the contents of the resource
        :rtype: str
        """
        if not self.__content__:
            self.__retriever__ = self.__resolver__.resolve(self.uri)
            self.__content__ = self.__retriever__.read(self.uri)
        return self.__content__
 
    def expand(self): 
        """ Expand the contents of the Annotation if it is expandable 
          (i.e. if it references  multiple resources)
        :return: the list of expanded resources
        :rtype: list(AnnotationResource)
        """
        # default AnnotationResource type
        # doesn't expand
        return []

    @property
    def uri(self):
        return self.__uri__

    @property
    def type_uri(self):
        return self.__type_uri__

    @property
    def slug(self):
        return self.__slug__

    @property
    def expandable(self):
        # default AnnotationResource type is not expandable
        return False

    @property
    def target(self):
        return self.__target__

class Target(object):
    """ AnnotationTarget
    :param urn: URN targeted by an Annotation
    :type urn: MyCapytain.common.reference.URN
    """

    def __init__(self, urn, **kwargs):
        self.__urn__ = urn

    @property
    def urn(self):
        return self.__urn__
