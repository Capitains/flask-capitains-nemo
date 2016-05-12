import flask_nemo._data
from flask_nemo.common import regMatch, getFromDict
from collections import defaultdict, OrderedDict


def f_order_author(textgroups, lang="eng"):
    """ Order a list of textgroups

    :param textgroups: list of textgroups to be sorted
    :param lang: Language to display
    :return: Sorted list
    """
    __textgroups__ = {
        tg.metadata["groupname"][lang] or str(tg.urn): tg
        for tg in textgroups
    }

    return [
       __textgroups__[key]
       for key in sorted(list(__textgroups__.keys()))
   ]


def f_active_link(string, url):
    """ Check if current string is in the list of names

    :param string: String to check for in url
    :return: CSS class "active" if valid
    :rtype: str
    """
    if string in url.values():
        return "active"
    return ""


def f_collection_i18n(string, lang="eng"):
    """ Return a i18n human readable version of a CTS domain such as latinLit

    :param string: CTS Domain identifier
    :type string: str
    :return: Human i18n readable version of the CTS Domain
    :rtype: str
    """
    if string in flask_nemo._data.COLLECTIONS:
        return flask_nemo._data.COLLECTIONS[string]
    elif regMatch.match(string):
        lg = string[0:2]
        if lg in flask_nemo._data.ISOCODES and lang in flask_nemo._data.ISOCODES[lg]:
            return flask_nemo._data.ISOCODES[lg][lang]
    return string


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


def f_group_texts(versions_list):
    """ Takes a list of versions and regroup them by work identifier

    :param versions_list: List of text versions
    :type versions_list: [Text]
    :return: List of texts grouped by work
    :rtype: [(Work, [Text])]
    """
    works = {}
    texts = defaultdict(list)
    for version in versions_list:
        if version.urn.work not in works:
            works[version.urn.work] = version.parents[0]
        texts[version.urn.work].append(version)
    return [
        (works[index], texts[index])
        for index in works
    ]


def f_order_text_edition_translation(versions_list):
    """ Takes a list of versions and put translations after editions

    :param versions_list: List of text versions
    :type versions_list: [Text]
    :return: List where first members will be editions
    :rtype: [Text]
    """
    translations = []
    editions = []
    for version in versions_list:
        if version.subtype == "Translation":
            translations.append(version)
        else:
            editions.append(version)
    return editions + translations


def f_hierarchical_passages(reffs, version):
    """ A function to construct a hierarchical dictionary representing the different citation layers of a text

    :param reffs: passage references with human-readable equivalent
    :type reffs: [(str, str)]
    :param version: text from which the reference comes
    :type version: MyCapytain.resources.inventory.Text
    :return: nested dictionary representing where keys represent the names of the levels and the final values represent the passage reference
    :rtype: OrderedDict
    """
    d = OrderedDict()
    levels = [x for x in version.citation]
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

    .. todo :: use i18n tools and provide real i18n
    """
    s = " ".join(string.strip("%").split("|"))
    return s.capitalize()