# -*- coding: utf-8 -*-
"""
    Capitains Nemo
    ====

    Extensions for Flask to propose a Nemo extensions
"""


import os.path as op
import jinja2
from flask import render_template, Blueprint, abort, Markup, send_from_directory, Flask
import MyCapytain.retrievers.cts5
from MyCapytain.retrievers.proto import CTS as CtsProtoRetriever
import MyCapytain.resources.texts.tei
import MyCapytain.resources.texts.api
import MyCapytain.resources.inventory
from MyCapytain.common.reference import URN
from lxml import etree
from copy import deepcopy as copy
from pkg_resources import resource_filename
from collections import Callable, OrderedDict
import flask_nemo._data
import flask_nemo.filters
from flask_nemo.chunker import default_chunker as __default_chunker__
from flask_nemo.default import Breadcrumb
from flask_nemo.common import resource_qualifier, ASSETS_STRUCTURE


class Nemo(object):
    """ Nemo is an extension for Flask python micro-framework which provides
    a User Interface to your app for dealing with CTS API.

    :param app: Flask application
    :type app: Flask
    :param api_url: URL of the API Endpoint
    :type api_url: str
    :param retriever: CTS Retriever (Will be defaulted to api_url using cts5 retriever if necessary)
    :type retriever: MyCapytain.retrievers.proto.CTS
    :param base_url: Base URL to use when registering the endpoint
    :type base_url: str
    :param cache: SQLITE cache file name
    :type base_url: str
    :param expire: TIme before expiration of cache, default 3600
    :type expire: int
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
    :param inventory: Default inventory to use
    :type inventory: str
    :param transform: Dictionary of XSL filepath or transform function where default key is the default applied function
    :type transform: bool|dict
    :param urntransform: Dictionary of urn transform functions where default key is the default applied function
    :type urntransform: bool|dict
    :param chunker: Dictionary of function to group responses of GetValidReff
    :type chunker: {str: function(str, function(int))}
    :param prevnext: Dictionary of function to execute GetPrevNext
    :type prevnext: {str: function(str, function())}
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

    :ivar assets: Dictionary of assets loaded individually
    :ivar plugins: List of loaded plugins

    .. warning:: Until a C libxslt error is fixed ( https://bugzilla.gnome.org/show_bug.cgi?id=620102 ), it is not possible to use strip spaces in the xslt given to this application. See :ref:`lxml.strip-spaces`
    """

    ROUTES = [
        ("/", "r_index", ["GET"]),
        ("/read/<collection>", "r_collection", ["GET"]),
        ("/read/<collection>/<textgroup>", "r_texts", ["GET"]),
        ("/read/<collection>/<textgroup>/<work>/<version>", "r_version", ["GET"]),
        ("/read/<collection>/<textgroup>/<work>/<version>/<passage_identifier>", "r_passage", ["GET"])
    ]
    FILTERS = [
        "f_active_link",
        "f_collection_i18n",
        "f_formatting_passage_reference",
        "f_i18n_iso",
        "f_group_texts",
        "f_order_text_edition_translation",
        "f_hierarchical_passages",
        "f_is_str",
        "f_i18n_citation_type",
        "f_order_author"
    ]

    """ Assets dictionary model
    """
    ASSETS = copy(ASSETS_STRUCTURE)
    default_chunker = __default_chunker__

    def __init__(self, name=None, app=None, api_url="/", retriever=None, base_url="/nemo", cache=None, expire=3600,
                 plugins=None,
                 template_folder=None, static_folder=None, static_url_path=None,
                 urls=None, inventory=None, transform=None, urntransform=None, chunker=None, prevnext=None,
                 css=None, js=None, templates=None, statics=None,
                 prevent_plugin_clearing_assets=False,
                 original_breadcrumb=True):

        self.name = __name__
        if name:
            self.name = name
        self.prefix = base_url
        self.api_url = api_url

        if isinstance(retriever, CtsProtoRetriever):
            self.retriever = retriever
        else:
            self.retriever = MyCapytain.retrievers.cts5.CTS(self.api_url)

        if app is not None:
            self.app = app
        else:
            self.app = None

        self.api_inventory = inventory
        if self.api_inventory:
            self.retriever.inventory = self.api_inventory

        self.cache = None
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

        self._filters = copy(Nemo.FILTERS)
        self._filters = [tuple([filt] + [None]) for filt in self._filters]

        # Reusing self._inventory across requests
        self._inventory = None
        self.__transform = {
            "default": None
        }

        self.__urntransform = {
            "default": None
        }

        if isinstance(transform, dict):
            self.__transform.update(transform)

        if isinstance(urntransform, dict):
            self.__urntransform.update(urntransform)

        self.chunker = dict()
        self.chunker["default"] = type(self).default_chunker
        if isinstance(chunker, dict):
            self.chunker.update(chunker)

        self.prevnext = dict()
        self.prevnext["default"] = type(self).default_prevnext
        if isinstance(prevnext, dict):
            self.prevnext.update(prevnext)

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

        if app:
            self.init_app(self.app)

    @property
    def plugins(self):
        return self.__plugins__

    @property
    def assets(self):
        return self.__assets__

    def init_app(self, app=None):
        """ Initiate the application

        :param app: Flask application on which to add the extension
        :type app: flask.Flask
        """
        # Legacy code
        if "CTS_API_URL" in app.config:
            self.api_url = app.config['CTS_API_URL']
        if "CTS_API_INVENTORY" in app.config:
            self.api_inventory = app.config['CTS_API_INVENTORY']
        if app:
            self.app = app

        self.register()

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
            return etree.tostring(xslt(xml), encoding=str, method="html", xml_declaration=None, pretty_print=False, with_tail=True, standalone=None)

        # If we have a function, it means we return the result of the function
        elif isinstance(func, Callable):
            return func(work, xml)
        # If we have None, it meants we just give back the xml
        elif func is None:
            return etree.tostring(xml, encoding=str)

    def transform_urn(self, urn):
        """ Transform urn according to configurable function

        :param urn: URN to transform
        :type urn: URN
        :return: the URN (transformed or not)
        :rtype: URN
        """
        # We check first that we don't have an override function
        # N.B. overrides will be on the text level, not the passage
        if urn.upTo(URN.NO_PASSAGE) in self.__urntransform:
            func = self.__urntransform[urn.upTo(URN.NO_PASSAGE)]
        else:
            func = self.__urntransform["default"]

        # If we have a function, it means we return the result of the function
        if isinstance(func, Callable):
            return func(urn)
        # If we have None, it means we just give back the urn as string
        return urn

    def get_inventory(self):
        """ Request the api endpoint to retrieve information about the inventory

        :return: The text inventory
        :rtype: MyCapytain.resources.inventory.TextInventory
        """
        if self._inventory:
            return self._inventory

        reply = self.retriever.getCapabilities(inventory=self.api_inventory)
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
            [inventory.textgroups[textgroup].urn.namespace for textgroup in inventory.textgroups]
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

        texts = [text for text in texts if text.urn.version == version_urn]
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
            self.retriever,
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
            self.retriever
        )
        passage = text.getPassage(passage_identifier)
        return passage

    def r_index(self):
        """ Homepage route function

        :return: Template to use for Home page
        :rtype: {str: str}
        """
        return {"template": "main::index.html"}

    def r_collection(self, collection):
        """ Collection content browsing route function

        :param collection: Collection identifier
        :type collection: str
        :return: Template and textgroups contained in given collections
        :rtype: {str: Any}
        """
        return {
            "template": "main::textgroups.html",
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
            "template": "main::texts.html",
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
            "template": "main::version.html",
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
        urn = self.transform_urn(text.urn)
        return {
            "template": "main::text.html",
            "version": edition,
            "text_passage": Markup(passage),
            "urn": urn,
            "prev": prev,
            "next": next
        }

    def r_assets(self, type, asset):
        """ Route for specific assets.

        :param asset: Filename of an asset
        :return: Response
        """
        if type in self.assets and asset in self.assets[type] and self.assets[type][asset]:
            return send_from_directory(
                directory=self.assets[type][asset],
                filename=asset
            )
        abort(404)

    def register_assets(self):
        """ Merge and register assets, both as routes and dictionary

        :return: None
        """
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

        return self.blueprint

    def view_maker(self, name, instance=None):
        """ Create a view

        :param name: Name of the route function to use for the view.
        :type name: str
        :return: Route function which makes use of Nemo context (such as menu informations)
        :rtype: function
        """
        if instance:
            return lambda **kwargs: self.route(getattr(instance, name), **kwargs)
        else:
            return lambda **kwargs: self.route(getattr(self, name), **kwargs)

    def render(self, template, **kwargs):
        """ Render a route template and adds information to this route.

        :param template: Template name.
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

        for plugin in self.__plugins_render_views__:
            kwargs.update(plugin.render(**kwargs))

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
            plugin.register_nemo(self)

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
    def default_prevnext(passage, callback):
        """ Default deliver of prevnext informations

        :param passage: Passage for which to get previous and following reference
        :type passage: MyCapytains.resources.texts.api.Passage
        :param callback: Function to retrieve those information
        :type callback: function

        :return: Tuple representing previous and following reference
        :rtype: (str, str)
        """
        previous, following = passage.prev, passage.next

        if previous is None and following is None:
            previous, following = callback()

        if previous is not None:
            previous = str(previous.reference)
        if following is not None:
            following = str(following.reference)
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

        return str(item.urn.__getattribute__([
            "", "urn_namespace", "namespace", "textgroup", "work", "version", "reference"
        ][part_of_urn]).lower()) == query.lower().strip()


def _plugin_endpoint_rename(fn_name, instance):
    """ Rename endpoint function name to avoid conflict when namespacing is set to true

    :param fn_name: Name of the route function
    :param instance: Instance bound to the function
    :return: Name of the new namespaced function name
    """

    if instance and instance.namespaced:
        fn_name = "r_{0}_{1}".format(instance.name, fn_name[2:])
    return fn_name


def cmd():
    import argparse
    parser = argparse.ArgumentParser(description='Capitains Nemo CTS UI')
    parser.add_argument('endpoint', metavar='endpoint', type=str,
                       help='CTS API Endpoint')
    parser.add_argument('--port', type=int, default=8000,
                       help='Port to use for the HTTP Server')
    parser.add_argument('--host', type=str, default="127.0.0.1",
                       help='Host to use for the HTTP Server')
    parser.add_argument('--inventory', type=str, default=None,
                       help='Inventory to request from the endpoint')
    parser.add_argument('--css', type=str, default=None, nargs='*',
                       help='Full path to secondary css file')
    parser.add_argument('--groupby', type=int, default=25,
                       help='Number of passage to group in the deepest level of the hierarchy')
    parser.add_argument('--debug', action="store_true", default=False, help="Set-up the application for debugging")

    args = parser.parse_args()

    if args.endpoint:
        app = Flask(
            __name__
        )
        # We set up Nemo
        nemo = Nemo(
            app=app,
            name="nemo",
            base_url="",
            css=args.css,
            inventory=args.inventory,
            api_url=args.endpoint,
            chunker={"default": lambda x, y: Nemo.level_grouper(x, y, groupby=args.groupby)}
        )

        # We run the app
        app.debug = args.debug
        app.run(port=args.port, host=args.host)

if __name__ == "__main__":
    cmd()
