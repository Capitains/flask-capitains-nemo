from MyCapytain.common.reference import URN
from flask_nemo.query.proto import QueryPrototype
from flask_nemo.query.annotation import AnnotationResource
from werkzeug.exceptions import NotFound


class SimpleQuery(QueryPrototype):
    """ Query Interface for hardcoded annotations.

    :param annotations: List of tuple of (CTS URN Targeted, URI of the Annotation, Type of the annotation) or/and AnnotationResources
    :type annotations: [(str, str, str) or AnnotationResource]
    :param resolver: Resolver
    :type resolver: Resolver

    This interface requires to be connected to Nemo upon instantiation to expand annotations :

    >>> nemo = Nemo("/", endpoint="http://cts.perseids.org")
    >>> query = SimpleQuery([...])
    >>> query.process(nemo)

    """

    def __init__(self, annotations, resolver=None):
        super(SimpleQuery, self).__init__(None)
        self.__annotations__ = []
        self.__nemo__ = None
        self.__resolver__ = resolver

        for resource in annotations:
            if isinstance(resource, tuple):
                target, body, type_uri = resource
                self.__annotations__.append(AnnotationResource(
                    body, target, type_uri, self.__resolver__
                ))
            else:
                self.__annotations__.append(resource)

    @property
    def textResolver(self):
        return self.__nemo__.resolver

    def process(self, nemo):
        """ Register nemo and parses annotations

        .. note:: Process parses the annotation and extends informations about the target URNs by retrieving resource in range

        :param nemo: Nemo
        """
        self.__nemo__ = nemo
        for annotation in self.__annotations__:
            annotation.target.expanded = frozenset(
                self.__getinnerreffs__(
                    objectId=annotation.target.objectId,
                    subreference=annotation.target.subreference
                )
            )

    def __get_resource_metadata__(self, objectId):
        """ Return a metadata text object

        :param objectId: objectId of the text
        :return: Text
        """
        return self.textResolver.getMetadata(objectId)

    @property
    def annotations(self):
        return self.__annotations__

    def getResource(self, sha):
        try:
            return [annotation for annotation in self.annotations if annotation.sha == sha][0]
        except IndexError:
            raise NotFound

    def getAnnotations(self, targets, wildcard=".", include=None, exclude=None, limit=None, start=1, expand=False,
                       **kwargs):
        annotations = []

        if not targets:
            return len(self.annotations), sorted(self.annotations, key=lambda x: x.uri)

        if not isinstance(targets, list):
            targets = [targets]

        for target in targets:
            if isinstance(target, tuple):
                objectId, subreference = target
            elif isinstance(target, URN):
                objectId, subreference = target.upTo(URN.NO_PASSAGE), str(target.reference)
            else:
                objectId, subreference = target, None

            ref_in_range = list(self.__getinnerreffs__(
                objectId=objectId,
                subreference=subreference
            ))
            ref_in_range = frozenset(ref_in_range)
            annotations.extend([
                annotation
                for annotation in self.annotations
                # Exact match
                if (str(objectId), subreference) == (annotation.target.objectId, annotation.target.subreference) or
                # Deeper match
                len(ref_in_range.intersection(annotation.target.expanded)) > 0
            ])

        annotations = list(set(annotations))

        return len(annotations), sorted(annotations, key=lambda x: x.uri)

    def __getinnerreffs__(self, objectId, subreference):
        """ Resolve the list of urns between in a range

        :param text_metadata: Resource Metadata
        :param objectId: ID of the Text
        :type objectId: str
        :param subreference: ID of the Text
        :type subreference: str
        :return: References in the span
        """
        level = 0
        yield subreference
        while level > -1:
            reffs = self.__nemo__.resolver.getReffs(
                objectId,
                subreference=subreference,
                level=level
            )
            if len(reffs) == 0:
                break
            else:
                for r in reffs:
                    yield r
                level += 1
