import os.path as op
from collections import OrderedDict
import re
from functools import reduce


""" Regular expression to match common literature namespace
"""
regMatch = re.compile("^[a-z]{3}Lit$")


def resource_qualifier(resource):
    """ Split a resource in (filename, directory) tuple with taking care of external resources

    :param resource: A file path or a URI
    :return: (Filename, Directory) for files, (URI, None) for URI
    """
    if resource.startswith("//") or resource.startswith("http"):
        return resource, None
    else:
        return reversed(op.split(resource))

ASSETS_STRUCTURE = {
    "js": OrderedDict(),
    "css": OrderedDict(),
    "static": OrderedDict()
}


def join_or_single(start, end):
    """ Join passages range. If they are the same, return a single part of the range

    :param start: Start of the passage range
    :param end: End of the passage range
    :return: Finale Passage Chunk Identifier
    """
    if start == end:
        return start
    else:
        return "{}-{}".format(
            start,
            end
        )


def getFromDict(dataDict, keyList):
    """Retrieves and creates when necessary a dictionary in nested dictionaries

    :param dataDict: a dictionary
    :param keyList: list of keys
    :return: target dictionary
    """
    return reduce(create_hierarchy, keyList, dataDict)


def create_hierarchy(hierarchy, level):
    """Create an OrderedDict

    :param hierarchy: a dictionary
    :param level: single key
    :return: deeper dictionary
    """
    if level not in hierarchy:
        hierarchy[level] = OrderedDict()
    return hierarchy[level]
