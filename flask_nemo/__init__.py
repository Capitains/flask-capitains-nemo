# -*- coding: utf-8 -*-
"""
    Capitains Nemo
    ====

    Extensions for Flask to propose a Nemo extensions
"""

__version__ = "0.0.1"

import os.path as op
from flask import request, render_template, Blueprint, abort, Markup, send_from_directory
import MyCapytain.endpoints.cts5
import MyCapytain.resources.texts.tei
import MyCapytain.resources.texts.api
import MyCapytain.resources.inventory
from lxml import etree
import requests_cache
from collections import OrderedDict, Callable
import jinja2
from copy import copy
from pkg_resources import resource_filename

class Nemo(object):
    """ Nemo is an extension for Flask python micro-framework which provides
    a User Interface to your app for dealing with CTS API.

    :param app: Flask application
    :type app: Flask
    :param api_url: URL of the API Endpoint
    :type api_url: str
    :param base_url: Base URL to use when registering the endpoint
    :type base_url: str
    :param cache: SQLITE cache file name
    :type base_url: str
    :param expire: TIme before expiration of cache, default 3600
    :type exipre: int
    :param template_folder: Folder in which the templates can be found
    :type template_folder: str
    :param static_folder: Folder in which statics file can be found
    :type static_folder: str
    :param static_url_path: Base url to use for assets
    :type static_url_path: str
    :param urls: Function and routes to register (See Nemo.ROUTES)
    :type urls: [(str, str, [str])]
    :param inventory: Default inventory to use
    :type inventory: str
    :param transform: Dictionary of XSL filepath or transform function where default key is the default applied function
    :type transform: bool|dict
    :param chunker: Dictionary of function to group responses of GetValidReff
    :type chunker: {str: function(str, function(int))}
    :param prevnext: Dictionary of function to execute GetPrevNext
    :type prevnext: {str: function(str, function())}
    :param css: Path to additional stylesheets to load
    :type css: [str]
    :param js: Path to additional javascripts to load
    :type js: [str]
    :param templates: Register or override templates (Dictionary of index / path)
    :type templates: {str: str}
    :param statics: Path to additional statics such as picture to load
    :type statics: [str]

    .. warning:: Until a C libxslt error is fixed ( https://bugzilla.gnome.org/show_bug.cgi?id=620102 ), it is not possible to use strip spaces in the xslt given to this application. See :ref:`lxml.strip-spaces`
    """

    ROUTES = [
        ("/", "r_index", ["GET"]),
        ("/read/<collection>", "r_collection", ["GET"]),
        ("/read/<collection>/<textgroup>", "r_texts", ["GET"]),
        ("/read/<collection>/<textgroup>/<work>/<version>", "r_version", ["GET"]),
        ("/read/<collection>/<textgroup>/<work>/<version>/<passage_identifier>", "r_passage", ["GET"])
    ]
    TEMPLATES = {
        "container": "container.html",
        "menu": "menu.html",
        "text": "text.html",
        "textgroups": "textgroups.html",
        "index": "index.html",
        "texts": "texts.html",
        "version": "version.html"
    }
    COLLECTIONS = {
        "latinLit": "Latin",
        "greekLit": "Ancient Greek",
        "froLit": "Medieval French"
    }
    FILTERS = [
        "f_active_link",
        "f_collection_i18n",
        "f_formatting_passage_reference"
    ]

    def __init__(self, name=None, app=None, api_url="/", base_url="/nemo", cache=None, expire=3600,
                 template_folder=None, static_folder=None, static_url_path=None,
                 urls=None, inventory=None, transform=None, chunker=None, prevnext=None,
                 css=None, js=None, templates=None, statics=None):
        __doc__ = Nemo.__doc__
        self.name = __name__
        if name:
            self.name = name
        self.prefix = base_url
        self.api_url = api_url
        self.endpoint = MyCapytain.endpoints.cts5.CTS(self.api_url)

        self.templates = copy(Nemo.TEMPLATES)
        if isinstance(templates, dict):
            self.templates.update(templates)

        if app is not None:
            self.app = app
            self.init_app(self.app)
        else:
            self.app = None

        self.api_inventory = inventory
        if self.api_inventory:
            self.endpoint.inventory = self.api_inventory
        self.cache = None
        if cache is not None:
            self.__register_cache(cache, expire)

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
            self._urls = Nemo.ROUTES

        self._filters = copy(Nemo.FILTERS)
        # Reusing self._inventory across requests
        self._inventory = None
        self.__transform = {
            "default" : None
        }

        if isinstance(transform, dict):
            self.__transform.update(transform)

        self.chunker = {}
        self.chunker["default"] = Nemo.default_chunker
        if isinstance(chunker, dict):
            self.chunker.update(chunker)

        self.prevnext = {}
        self.prevnext["default"] = Nemo.default_prevnext
        if isinstance(prevnext, dict):
            self.prevnext.update(prevnext)

        self.css = []
        if isinstance(css, list):
            self.css = css

        self.js = []
        if isinstance(js, list):
            self.js = js

        self.statics = []
        if isinstance(statics, list):
            self.statics = statics

        self.assets = {
            "js": OrderedDict(),
            "css": OrderedDict(),
            "static": OrderedDict()
        }

    def __register_cache(self, sqlite_path, expire):
        """ Set up a request cache

        :param sqlite_path: Set up a sqlite cache system
        :type sqlite_path: str
        :param expire: Time for the cache to expire
        :type expire: int
        """
        self.cache = requests_cache.install_cache(
            sqlite_path,
            backend="sqlite",
            expire_after=expire
        )

    def init_app(self, app):
        """ Initiate the application

        :param app: Flask application on which to add the extension
        :type app: flask.Flask
        """
        if "CTS_API_URL" in app.config:
            self.api_url = app.config['CTS_API_URL']
        if "CTS_API_INVENTORY" in app.config:
            self.api_inventory = app.config['CTS_API_INVENTORY']
        if self.app is None:
            self.app = app

    def transform(self, work, xml):
        """ Transform input according to potentiallyregistered XSLT

        .. note:: Due to XSLT not being able to be used twice, we rexsltise the xml at every call of xslt
        .. warning:: Until a C libxslt error is fixed ( https://bugzilla.gnome.org/show_bug.cgi?id=620102 ), it is not possible to use strip tags in the xslt given to this application

        :param work: Work object containing metadata about the xml
        :type work: MyCapytains.resources.inventory.Text
        :param xml: XML to transform
        :type xml: etree._Element
        :return: String representation of transformed resource
        :rtype: str
        """
        # We check first that we don't have
        if str(work.urn) in self.__transform:
            func = self.__transform[str(work.urn)]
        else:
            func = self.__transform["default"]

        # If we have a string, it means we get a XSL filepath
        if isinstance(func, str):
            with open(func) as f:
                xslt = etree.XSLT(etree.parse(f))
            return etree.tostring(xslt(xml), encoding=str)

        # If we have a function, it means we return the result of the function
        elif isinstance(func, Callable):
            return func(work, xml)
        # If we have None, it meants we just give back the xml
        elif func is None:
            return etree.tostring(xml, encoding=str)

    def get_inventory(self):
        """ Request the api endpoint to retrieve information about the inventory

        :return: The text inventory
        :rtype: MyCapytain.resources.inventory.TextInventory
        """
        if self._inventory:
            return self._inventory

        reply = self.endpoint.getCapabilities(inventory=self.api_inventory)
        inventory = MyCapytain.resources.inventory.TextInventory(resource=reply)
        self._inventory = inventory
        return self._inventory

    def get_collections(self):
        """ Filter inventory and make a list of available collections

        :return: A set of CTS Namespaces
        :rtype: set(str)
        """
        inventory = self.get_inventory()
        urns = set(
            [inventory.textgroups[textgroup].urn[2] for textgroup in inventory.textgroups]
        )
        return urns

    def get_textgroups(self, collection_urn=None):
        """ Retrieve textgroups

        :param collection_urn: Collection to use for filtering the textgroups
        :type collection_urn: str
        :return: List of textgroup filtered by collection
        :rtype: [MyCapytain.resources.inventory.Textgroup]
        """
        inventory = self.get_inventory()
        if collection_urn is not None:
            return Nemo.map_urns(inventory, collection_urn, 2, "textgroups")
        return list(inventory.textgroups.values())

    def get_works(self, collection_urn=None, textgroup_urn=None):
        """ Retrieve works

        :param collection_urn: Collection to use for filtering the textgroups
        :type collection_urn: str
        :param textgroup_urn: Textgroup to use for filtering the works
        :type textgroup_urn: str
        :return: List of work filtered by collection/Textgroup
        :rtype: [MyCapytain.resources.inventory.Work]
        """
        if collection_urn is not None and textgroup_urn is not None:
            textgroup = list(
                filter(lambda x: Nemo.filter_urn(x, 3, textgroup_urn), self.get_textgroups(collection_urn))
            )
            if len(textgroup) == 1:
                return textgroup[0].works.values()
            else:
                return []
        elif collection_urn is None and textgroup_urn is None:
            return [work for textgroup in self.get_inventory().textgroups.values() for work in textgroup.works.values()]
        else:
            raise ValueError("Get_Work takes either two None value or two set up value")

    def get_texts(self, collection_urn=None, textgroup_urn=None, work_urn=None):
        """ Retrieve texts

        :param collection_urn: Collection to use for filtering the textgroups
        :type collection_urn: str
        :param textgroup_urn: Textgroup to use for filtering the works
        :type textgroup_urn: str
        :param work_urn: Work to use for filtering the texts
        :type work_urn: str
        :return: List of texts filtered by parameters
        :rtype: [MyCapytain.resources.inventory.Text]
        """
        if collection_urn is not None and textgroup_urn is not None and work_urn is not None:
            work = list(
                filter(lambda x: Nemo.filter_urn(x, 4, work_urn), self.get_works(collection_urn, textgroup_urn))
            )
            if len(work) == 1:
                return work[0].texts.values()
            else:
                return []
        elif collection_urn is not None and textgroup_urn is not None and work_urn is None:
            return [
                text
                for work in self.get_works(collection_urn, textgroup_urn)
                for text in work.texts.values()
            ]
        elif collection_urn is None and textgroup_urn is None and work_urn is None:
            return [
                text
                for textgroup in self.get_inventory().textgroups.values()
                for work in textgroup.works.values()
                for text in work.texts.values()
            ]
        else:
            raise ValueError("Get_Work takes either two None value or two set up value")

    def get_text(self, collection_urn, textgroup_urn, work_urn, version_urn):
        """ Retrieve one version of a Text

        :param collection_urn: Collection to use for filtering the textgroups
        :type collection_urn: str
        :param textgroup_urn: Textgroup to use for filtering the works
        :type textgroup_urn: str
        :param work_urn: Work identifier to use for filtering texts
        :type work_urn: str
        :param version_urn: Version identifier
        :type version_urn: str
        :return: A Text represented by the various parameters
        :rtype: MyCapytain.resources.inventory.Text
        """
        work = list(
            filter(lambda x: Nemo.filter_urn(x, 4, work_urn), self.get_works(collection_urn, textgroup_urn))
        )
        if len(work) == 1:
            texts = work[0].texts.values()
        else:
            texts = []

        texts = [text for text in texts if text.urn[5] == version_urn]
        if len(texts) == 1:
            return texts[0]
        abort(404)

    def get_reffs(self, collection, textgroup, work, version):
        """ Get the setup for valid reffs.

        Returns the inventory text object with its metadata and a callback function taking a level parameter
        and returning a list of strings.

        :param collection: Collection identifier
        :type collection: str
        :param textgroup: Textgroup identifier
        :type textgroup: str
        :param work: Work identifier
        :type work: str
        :param version: Version identifier
        :type version: str
        :return: Text with its metadata, callback function to retrieve validreffs
        :rtype: (MyCapytains.resources.texts.api.Text, lambda: [str])
        """
        text = self.get_text(collection, textgroup, work, version)
        reffs = MyCapytain.resources.texts.api.Text(
            "urn:cts:{0}:{1}.{2}.{3}".format(collection, textgroup, work, version),
            self.endpoint,
            citation=text.citation
        )
        return text, lambda level: reffs.getValidReff(level=level)

    def get_passage(self, collection, textgroup, work, version, passage_identifier):
        """ Retrieve the passage identified by the parameters


        :param collection: Collection identifier
        :type collection: str
        :param textgroup: Textgroup identifier
        :type textgroup: str
        :param work: Work identifier
        :type work: str
        :param version: Version identifier
        :type version: str
        :param passage_identifier: Reference Identifier
        :type passage_identifier: str
        :return: A Passage object containing informations about the passage
        :rtype: MyCapytain.resources.texts.api.Passage
        """
        text = MyCapytain.resources.texts.api.Text(
            "urn:cts:{0}:{1}.{2}.{3}".format(collection, textgroup, work, version),
            self.endpoint
        )
        passage = text.getPassage(passage_identifier)
        return passage

    def r_index(self):
        """ Homepage route function

        :return: Template to use for Home page
        :rtype: {str: str}
        """
        return {"template": self.templates["index"]}

    def r_collection(self, collection):
        """ Collection content browsing route function

        :param collection: Collection identifier
        :type collection: str
        :return: Template and textgroups contained in given collections
        :rtype: {str: Any}
        """
        return {
            "template": self.templates["textgroups"],
            "textgroups": self.get_textgroups(collection)
        }

    def r_texts(self, collection, textgroup):
        """ Textgroup content browsing route function

        :param collection: Collection identifier
        :type collection: str
        :param textgroup: Textgroup Identifier
        :type textgroup: str
        :return: Template and texts contained in given textgroup
        :rtype: {str: Any}
        """
        return {
            "template": self.templates["texts"],
            "texts": self.get_texts(collection, textgroup)
        }

    def r_version(self, collection, textgroup, work, version):
        """ Text exemplar references browsing route function

        :param collection: Collection identifier
        :type collection: str
        :param textgroup: Textgroup Identifier
        :type textgroup: str
        :param work: Work identifier
        :type work: str
        :param version: Version identifier
        :type version: str
        :return: Template, version inventory object and references urn parts
        :rtype: {
            "template" : str,
            "version": MyCapytains.resources.inventory.Text,
            "reffs": [str]
            }
        """
        version, reffs = self.get_reffs(collection, textgroup, work, version)
        reffs = self.chunk(version, reffs)
        return {
            "template": self.templates["version"],
            "version": version,
            "reffs": reffs
        }

    def r_passage(self, collection, textgroup, work, version, passage_identifier):
        """ Retrieve the text of the passage

        :param collection: Collection identifier
        :type collection: str
        :param textgroup: Textgroup Identifier
        :type textgroup: str
        :param work: Work identifier
        :type work: str
        :param version: Version identifier
        :type version: str
        :param passage_identifier: Reference identifier
        :type passage_identifier: str
        :return: Template, version inventory object and Markup object representing the text
        :rtype: {str: Any}
        """
        edition = self.get_text(collection, textgroup, work, version)
        text = self.get_passage(collection, textgroup, work, version, passage_identifier)

        passage = self.transform(edition, text.xml)
        prev, next = self.getprevnext(text, Nemo.prevnext_callback_generator(text))
        return {
            "template": self.templates["text"],
            "version": edition,
            "text_passage": Markup(passage),
            "prev": prev,
            "next": next
        }

    def r_assets(self, type, asset):
        """ Route for specific assets.

        :param asset: Filename of an asset
        :return: Response
        """
        if type in self.assets and asset in self.assets[type]:
            return send_from_directory(directory=self.assets[type][asset], filename=asset)
        abort(404)

    def register_assets(self):
        """ Merge and register assets, both as routes and dictionary

        :return: None
        """
        # Save assets routes
        for css in self.css:
            directory, filename = op.split(css)
            self.assets["css"][filename] = directory
        for js in self.js:
            directory, filename = op.split(js)
            self.assets["js"][filename] = directory
        for static in self.statics:
            directory, filename = op.split(static)
            self.assets["static"][filename] = directory

        self.blueprint.add_url_rule(
            # Register another path to ensure assets compatibility
            "{0}.secondary/<type>/<asset>".format(self.static_url_path),
            view_func=self.r_assets,
            endpoint="secondary_assets",
            methods=["GET"]
        )

    def create_blueprint(self):
        """ Create blueprint and register rules

        :return: Blueprint of the current nemo app
        :rtype: flask.Blueprint
        """
        self.blueprint = Blueprint(
            self.name,
            "nemo",
            url_prefix=self.prefix,
            template_folder=self.template_folder,
            static_folder=self.static_folder,
            static_url_path=self.static_url_path
        )

        for url, name, methods in self._urls:
            self.blueprint.add_url_rule(
                url,
                view_func=self.view_maker(name),
                endpoint=name,
                methods=methods
            )

        self.register_assets()

        # If we have added or overriden the default templates
        if self.templates != Nemo.TEMPLATES:
            folders = set([op.dirname(path) for path in self.templates if path != self.template_folder])
            self.loader = jinja2.ChoiceLoader([
                    self.blueprint.jinja_loader
                ] + [
                    jinja2.FileSystemLoader(folder) for folder in folders
                ]
            )
            self.blueprint.jinja_loader = self.loader

        return self.blueprint

    def view_maker(self, name):
        """ Create a view

        :param name: Name of the route function to use for the view.
        :type name: str
        :return: Route function which makes use of Nemo context (such as menu informations)
        :rtype: function
        """
        return lambda **kwargs: self.route(getattr(self, name), **kwargs)

    def render(self, template, **kwargs):
        """ Render a route template and adds information to this route.

        :param template: Template name
        :type template: str
        :param kwargs: dictionary of named arguments used to be passed to the template
        :type kwargs: dict
        :return: Http Response with rendered template
        :rtype: flask.Response
        """
        kwargs["collections"] = self.get_collections()
        kwargs["lang"] = "eng"

        if Nemo.in_and_not_in("textgroup", "textgroups", kwargs):
            kwargs["textgroups"] = self.get_textgroups(kwargs["url"]["collection"])

            if Nemo.in_and_not_in("text", "texts", kwargs):
                kwargs["texts"] = self.get_texts(kwargs["url"]["collection"], kwargs["url"]["textgroup"])

        kwargs["assets"] = self.assets
        kwargs["templates"] = self.templates

        return render_template(template, **kwargs)

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
        new_kwargs["url"] = kwargs
        return self.render(**new_kwargs)

    def register_routes(self):
        """ Register routes on app using Blueprint

        :return: Nemo blueprint
        :rtype: flask.Blueprint
        """
        if self.app is not None:
            if not self.blueprint:
                self.blueprint = self.create_blueprint()
            self.app.register_blueprint(self.blueprint)
            return self.blueprint
        return None

    def register_filters(self):
        """ Register filters for Jinja to use

       .. note::  Extends the dictionary filters of jinja_env using self._filters list
        """
        for _filter in self._filters:
            self.app.jinja_env.filters[
                _filter.replace("f_", "")
            ] = getattr(self.__class__, _filter)

    def chunk(self, text, reffs):
        """ Handle a list of references depending on the text identifier using the chunker dictionary.

        :param text: Text object from which comes the references
        :type text: MyCapytains.resources.texts.api.Text
        :param reffs: Callback function to retrieve a list of string with a level parameter
        :type reffs: callback(level)
        :return: Transformed list of references
        :rtype: [str]
        """
        if str(text.urn) in self.chunker:
            return self.chunker[str(text.urn)](text, reffs)
        return self.chunker["default"](text, reffs)

    def getprevnext(self, passage, callback):
        """ Retrieve previous and next passage using

        :param text: Text object from which comes the references
        :type text: MyCapytains.resources.texts.api.Passage
        :param reffs: Callback function to retrieve a tuple where first element is the previous passage, and second the next
        :type reffs: callback()
        :return: Reference of previous passage, reference of next passage
        :rtype: (str, str)
        """
        if str(passage.urn) in self.prevnext:
            return self.prevnext[str(passage.urn)](passage, callback)
        return self.prevnext["default"](passage, callback)

    @staticmethod
    def in_and_not_in(identifier, collection, kwargs):
        """ Check if an element identified by identifier is in kwargs but not the collection containing it

        :param identifier: URL Identifier of one kind of element (Textgroup, work, etc.)
        :type identifier: str
        :param collection: Resource identifier of one kind of element (Textgroup, work, etc.)
        :type collection: str
        :param kwargs: Arguments passed to a template
        :type kwargs: {str: Any}
        :return: Indicator of presence of required informations
        :rtype: bool
        """
        return identifier in kwargs["url"] and collection not in kwargs

    @staticmethod
    def f_active_link(string, url):
        """ Check if current string is in the list of names

        :param string: String to check for in url
        :return: CSS class "active" if valid
        :rtype: str
        """
        if string in url.values():
            return "active"
        return ""

    @staticmethod
    def f_collection_i18n(string):
        """ Return a i18n human readable version of a CTS domain such as latinLit

        :param string: CTS Domain identifier
        :type string: str
        :return: Human i18n readable version of the CTS Domain
        :rtype: str
        """
        if string in Nemo.COLLECTIONS:
            return Nemo.COLLECTIONS[string]
        return string

    @staticmethod
    def f_formatting_passage_reference(string):
        """ Get the first part only of a two parts reference

        :param string: A urn reference part
        :type string: str
        :return: First part only of the two parts reference
        :rtype: str
        """
        return string.split("-")[0]

    @staticmethod
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

    @staticmethod
    def scheme_chunker(text, getreffs):
        """ This is the scheme chunker which will resolve the reference giving a callback (getreffs) and a text object with its metadata

        :param text: Text Object representing either an edition or a translation
        :type text: MyCapytains.resources.inventory.Text
        :param getreffs: callback function which retrieves a list of references
        :type getreffs: function

        :return: List of urn references with their human readable version
        :rtype: [(str, str)]
        """
        # print(text)
        level = len(text.citation)
        types = [citation.name for citation in text.citation]
        if types == ["book", "poem", "line"]:
            level = 2
        elif types == ["book", "line"]:
            return Nemo.line_chunker(text, getreffs)
        return [tuple([reff.split(":")[-1]]*2) for reff in getreffs(level=level)]

    @staticmethod
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

    @staticmethod
    def default_prevnext(passage, callback):
        """ Default deliver of prevnext informations

        :param passage: Passage for which to get previous and following reference
        :type passage: MyCapytains.resources.texts.api.Passage
        :param callback: Function to retrieve those information
        :type callback: function

        :return: Tuple representing previous and following reference
        :rtype: (str, str)
        """
        previous, following = passage._next, passage._prev

        if previous is None and following is None:
            previous, following = callback()

        if previous is not None:
            previous = previous.split(":")[-1]
        if following is not None:
            following = following.split(":")[-1]
        return previous, following

    @staticmethod
    def prevnext_callback_generator(passage):
        """ Default callback generator to retrieve prev and next value of a passage

        :param passage: Passage for which to get previous and following reference
        :type passage: MyCapytains.resources.texts.api.Passage
        :return: Function to retrieve those information
        :rtype: function
        """
        def callback():
            return MyCapytain.resources.texts.api.Passage.prevnext(
                passage.parent.resource.getPrevNextUrn(urn=str(passage.urn))
            )
        return callback

    @staticmethod
    def map_urns(items, query, part_of_urn=1, attr="textgroups"):
        """ Small function to map urns to filter out a list of items or on a parent item

        :param items: Inventory object
        :type items: MyCapytains.resources.inventory.Resource
        :param query: Part of urn to check against
        :type query: str
        :param part_of_urn: Identifier of the part of the urn
        :type part_of_urn: int
        :return: Items corresponding to the object children filtered by the query
        :rtype: list(items.children)
        """

        if attr is not None:
            return [
                item
                for item in getattr(items, attr).values()
                if Nemo.filter_urn(item, part_of_urn, query)
            ]

    @staticmethod
    def filter_urn(item, part_of_urn, query):
        """ Small function to map urns to filter out a list of items or on a parent item

        :param item: Inventory object
        :param query: Part of urn to check against
        :type query: str
        :param part_of_urn: Identifier of the part of the urn
        :type part_of_urn: int
        :return: Items corresponding to the object children filtered by the query
        :rtype: list(items.children)
        """
        return item.urn[part_of_urn].lower() == query.lower().strip()
