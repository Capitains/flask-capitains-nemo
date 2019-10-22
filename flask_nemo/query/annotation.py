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
        self._objectId = objectId
        self._subreference = subreference

    @property
    def objectId(self):
        return self._objectId

    @property
    def subreference(self):
        return self._subreference

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
        self._uri = uri
        if not isinstance(target, Target):
            self._target = target_class(target)
        else:
            self._target = target
        self._type_uri = type_uri
        self._slug = slug or deepcopy(type(self).SLUG)
        self._sha = hashlib.sha256(
            "{uri}::{type_uri}".format(uri=uri, type_uri=type_uri).encode('utf-8')
        ).hexdigest()

        self._content = None
        self._resolver = resolver
        self._retriever = None
        self._mimetype = mimetype

    @property
    def mimetype(self):
        return self._mimetype

    @property
    def sha(self):
        return self._sha

    @property
    def uri(self):
        return self._uri

    @property
    def type_uri(self):
        return self._type_uri

    @property
    def slug(self):
        return self._slug

    @property
    def target(self):
        return self._target

    @property
    def expandable(self):
        # default AnnotationResource type is not expandable
        return False

    def read(self):
        """ Read the contents of the Annotation Resource

        :return: the contents of the resource
        :rtype: str or bytes or flask.response
        """
        if not self._content:
            self._retriever = self._resolver.resolve(self.uri)
            self._content, self._mimetype = self._retriever.read(self.uri)
        return self._content
 
    def expand(self): 
        """ Expand the contents of the Annotation if it is expandable  (i.e. if it references  multiple resources)

        :return: the list of expanded resources
        :rtype: list(AnnotationResource)
        """
        # default AnnotationResource type doesn't expand
        return []
