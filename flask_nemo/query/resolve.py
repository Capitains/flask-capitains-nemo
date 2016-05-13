from requests import request
import re


class UnresolvableURIError(Exception):
    """ Error to be run when a URI is not resolvable
    """


class Resolver(object):

    """ Prototype for a Resolver
    :param retriever: Retriever(s) to use to resolve resources passed to this resolver
    :type retriever: Retriever instances
    """

    def __init__(self, *retrievers, **kwargs):
        self.__retrievers__ = retrievers

    def resolve(self, uri):
        """ Resolve a Resource identified by URI
        :param uri: The URI of the resource to be resolved
        :type uri: str
        :return: the contents of the resource as a string
        :rtype: str
        """
        for r in self.__retrievers__:
            if type(r).match(uri):
                return r
        raise UnresolvableURIError()


class RetrieverPrototype(object):

    """ Prototype for a Retriever
    """

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

    def read(self, uri):
        """ Retrieve the contents of the resource
        :param uri: the URI of the resource to be retrieved
        :type uri: str
        :return: the contents of the resource
        :rtype: str
        """
        return None


class HTTPRetriever(RetrieverPrototype):
    """ Http retriever retrieves resources being remotely hosted in CTS
    """
    __reg_exp__ = re.compile("^(https?:)?\/\/")

    @staticmethod
    def match(uri):
        """ Check to see if this URI is retrievable by this Retriever implementation

        :param uri: the URI of the resource to be retrieved
        :type uri: str
        :return: True if it can be, False if not
        :rtype: bool
        """
        # prototype implementation can't retrieve anything!
        return HTTPRetriever.__reg_exp__.match(uri) is not None

    def read(self, uri):
        """ Retrieve the contents of the resource

        :param uri: the URI of the resource to be retrieved
        :type uri: str
        :return: the contents of the resource
        :rtype: str
        """
        return request("GET", uri).text


class LocalRetriever(RetrieverPrototype):
    """ Http retriever retrieves resources being remotely hosted in CTS

    :cvar FORCE_MATCH: Force the local retriever to read a resource even if it does not match with the regular expression
    :type FORCE_MATCH: bool
    """
    __reg_exp__ = re.compile("^([a-z0-9_ ]+|\.{1,2})?/")
    FORCE_MATCH = False

    @staticmethod
    def match(uri):
        """ Check to see if this URI is retrievable by this Retriever implementation

        :param uri: the URI of the resource to be retrieved
        :type uri: str
        :return: True if it can be, False if not
        :rtype: bool
        """
        # prototype implementation can't retrieve anything!
        if LocalRetriever.FORCE_MATCH:
            return LocalRetriever.__reg_exp__.match(uri) is not None
        else:
            return True

    def read(self, uri):
        """ Retrieve the contents of the resource

        :param uri: the URI of the resource to be retrieved
        :type uri: str
        :return: the contents of the resource
        :rtype: str
        """
        file = None
        with open(uri, "r") as f:
            file = f.read()
        return file


class CTSRetriever(RetrieverPrototype):
    """ CTS retriever retrieves resources being remotely hosted in CTS

    :param retriever: CTS5 Retrieve
    :type retriever: MyCapytain.retrievers.cts5.
    """
    __reg_exp__ = re.compile("^urn:cts:")

    def __init__(self, retriever):
        self.__retriever__ = retriever

    @staticmethod
    def match(uri):
        """ Check to see if this URI is retrievable by this Retriever implementation

        :param uri: the URI of the resource to be retrieved
        :type uri: str
        :return: True if it can be, False if not
        :rtype: bool
        """
        # prototype implementation can't retrieve anything!
        return CTSRetriever.__reg_exp__.match(uri) is not None

    def read(self, uri):
        """ Retrieve the contents of the resource

        :param uri: the URI of the resource to be retrieved
        :type uri: str
        :return: the contents of the resource
        :rtype: str
        """
        return self.__retriever__.getPassage(uri)