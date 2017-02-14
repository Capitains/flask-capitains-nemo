import flask_nemo._data
from flask_nemo.common import getFromDict
from collections import OrderedDict
from slugify import slugify
from operator import itemgetter


def f_slugify(string):
    """ Slugify a string

    :param string: String to slugify
    :return: Slugified string
    """
    return slugify(string)


def f_formatting_passage_reference(string):
    """ Get the first part only of a two parts reference

    :param string: A urn reference part
    :type string: str
    :return: First part only of the two parts reference
    :rtype: str
    """
    return string.split("-")[0]


def f_i18n_iso(isocode, lang="eng"):
    """ Replace isocode by its language equivalent

    :param isocode: Three character long language code
    :param lang: Lang in which to return the language name
    :return: Full Text Language Name
    """
    if lang not in flask_nemo._data.AVAILABLE_TRANSLATIONS:
        lang = "eng"

    try:
        return flask_nemo._data.ISOCODES[isocode][lang]
    except KeyError:
        return "Unknown"


def f_order_resource_by_lang(versions_list):
    """ Takes a list of versions and put translations after editions

    :param versions_list: List of text versions
    :type versions_list: [Text]
    :return: List where first members will be editions
    :rtype: [Text]
    """
    return sorted(versions_list, key=itemgetter("lang"))


def f_hierarchical_passages(reffs, citation):
    """ A function to construct a hierarchical dictionary representing the different citation layers of a text

    :param reffs: passage references with human-readable equivalent
    :type reffs: [(str, str)]
    :param citation: Main Citation
    :type citation: Citation
    :return: nested dictionary representing where keys represent the names of the levels and the final values represent the passage reference
    :rtype: OrderedDict
    """
    d = OrderedDict()
    levels = [x for x in citation]
    for cit, name in reffs:
        ref = cit.split('-')[0]
        levs = ['%{}|{}%'.format(levels[i].name, v) for i, v in enumerate(ref.split('.'))]
        getFromDict(d, levs[:-1])[name] = cit
    return d


def f_is_str(value):
    """ Check if object is a string

    :param value: object to check against
    :return: Return if value is a string
    """
    return isinstance(value, str)


def f_i18n_citation_type(string, lang="eng"):
    """ Take a string of form %citation_type|passage% and format it for human

    :param string: String of formation %citation_type|passage%
    :param lang: Language to translate to
    :return: Human Readable string

    .. note :: To Do : Use i18n tools and provide real i18n
    """
    s = " ".join(string.strip("%").split("|"))
    return s.capitalize()


def f_annotation_filter(annotations, type_uri, number):
    """ Annotation filtering filter

    :param annotations: List of annotations
    :type annotations: [AnnotationResource]
    :param type_uri: URI Type on which to filter
    :type type_uri: str
    :param number: Number of the annotation to return
    :type number: int
    :return: Annotation(s) matching the request
    :rtype: [AnnotationResource] or AnnotationResource
    """
    filtered = [
        annotation
        for annotation in annotations
        if annotation.type_uri == type_uri
    ]
    number = min([len(filtered), number])
    if number == 0:
        return None
    else:
        return filtered[number-1]
