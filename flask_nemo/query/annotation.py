# -*- coding: utf-8 -*-
from copy import deepcopy
from MyCapytain.common.reference import URN
import hashlib


class Target(object):
    """ Object and prototype for representing target of annotation.

    .. note:: Target default object are URN based because that's what Nemo is about.

    :param urn: URN targeted by an Annotation
    :type urn: MyCapytain.common.reference.URN

    :ivar urn: Target urn
    """

    def __init__(self, objectId, subreference=None, **kwargs):
        if isinstance(objectId, URN):
            if objectId.reference is not None:
                subreference = str(objectId.reference)
                objectId = str(objectId.upTo(URN.VERSION))
            else:
                objectId = str(objectId)
                subreference = None
        elif isinstance(objectId, tuple):
            objectId, subreference = objectId
        self.__objectId__ = objectId
        self.__subreference__ = subreference

    @property
    def objectId(self):
        return self.__objectId__

    @property
    def subreference(self):
        return self.__subreference__

    def to_json(self):
        """ Method to call to get a serializable object for json.dump or jsonify based on the target

        :return: dict
        """
        if self.subreference is not None:
            return {
                "source": self.objectId,
                "selector": {
                    "type": "FragmentSelector",
                    "conformsTo": "http://ontology-dts.org/terms/subreference",
                    "value": self.subreference
                }
            }
        else:
            return {"source": self.objectId}


class AnnotationResource(object):
    """ Object representing an annotation. It encapsulates both the body (through the .read() function) and the target (through the .target method)

    :param uri: URI identifier for the AnnotationResource
    :type uri: str
    :param target: the Target of the Annotation
    :type target: Target or str or URN or tuple
    :param type_uri: the URI identifying the underlying datatype of the Annotation
    :type type_uri: str
    :param resolver: Resolver providing access to the annotation
    :type resolver: AnnotationResolver
    :param target_class: Alias for the Target class to be used
    :type target_class: class
    :param mimetype: MimeType of the Annotation object
    :type mimetype: str
    :param slug: Slug type of the object
    :type slug: str

    :ivar mimetype: Mimetype of the annotation object
    :ivar sha: SHA identifying the object
    :ivar uri: Original URI of the object
    :ivar slug: Slug Type of the Annotation Object
    :ivar type_uri: URI of the type
    :ivar expandable: Indication of expandability of the object
    :ivar target: Target object of the Annotation
    """

    SLUG = "annotation"

    def __init__(self, uri, target, type_uri, resolver, target_class=Target, mimetype=None, slug=None, **kwargs):
        self.__uri__ = uri
        if not isinstance(target, Target):
            self.__target__ = target_class(target)
        else:
            self.__target__ = target
        self.__type_uri__ = type_uri
        self.__slug__ = slug or deepcopy(type(self).SLUG)
        self.__sha__ = hashlib.sha256(
            "{uri}::{type_uri}".format(uri=uri, type_uri=type_uri).encode('utf-8')
        ).hexdigest()

        self.__content__ = None
        self.__resolver__ = resolver
        self.__retriever__ = None
        self.__mimetype__ = mimetype

    @property
    def mimetype(self):
        return self.__mimetype__

    @property
    def sha(self):
        return self.__sha__

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
    def target(self):
        return self.__target__

    @property
    def expandable(self):
        # default AnnotationResource type is not expandable
        return False

    def read(self):
        """ Read the contents of the Annotation Resource

        :return: the contents of the resource
        :rtype: str or bytes or flask.response
        """
        if not self.__content__:
            self.__retriever__ = self.__resolver__.resolve(self.uri)
            self.__content__, self.__mimetype__ = self.__retriever__.read(self.uri)
        return self.__content__
 
    def expand(self): 
        """ Expand the contents of the Annotation if it is expandable  (i.e. if it references  multiple resources)

        :return: the list of expanded resources
        :rtype: list(AnnotationResource)
        """
        # default AnnotationResource type doesn't expand
        return []
