from collections import OrderedDict
from flask_nemo.common import join_or_single


def default_chunker(text, getreffs):
    """ This is the default chunker which will resolve the reference giving a callback (getreffs) and a text object with its metadata

    :param text: Text Object representing either an edition or a translation
    :type text: MyCapytains.resources.inventory.Text
    :param getreffs: callback function which retrieves a list of references
    :type getreffs: function

    :return: List of urn references with their human readable version
    :rtype: [(str, str)]
    """
    level = len(text.citation)
    return [tuple([reff.split(":")[-1]]*2) for reff in getreffs(level=level)]


def scheme_chunker(text, getreffs):
    """ This is the scheme chunker which will resolve the reference giving a callback (getreffs) and a text object with its metadata

    :param text: Text Object representing either an edition or a translation
    :type text: MyCapytains.resources.inventory.Text
    :param getreffs: callback function which retrieves a list of references
    :type getreffs: function

    :return: List of urn references with their human readable version
    :rtype: [(str, str)]
    """
    level = len(text.citation)
    types = [citation.name for citation in text.citation]
    if types == ["book", "poem", "line"]:
        level = 2
    elif types == ["book", "line"]:
        return line_chunker(text, getreffs)
    return [tuple([reff.split(":")[-1]]*2) for reff in getreffs(level=level)]


def line_chunker(text, getreffs, lines=30):
    """ Groups line reference together

    :param text: Text object
    :type text: MyCapytains.resources.text.api
    :param getreffs: Callback function to retrieve text
    :type getreffs: function(level)
    :param lines: Number of lines to use by group
    :type lines: int
    :return: List of grouped urn references with their human readable version
    :rtype: [(str, str)]
    """
    level = len(text.citation)
    source_reffs = [reff.split(":")[-1] for reff in getreffs(level=level)]
    reffs = []
    i = 0
    while i + lines - 1 < len(source_reffs):
        reffs.append(tuple([source_reffs[i]+"-"+source_reffs[i+lines-1], source_reffs[i]]))
        i += lines
    if i < len(source_reffs):
        reffs.append(tuple([source_reffs[i]+"-"+source_reffs[len(source_reffs)-1], source_reffs[i]]))
    return reffs


def level_chunker(text, getreffs, level=1):
    """ Chunk a text at the passage level

    :param text: Text object
    :type text: MyCapytains.resources.text.api
    :param getreffs: Callback function to retrieve text
    :type getreffs: function(level)
    :return: List of urn references with their human readable version
    :rtype: [(str, str)]
    """
    references = getreffs(level=level)
    return [(ref.split(":")[-1], ref.split(":")[-1]) for ref in references]


def level_grouper(text, getreffs, level=None, groupby=20):
    """ Alternative to level_chunker: groups levels together at the latest level

    :param text: Text object
    :param getreffs: GetValidReff query callback
    :param level: Level of citation to retrieve
    :param groupby: Number of level to groupby
    :return: Automatically curated references
    """
    if level is None or level > len(text.citation):
        level = len(text.citation)

    references = [ref.split(":")[-1] for ref in getreffs(level=level)]
    _refs = OrderedDict()

    for key in references:
        k = ".".join(key.split(".")[:level-1])
        if k not in _refs:
            _refs[k] = []
        _refs[k].append(key)
        del k

    return [
        (
            join_or_single(ref[0], ref[-1]),
            join_or_single(ref[0], ref[-1])
        )
        for sublist in _refs.values()
        for ref in [
            sublist[i:i+groupby]
            for i in range(0, len(sublist), groupby)
        ]
    ]
