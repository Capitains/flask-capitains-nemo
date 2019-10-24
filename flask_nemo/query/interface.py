from MyCapytain.common.reference import URN, BaseReferenceSet, BaseReference
from MyCapytain.errors import CitationDepthError
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

    # ToDo: We should probably make a real use (and not just test fixes)
    #       of BaseReferenceSet and BaseReference here. This seems silly
    #       that we are restringing stuff here.

    def __init__(self, annotations, resolver=None):
        super(SimpleQuery, self).__init__(None)
        self._annotations = []
        self._nemo = None
        self._resolver = resolver

        for resource in annotations:
            if isinstance(resource, tuple):
                target, body, type_uri = resource
                self._annotations.append(AnnotationResource(
                    body, target, type_uri, self._resolver
                ))
            else:
                self._annotations.append(resource)

    @property
    def textResolver(self):
        return self._nemo.resolver

    def process(self, nemo):
        """ Register nemo and parses annotations

        .. note:: Process parses the annotation and extends informations about the target URNs by retrieving resource in range

        :param nemo: Nemo
        """
        self._nemo = nemo
        for annotation in self._annotations:
            annotation.target.expanded = frozenset(
                self._getinnerreffs(
                    objectId=annotation.target.objectId,
                    subreference=annotation.target.subreference
                )
            )

    def _get_resource_metadata(self, objectId):
        """ Return a metadata text object

        :param objectId: objectId of the text
        :return: Text
        """
        return self.textResolver.getMetadata(objectId)

    @property
    def annotations(self):
        return self._annotations

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

            ref_in_range = list(self._getinnerreffs(
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

    def _getinnerreffs(self, objectId, subreference) -> BaseReference:
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
            try:
                # type == BaseReferenceSet. I removed the explicit typing below since it broke the tests on Python 3.5.
                reffs = self._nemo.resolver.getReffs(
                    objectId,
                    subreference=subreference,
                    level=level
                )
            # This is the new behavior in MyCapytain 3.0.0
            except CitationDepthError:
                break
            else:
                for r in reffs:
                    # We only needs the start of the reference here,
                    # because we specifically want to drop ranges here.
                    yield r.start
                level += 1
