# -*- coding: utf-8 -*-
"""
    Capitains Nemo
    ====

    Extensions for Flask to propose a Nemo extensions
"""

from urllib.parse import quote
from operator import itemgetter
from warnings import warn
from collections import Callable, OrderedDict
from copy import deepcopy as copy
from pkg_resources import resource_filename

from lxml import etree
from flask import render_template, Blueprint, abort, Markup, send_from_directory, Flask, url_for, redirect, request

import jinja2
import inspect
import os.path as op

from MyCapytain.common.constants import Mimetypes
from MyCapytain.resources.prototypes.metadata import ResourceCollection
from MyCapytain.resources.prototypes.cts.inventory import CtsWorkMetadata, CtsEditionMetadata
from MyCapytain.errors import UnknownCollection

import flask_nemo._data
import flask_nemo.filters
from flask_nemo.errors import ValueWarning
from flask_nemo.chunker import level_grouper as __level_grouper__
from flask_nemo.plugins.default import Breadcrumb
from flask_nemo.common import resource_qualifier, ASSETS_STRUCTURE
from flask_nemo.jinjaext import FakeCacheExtension


class Nemo(object):
    """ Nemo is an extension for Flask python micro-framework which provides
    a User Interface to your app for dealing with CTS API.

    :param app: Flask application
    :type app: Flask
    :param resolver: MyCapytain resolver
    :type resolver: MyCapytain.resolvers.prototypes.Resolver
    :param base_url: Base URL to use when registering the endpoint
    :type base_url: str
    :param cache: Flask-Caching instance or any object having a memoize decorator
    :type cache: flask_caching.Cache
    :param plugins: List of plugins to connect to the Nemo instance
    :type plugins: list(flask_nemo.plugin.PluginPrototype)
    :param template_folder: Folder in which the full set of main namespace templates can be found
    :type template_folder: str
    :param static_folder: Folder in which statics file can be found
    :type static_folder: str
    :param static_url_path: Base url to use for assets
    :type static_url_path: str
    :param urls: Function and routes to register (See Nemo.ROUTES)
    :type urls: [(str, str, [str])]
    :param transform: Dictionary of XSL filepath or transform function where default key is the default applied function
    :type transform: bool|dict
    :param chunker: Dictionary of function to group responses of GetValidReff
    :type chunker: {str: function(str, function(int))}
    :param css: Path to additional stylesheets to load
    :type css: [str]
    :param js: Path to additional javascripts to load
    :type js: [str]
    :param templates: Register or override templates (Dictionary of namespace / directory containing template)
    :type templates: {str: str}
    :param statics: Path to additional statics such as picture to load
    :type statics: [str]
    :param prevent_plugin_clearing_assets: Prevent plugins to clear the static folder route
    :type prevent_plugin_clearing_assets: bool
    :param original_breadcrumb: Use the default Breadcrumb plugin packaged with Nemo (Default: True)
    :type original_breadcrumb: bool
    :param default_lang: Default lang to fall back to
    :type default_lang: str

    :ivar assets: Dictionary of assets loaded individually
    :ivar plugins: List of loaded plugins
    :ivar resolver: Resolver
    :ivar cached: List of cached functions
    :ivar cache: Cache Instance

    .. warning:: Until a C libxslt error is fixed ( https://bugzilla.gnome.org/show_bug.cgi?id=620102 ), \
    it is not possible to use strip spaces in the xslt given to this application. See :ref:`lxml.strip-spaces`
    """

    ROUTES = [
        ("/", "r_index", ["GET"]),
        ("/collections", "r_collections", ["GET"]),
        ("/collections/<objectId>", "r_collection", ["GET"]),
        ("/text/<objectId>/references", "r_references", ["GET"]),
        ("/text/<objectId>/passage/<subreference>", "r_passage", ["GET"]),
        ("/text/<objectId>/passage", "r_first_passage", ["GET"])
    ]
    SEMANTIC_ROUTES = [
        "r_collection", "r_references", "r_passage"
    ]
    FILTERS = [
        "f_formatting_passage_reference",
        "f_i18n_iso",
        "f_order_resource_by_lang",
        "f_hierarchical_passages",
        "f_is_str",
        "f_i18n_citation_type",
        "f_slugify"
    ]

    CACHED = [
        # Routes
        "r_index", "r_collection", "r_collections", "r_references", "r_passage", "r_first_passage", "r_assets",
        # Controllers
        "get_inventory", "get_collection", "get_reffs", "get_passage", "get_siblings",
        # Translater
        "semantic", "make_coins", "expose_ancestors_or_children", "make_members", "transform",
        # Business logic
        # "view_maker", "route", #"render",
    ]

    """ Assets dictionary model
    """
    ASSETS = copy(ASSETS_STRUCTURE)
    default_chunker = __level_grouper__

    def __init__(self,
                 name=None, app=None, base_url="/nemo",
                 cache=None, resolver=None,
                 plugins=None,
                 template_folder=None, static_folder=None, static_url_path=None,
                 urls=None, transform=None, chunker=None,
                 css=None, js=None, templates=None, statics=None,
                 prevent_plugin_clearing_assets=False,
                 original_breadcrumb=True, default_lang="eng"):

        self.name = __name__
        if name:
            self.name = name

        if base_url == "/":
            warn("Nemo(base_url) cannot be '/'. If you wish to use the root URL, you need to use an empty value ''. "
                 "This was automatically set to ''", ValueWarning)
            base_url = ""
        self.prefix = base_url

        self.resolver = resolver

        if app is not None:
            self.app = app
        else:
            self.app = None

        self.cache = cache
        self.cached = list()
        for func in self.CACHED:
            self.cached.append((getattr(self, func), self))

        self.prevent_plugin_clearing_assets = prevent_plugin_clearing_assets

        if template_folder:
            self.template_folder = template_folder
        else:
            self.template_folder = resource_filename("flask_nemo", "data/templates")

        if static_folder:
            self.static_folder = static_folder
        else:
            self.static_folder = resource_filename("flask_nemo", "data/static")

        if static_url_path:
            self.static_url_path = static_url_path
        else:
            self.static_url_path = "/assets/nemo"
        self.blueprint = None

        if urls:
            self._urls = urls
        else:
            self._urls = copy(type(self).ROUTES)

        # Adding instance information
        self._urls = [tuple(list(url) + [None]) for url in self._urls]
        # Adding semantic ones
        self._semantic_url = [
            (uri+"/<semantic>", endpoint, method, instance)
            for uri, endpoint, method, instance in self._urls
            if endpoint in self.SEMANTIC_ROUTES
        ]

        self._filters = copy(Nemo.FILTERS)
        self._filters = [tuple([filt] + [None]) for filt in self._filters]

        # Reusing self._inventory across requests
        self._inventory = None
        self._transform = {
            "default": None
        }

        self.__urntransform = {
            "default": None
        }

        if isinstance(transform, dict):
            self._transform.update(transform)

        self.chunker = {
            "default": type(self).default_chunker
        }
        if isinstance(chunker, dict):
            self.chunker.update(chunker)

        # Setting up assets
        self.__assets__ = copy(type(self).ASSETS)
        if css and isinstance(css, list):
            for css_s in css:
                filename, directory = resource_qualifier(css_s)
                self.__assets__["css"][filename] = directory
        if js and isinstance(js, list):
            for javascript in js:
                filename, directory = resource_qualifier(javascript)
                self.__assets__["js"][filename] = directory
        if statics and isinstance(statics, list):
            for static in statics:
                directory, filename = op.split(static)
                self.__assets__["static"][filename] = directory

        self.__plugins_render_views__ = []
        self.__plugins__ = OrderedDict()
        if original_breadcrumb:
            self.__plugins__["nemo.breadcrumb"] = Breadcrumb(name="breadcrumb")
        if isinstance(plugins, list):
            for plugin in plugins:
                self.__plugins__[plugin.name] = plugin

        self.__templates_namespaces__ = [
            ("main", self.template_folder)
        ]
        self.__instance_templates__ = []

        if isinstance(templates, dict):
            self.__instance_templates__.extend(
                [(namespace, folder) for namespace, folder in templates.items()]
            )
        self.__template_loader__ = dict()
        self.__default_lang__ = default_lang

        if app:
            self.init_app(self.app)

    @property
    def plugins(self):
        """ Dictionary of registered plugins

        :rtype: dict
        """
        return self.__plugins__

    @property
    def assets(self):
        """ Dictionary of assets (First level : type, second level resource)

        :rtype: dict
        """
        return self.__assets__

    @property
    def inventory(self):
        """ Root collection of the application

        :rtype: Collection
        """
        return self.get_inventory()

    def init_app(self, app=None):
        """ Initiate the application

        :param app: Flask application on which to add the extension
        :type app: flask.Flask
        """
        # Legacy code
        if app:
            self.app = app

        self.register()

    def get_locale(self):
        """ Retrieve the best matching locale using request headers

        .. note:: Probably one of the thing to enhance quickly.

        :rtype: str
        """
        best_match = request.accept_languages.best_match(['de', 'fr', 'en', 'la'])
        if best_match is None:
            if len(request.accept_languages) > 0:
                best_match = request.accept_languages[0][0][:2]
            else:
                return self.__default_lang__
        lang = self.__default_lang__
        if best_match == "de":
            lang = "ger"
        elif best_match == "fr":
            lang = "fre"
        elif best_match == "en":
            lang = "eng"
        elif best_match == "la":
            lang = "lat"
        return lang

    def transform(self, work, xml, objectId, subreference=None):
        """ Transform input according to potentially registered XSLT

        .. note:: Since 1.0.0, transform takes an objectId parameter which represent the passage which is called

        .. note:: Due to XSLT not being able to be used twice, we rexsltise the xml at every call of xslt

        .. warning:: Until a C libxslt error is fixed ( https://bugzilla.gnome.org/show_bug.cgi?id=620102 ), \
        it is not possible to use strip tags in the xslt given to this application

        :param work: Work object containing metadata about the xml
        :type work: MyCapytains.resources.inventory.Text
        :param xml: XML to transform
        :type xml: etree._Element
        :param objectId: Object Identifier
        :type objectId: str
        :param subreference: Subreference
        :type subreference: str
        :return: String representation of transformed resource
        :rtype: str
        """
        # We check first that we don't have
        if str(objectId) in self._transform:
            func = self._transform[str(objectId)]
        else:
            func = self._transform["default"]

        # If we have a string, it means we get a XSL filepath
        if isinstance(func, str):
            with open(func) as f:
                xslt = etree.XSLT(etree.parse(f))
            return etree.tostring(
                xslt(xml),
                encoding=str, method="html",
                xml_declaration=None, pretty_print=False, with_tail=True, standalone=None
            )

        # If we have a function, it means we return the result of the function
        elif isinstance(func, Callable):
            return func(work, xml, objectId, subreference)
        # If we have None, it means we just give back the xml
        elif func is None:
            return etree.tostring(xml, encoding=str)

    def get_inventory(self):
        """ Request the api endpoint to retrieve information about the inventory

        :return: Main Collection
        :rtype: Collection
        """
        if self._inventory is not None:
            return self._inventory

        self._inventory = self.resolver.getMetadata()
        return self._inventory

    def get_collection(self, objectId):
        """ Retrieve a collection in the inventory

        :param objectId: Collection Identifier
        :type objectId: str
        :return: Requested collection
        :rtype: Collection
        """
        return self.inventory[objectId]

    def get_reffs(self, objectId, subreference=None, collection=None, export_collection=False):
        """ Retrieve and transform a list of references.

        Returns the inventory collection object with its metadata and a callback function taking a level parameter \
        and returning a list of strings.

        :param objectId: Collection Identifier
        :type objectId: str
        :param subreference: Subreference from which to retrieve children
        :type subreference: str
        :param collection: Collection object bearing metadata
        :type collection: Collection
        :param export_collection: Return collection metadata
        :type export_collection: bool
        :return: Returns either the list of references, or the text collection object with its references as tuple
        :rtype: (Collection, [str]) or [str]
        """
        if collection is not None:
            text = collection
        else:
            text = self.get_collection(objectId)
        reffs = self.chunk(
            text,
            lambda level: self.resolver.getReffs(objectId, level=level, subreference=subreference)
        )
        if export_collection is True:
            return text, reffs
        return reffs

    def get_passage(self, objectId, subreference):
        """ Retrieve the passage identified by the parameters

        :param objectId: Collection Identifier
        :type objectId: str
        :param subreference: Subreference of the passage
        :type subreference: str
        :return: An object bearing metadata and its text
        :rtype: InteractiveTextualNode
        """
        passage = self.resolver.getTextualNode(
            textId=objectId,
            subreference=subreference,
            metadata=True
        )
        return passage

    def get_siblings(self, objectId, subreference, passage):
        """ Get siblings of a browsed subreference

        .. note:: Since 1.0.0c, there is no more prevnext dict. Nemo uses the list of original\
        chunked references to retrieve next and previous, or simply relies on the resolver to get siblings\
        when the subreference is not found in given original chunks.

        :param objectId: Id of the object
        :param subreference: Subreference of the object
        :param passage: Current Passage
        :return: Previous and next references
        :rtype: (str, str)
        """
        reffs = [reff for reff, _ in self.get_reffs(objectId)]
        if subreference in reffs:
            index = reffs.index(subreference)
            # Not the first item and not the last one
            if 0 < index < len(reffs) - 1:
                return reffs[index-1], reffs[index+1]
            elif index == 0 and index < len(reffs) - 1:
                return None, reffs[1]
            elif index > 0 and index == len(reffs) - 1:
                return reffs[index-1], None
            else:
                return None, None
        else:
            return passage.siblingsId

    def semantic(self, collection, parent=None):
        """ Generates a SEO friendly string for given collection

        :param collection: Collection object to generate string for
        :param parent: Current collection parent
        :return: SEO/URL Friendly string
        """
        if parent is not None:
            collections = parent.parents[::-1] + [parent, collection]
        else:
            collections = collection.parents[::-1] + [collection]

        return filters.slugify("--".join([item.get_label() for item in collections if item.get_label()]))

    def make_coins(self, collection, text, subreference="", lang=None):
        """ Creates a CoINS Title string from information

        :param collection: Collection to create coins from
        :param text: Text/Passage object
        :param subreference: Subreference
        :param lang: Locale information
        :return: Coins HTML title value
        """
        if lang is None:
            lang = self.__default_lang__
        return "url_ver=Z39.88-2004"\
                 "&ctx_ver=Z39.88-2004"\
                 "&rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Abook"\
                 "&rft_id={cid}"\
                 "&rft.genre=bookitem"\
                 "&rft.btitle={title}"\
                 "&rft.edition={edition}"\
                 "&rft.au={author}"\
                 "&rft.atitle={pages}"\
                 "&rft.language={language}"\
                 "&rft.pages={pages}".format(
                    title=quote(str(text.get_title(lang))), author=quote(str(text.get_creator(lang))),
                    cid=url_for(".r_collection", objectId=collection.id, _external=True),
                    language=collection.lang, pages=quote(subreference), edition=quote(str(text.get_description(lang)))
                 )

    def expose_ancestors_or_children(self, member, collection, lang=None):
        """ Build an ancestor or descendant dict view based on selected information

        :param member: Current Member to build for
        :param collection: Collection from which we retrieved it
        :param lang: Language to express data in
        :return:
        """
        x = {
            "id": member.id,
            "label": str(member.get_label(lang)),
            "model": str(member.model),
            "type": str(member.type),
            "size": member.size,
            "semantic": self.semantic(member, parent=collection)
        }
        if isinstance(member, ResourceCollection):
            x["lang"] = str(member.lang)
        return x

    def make_members(self, collection, lang=None):
        """ Build member list for given collection

        :param collection: Collection to build dict view of for its members
        :param lang: Language to express data in
        :return: List of basic objects
        """
        objects = sorted([
                self.expose_ancestors_or_children(member, collection, lang=lang)
                for member in collection.members
                if member.get_label()
            ],
            key=itemgetter("label")
        )
        return objects

    def make_parents(self, collection, lang=None):
        """ Build parents list for given collection

        :param collection: Collection to build dict view of for its members
        :param lang: Language to express data in
        :return: List of basic objects
        """
        return [
            {
                "id": member.id,
                "label": str(member.get_label(lang)),
                "model": str(member.model),
                "type": str(member.type),
                "size": member.size
            }
            for member in collection.parents
            if member.get_label()
        ]

    def r_index(self):
        """ Homepage route function

        :return: Template to use for Home page
        :rtype: {str: str}
        """
        return {"template": "main::index.html"}

    def r_collections(self, lang=None):
        """ Retrieve the top collections of the inventory

        :param lang: Lang in which to express main data
        :type lang: str
        :return: Collections information and template
        :rtype: {str: Any}
        """
        collection = self.resolver.getMetadata()
        return {
            "template": "main::collection.html",
            "current_label": collection.get_label(lang),
            "collections": {
                "members": self.make_members(collection, lang=lang)
            }
        }

    def r_collection(self, objectId, lang=None):
        """ Collection content browsing route function

        :param objectId: Collection identifier
        :type objectId: str
        :param lang: Lang in which to express main data
        :type lang: str
        :return: Template and collections contained in given collection
        :rtype: {str: Any}
        """
        collection = self.resolver.getMetadata(objectId)
        return {
            "template": "main::collection.html",
            "collections": {
                "current": {
                    "label": str(collection.get_label(lang)),
                    "id": collection.id,
                    "model": str(collection.model),
                    "type": str(collection.type),
                },
                "members": self.make_members(collection, lang=lang),
                "parents": self.make_parents(collection, lang=lang)
            },
        }

    def r_references(self, objectId, lang=None):
        """ Text exemplar references browsing route function

        :param objectId: Collection identifier
        :type objectId: str
        :param lang: Lang in which to express main data
        :type lang: str
        :return: Template and required information about text with its references
        """
        collection, reffs = self.get_reffs(objectId=objectId, export_collection=True)
        return {
            "template": "main::references.html",
            "objectId": objectId,
            "citation": collection.citation,
            "collections": {
                "current": {
                    "label": collection.get_label(lang),
                    "id": collection.id,
                    "model": str(collection.model),
                    "type": str(collection.type),
                },
                "parents": self.make_parents(collection, lang=lang)
            },
            "reffs": reffs
        }

    def r_first_passage(self, objectId):
        """ Provides a redirect to the first passage of given objectId

        :param objectId: Collection identifier
        :type objectId: str
        :return: Redirection to the first passage of given text
        """
        collection, reffs = self.get_reffs(objectId=objectId, export_collection=True)
        first, _ = reffs[0]
        return redirect(
            url_for(".r_passage_semantic", objectId=objectId, subreference=first, semantic=self.semantic(collection))
        )

    def r_passage(self, objectId, subreference, lang=None):
        """ Retrieve the text of the passage

        :param objectId: Collection identifier
        :type objectId: str
        :param lang: Lang in which to express main data
        :type lang: str
        :param subreference: Reference identifier
        :type subreference: str
        :return: Template, collections metadata and Markup object representing the text
        :rtype: {str: Any}
        """
        collection = self.get_collection(objectId)
        if isinstance(collection, CtsWorkMetadata):
            editions = [t for t in collection.children.values() if isinstance(t, CtsEditionMetadata)]
            if len(editions) == 0:
                raise UnknownCollection("This work has no default edition")
            return redirect(url_for(".r_passage", objectId=str(editions[0].id), subreference=subreference))
        text = self.get_passage(objectId=objectId, subreference=subreference)
        passage = self.transform(text, text.export(Mimetypes.PYTHON.ETREE), objectId)
        prev, next = self.get_siblings(objectId, subreference, text)
        return {
            "template": "main::text.html",
            "objectId": objectId,
            "subreference": subreference,
            "collections": {
                "current": {
                    "label": collection.get_label(lang),
                    "id": collection.id,
                    "model": str(collection.model),
                    "type": str(collection.type),
                    "author": text.get_creator(lang),
                    "title": text.get_title(lang),
                    "description": text.get_description(lang),
                    "citation": collection.citation,
                    "coins": self.make_coins(collection, text, subreference, lang=lang)
                },
                "parents": self.make_parents(collection, lang=lang)
            },
            "text_passage": Markup(passage),
            "prev": prev,
            "next": next
        }

    def r_assets(self, filetype, asset):
        """ Route for specific assets.

        :param filetype: Asset Type
        :param asset: Filename of an asset
        :return: Response
        """
        if filetype in self.assets and asset in self.assets[filetype] and self.assets[filetype][asset]:
            return send_from_directory(
                directory=self.assets[filetype][asset],
                filename=asset
            )
        abort(404)

    def register_assets(self):
        """ Merge and register assets, both as routes and dictionary

        :return: None
        """
        self.blueprint.add_url_rule(
            # Register another path to ensure assets compatibility
            "{0}.secondary/<filetype>/<asset>".format(self.static_url_path),
            view_func=self.r_assets,
            endpoint="secondary_assets",
            methods=["GET"]
        )

    def create_blueprint(self):
        """ Create blueprint and register rules

        :return: Blueprint of the current nemo app
        :rtype: flask.Blueprint
        """
        self.register_plugins()

        self.blueprint = Blueprint(
            self.name,
            "nemo",
            url_prefix=self.prefix,
            template_folder=self.template_folder,
            static_folder=self.static_folder,
            static_url_path=self.static_url_path
        )

        for url, name, methods, instance in self._urls:
            self.blueprint.add_url_rule(
                url,
                view_func=self.view_maker(name, instance),
                endpoint=_plugin_endpoint_rename(name, instance),
                methods=methods
            )

        for url, name, methods, instance in self._semantic_url:
            self.blueprint.add_url_rule(
                url,
                view_func=self.view_maker(name, instance),
                endpoint=_plugin_endpoint_rename(name, instance)+"_semantic",
                methods=methods
            )

        self.register_assets()
        self.register_filters()

        # We extend the loading list by the instance value
        self.__templates_namespaces__.extend(self.__instance_templates__)
        # We generate a template loader
        for namespace, directory in self.__templates_namespaces__[::-1]:
            if namespace not in self.__template_loader__:
                self.__template_loader__[namespace] = []
            self.__template_loader__[namespace].append(
                jinja2.FileSystemLoader(op.abspath(directory))
            )
        self.blueprint.jinja_loader = jinja2.PrefixLoader(
            {namespace: jinja2.ChoiceLoader(paths) for namespace, paths in self.__template_loader__.items()},
            "::"
        )

        if self.cache is not None:
            for func, instance in self.cached:
                setattr(instance, func.__name__, self.cache.memoize()(func))

        return self.blueprint

    def view_maker(self, name, instance=None):
        """ Create a view

        :param name: Name of the route function to use for the view.
        :type name: str
        :return: Route function which makes use of Nemo context (such as menu informations)
        :rtype: function
        """
        if instance is None:
            instance = self
        sig = "lang" in [
            parameter.name
            for parameter in inspect.signature(getattr(instance, name)).parameters.values()
        ]

        def route(**kwargs):
            if sig and "lang" not in kwargs:
                kwargs["lang"] = self.get_locale()
            if "semantic" in kwargs:
                del kwargs["semantic"]
            return self.route(getattr(instance, name), **kwargs)
        return route

    def main_collections(self, lang=None):
        """ Retrieve main parent collections of a repository

        :param lang: Language to retrieve information in
        :return: Sorted collections representations
        """
        return sorted([
            {
                "id": member.id,
                "label": str(member.get_label(lang=lang)),
                "model": str(member.model),
                "type": str(member.type),
                "size": member.size
            }
            for member in self.resolver.getMetadata().members
        ], key=itemgetter("label"))

    def make_cache_keys(self, endpoint, kwargs):
        """ This function is built to provide cache keys for templates

        :param endpoint: Current endpoint
        :param kwargs: Keyword Arguments
        :return: tuple of i18n dependant cache key and i18n ignoring cache key
        :rtype: tuple(str)
        """
        keys = sorted(kwargs.keys())
        i18n_cache_key = endpoint+"|"+"|".join([kwargs[k] for k in keys])
        if "lang" in keys:
            cache_key = endpoint+"|" + "|".join([kwargs[k] for k in keys if k != "lang"])
        else:
            cache_key = i18n_cache_key
        return i18n_cache_key, cache_key

    def render(self, template, **kwargs):
        """ Render a route template and adds information to this route.

        :param template: Template name.
        :type template: str
        :param kwargs: dictionary of named arguments used to be passed to the template
        :type kwargs: dict
        :return: Http Response with rendered template
        :rtype: flask.Response
        """

        kwargs["cache_key"] = "%s" % kwargs["url"].values()
        kwargs["lang"] = self.get_locale()
        kwargs["assets"] = self.assets
        kwargs["main_collections"] = self.main_collections(kwargs["lang"])
        kwargs["cache_active"] = self.cache is not None
        kwargs["cache_time"] = 0
        kwargs["cache_key"], kwargs["cache_key_i18n"] = self.make_cache_keys(request.endpoint, kwargs["url"])
        kwargs["template"] = template

        for plugin in self.__plugins_render_views__:
            kwargs.update(plugin.render(**kwargs))

        return render_template(kwargs["template"], **kwargs)

    def route(self, fn, **kwargs):
        """ Route helper : apply fn function but keep the calling object, *ie* kwargs, for other functions

        :param fn: Function to run the route with
        :type fn: function
        :param kwargs: Parsed url arguments
        :type kwargs: dict
        :return: HTTP Response with rendered template
        :rtype: flask.Response
        """
        new_kwargs = fn(**kwargs)

        # If there is no templates, we assume that the response is finalized :
        if not isinstance(new_kwargs, dict):
            return new_kwargs

        new_kwargs["url"] = kwargs
        return self.render(**new_kwargs)

    def register(self):
        """ Register the app using Blueprint

        :return: Nemo blueprint
        :rtype: flask.Blueprint
        """
        if self.app is not None:
            if not self.blueprint:
                self.blueprint = self.create_blueprint()
            self.app.register_blueprint(self.blueprint)
            if self.cache is None:
                # We register a fake cache extension.
                setattr(self.app.jinja_env, "_fake_cache_extension", self)
                self.app.jinja_env.add_extension(FakeCacheExtension)
            return self.blueprint
        return None

    def register_filters(self):
        """ Register filters for Jinja to use

       .. note::  Extends the dictionary filters of jinja_env using self._filters list
        """
        for _filter, instance in self._filters:
            if not instance:
                self.app.jinja_env.filters[
                    _filter.replace("f_", "")
                ] = getattr(flask_nemo.filters, _filter)
            else:
                self.app.jinja_env.filters[
                    _filter.replace("f_", "")
                ] = getattr(instance, _filter.replace("_{}".format(instance.name), ""))

    def register_plugins(self):
        """ Register plugins in Nemo instance

        - Clear routes first if asked by one plugin
        - Clear assets if asked by one plugin and replace by the last plugin registered static_folder
        - Register each plugin
            - Append plugin routes to registered routes
            - Append plugin filters to registered filters
            - Append templates directory to given namespaces
            - Append assets (CSS, JS, statics) to given resources 
            - Append render view (if exists) to Nemo.render stack
        """
        if len([plugin for plugin in self.__plugins__.values() if plugin.clear_routes]) > 0:  # Clear current routes
            self._urls = list()
            self.cached = list()

        clear_assets = [plugin for plugin in self.__plugins__.values() if plugin.clear_assets]
        if len(clear_assets) > 0 and not self.prevent_plugin_clearing_assets:  # Clear current Assets
            self.__assets__ = copy(type(self).ASSETS)
            static_path = [plugin.static_folder for plugin in clear_assets if plugin.static_folder]
            if len(static_path) > 0:
                self.static_folder = static_path[-1]

        for plugin in self.__plugins__.values():
            self._urls.extend([(url, function, methods, plugin) for url, function, methods in plugin.routes])
            self._filters.extend([(filt, plugin) for filt in plugin.filters])
            self.__templates_namespaces__.extend(
                [(namespace, directory) for namespace, directory in plugin.templates.items()]
            )
            for asset_type in self.__assets__:
                for key, value in plugin.assets[asset_type].items():
                    self.__assets__[asset_type][key] = value
            if plugin.augment:
                self.__plugins_render_views__.append(plugin)

            if hasattr(plugin, "CACHED"):
                for func in plugin.CACHED:
                    self.cached.append((getattr(plugin, func), plugin))
            plugin.register_nemo(self)

    def chunk(self, text, reffs):
        """ Handle a list of references depending on the text identifier using the chunker dictionary.

        :param text: Text object from which comes the references
        :type text: MyCapytains.resources.texts.api.Text
        :param reffs: List of references to transform
        :type reffs: References
        :return: Transformed list of references
        :rtype: [str]
        """
        if str(text.id) in self.chunker:
            return self.chunker[str(text.id)](text, reffs)
        return self.chunker["default"](text, reffs)


def _plugin_endpoint_rename(fn_name, instance):
    """ Rename endpoint function name to avoid conflict when namespacing is set to true

    :param fn_name: Name of the route function
    :param instance: Instance bound to the function
    :return: Name of the new namespaced function name
    """

    if instance and instance.namespaced:
        fn_name = "r_{0}_{1}".format(instance.name, fn_name[2:])
    return fn_name
