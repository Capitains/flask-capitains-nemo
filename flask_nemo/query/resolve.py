from requests import request
import re
from os import path as op
from mimetypes import guess_type
from flask import send_file
from MyCapytain.common.constants import Mimetypes


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
            if r.match(uri):
                return r
        raise UnresolvableURIError()


class RetrieverPrototype(object):

    """ Prototype for a Retriever
    """

    def match(self, uri):
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
        :return: the contents of the resource and it's mime type in a tuple
        :rtype: str, str
        """
        return None, "text/xml"


class HTTPRetriever(RetrieverPrototype):
    """ Http retriever retrieves resources being remotely hosted in CTS
    """
    __reg_exp__ = re.compile("^(https?:)?\/\/")

    def match(self, uri):
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
        req = request("GET", uri)
        return req.content, req.headers['Content-Type']


class LocalRetriever(RetrieverPrototype):
    """ Http retriever retrieves resources being remotely hosted in CTS

    .. note:: Local Retriever needs to be instantiated

    :cvar FORCE_MATCH: Force the local retriever to read a resource even if it does not match with the regular expression
    :type FORCE_MATCH: bool
    """

    def __init__(self, path="./"):
        self.__path__ = op.abspath(path)

    def __absolute__(self, uri):
        """ Get the absolute uri for a file

        :param uri: URI of the resource to be retrieved
        :return: Absolute Path
        """
        return op.abspath(op.join(self.__path__, uri))

    def match(self, uri):
        """ Check to see if this URI is retrievable by this Retriever implementation

        :param uri: the URI of the resource to be retrieved
        :type uri: str
        :return: True if it can be, False if not
        :rtype: bool
        """
        absolute_uri = self.__absolute__(uri)

        return absolute_uri.startswith(self.__path__) and op.exists(absolute_uri)

    def read(self, uri):
        """ Retrieve the contents of the resource

        :param uri: the URI of the resource to be retrieved
        :type uri: str
        :return: the contents of the resource
        :rtype: str
        """
        uri = self.__absolute__(uri)
        mime, _ = guess_type(uri)
        if "image" in mime:
            return send_file(uri), mime
        else:
            with open(uri, "r") as f:
                file = f.read()
        return file, mime


class CTSRetriever(RetrieverPrototype):
    """ CTS retriever retrieves resources being remotely hosted in CTS

    .. note:: Local Retriever needs to be instantiated

    :param resolver: CTS5 Resolver
    :type resolver: MyCapytain.resolver.cts.*
    """
    __reg_exp__ = re.compile("^urn:cts:")

    def __init__(self, resolver):
        self.__resolver__ = resolver

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
        return self.__resolver__.getTextualNode(uri).export(Mimetypes.XML.TEI), "text/xml"
