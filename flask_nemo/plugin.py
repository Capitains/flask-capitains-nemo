# -*- coding: utf-8 -*-

from copy import deepcopy as copy
from flask_nemo.common import resource_qualifier, ASSETS_STRUCTURE


class PluginPrototype(object):
    """ Prototype for Nemo Plugins

    :param name: Name of the instance of the plugins. Defaults to the class name (Default : Plugin's class name)
    :param namespacing: Add namespace to route to avoid overwriting (Default : False)

    :cvar ROUTES: Routes represents the routes to be added to the Nemo instance. They take the form of a 3-tuple such as `("/read/<collection>", "r_collection", ["GET"])`
    :type ROUTES: list
    :cvar TEMPLATES: Dictionaries of template namespaces and directory to retrieve templates in given namespace
    :type TEMPLATES: dict
    :cvar FILTERS: List of filters to register. Naming convention is f_doSomething
    :type FILTERS: list
    :cvar HAS_AUGMENT_RENDER: Enables post-processing in view rendering function Nemo().render(template, **kwargs)
    :type HAS_AUGMENT_RENDER: bool
    :cvar CLEAR_ROUTES: Removes original nemo routes
    :type CLEAR_ROUTES: bool
    :cvar CLEAR_ASSETS: Removes original nemo secondary assets
    :type CLEAR_ASSETS: bool
    :cvar STATIC_FOLDER: Overwrite Nemo default statics folder
    :type STATIC_FOLDER: str
    :cvar CSS: List of CSS resources to link in and give access to if local
    :type CSS: [css]
    :cvar JS: List of JS resources to link in and give access to if local
    :type JS: [str]
    :cvar STATIC: List of static resources (images for example) to give access to
    :type STATIC: [str]

    :ivar assets: Dictionary of assets, with each key (css, js and static) being list of resources
    :type assets: dict(str:[str])
    :ivar augment: If true, means that the plugin has a render method which needs to be called upon rendering the view
    :type augment: bool
    :ivar clear_routes: If true, means that the plugin requires Nemo original routes to be removed
    :type clear_routes: bool
    :ivar clear_assets: If true, means that the plugin required Nemo original assets to be removed
    :type clear_assets: bool
    :ivar name: Name of the plugin instance
    :type name: str
    :ivar static_folder: Path to the plugin own static_folder to be used instead of the Nemo default one
    :type static_folder: str
    :ivar namespaced: Indicate if the plugin is namespaced or not
    :type namespaced: bool
    :ivar routes: List of routes where the first member is a flask URL template, the second a method name, and the third a list of accepted Methods
    :type routes: [(str, str, [str])]
    :ivar filters: List of filters method names to be registered in Nemo
    :type filters: [str]
    :ivar templates: Dictionary of namespace and target directory to resolve templates name
    :type templates: {str:str}
    :ivar nemo: Nemo instance
    :type nemo: flask_ext.Nemo

    :Example:
    .. code-block:: python

        ROUTES = [
            # (Path like flask, Name of the function (convention is r_*), List of Http Methods)
            ("/read/<collection>/<textgroup>/<work>/<version>/<passage_identifier>/<visavis>", "r_double", ["GET"])
        ]

    :ivar name: Name of the plugin instance

    """
    ROUTES = []
    TEMPLATES = {}
    FILTERS = []
    HAS_AUGMENT_RENDER = False
    CLEAR_ROUTES = False
    CLEAR_ASSETS = False
    CSS = []
    STATICS = []
    JS = []
    STATIC_FOLDER = None

    def __init__(self, name=None, namespacing=False, *args, **kwargs):
        self.__nemo__ = None
        self.__instance_name__ = name
        if not name:
            self.__instance_name__ = type(self).__name__

        self.__clear_routes__ = copy(type(self).CLEAR_ROUTES)
        self.__clear_assets__ = copy(type(self).CLEAR_ASSETS)
        self.__static_folder__ = copy(type(self).STATIC_FOLDER)
        self.__routes__ = copy(type(self).ROUTES)
        self.__filters__ = copy(type(self).FILTERS)
        self.__templates__ = copy(type(self).TEMPLATES)
        self.__augment__ = copy(type(self).HAS_AUGMENT_RENDER)
        self.__namespaced__ = namespacing

        if namespacing:
            for i in range(0, len(self.__routes__)):
                self.__routes__[i] = tuple(
                    ["/{0}{1}".format(self.name, self.__routes__[i][0])] + list(self.__routes__[i])[1:]
                )

            for i in range(0, len(self.__filters__)):
                self.__filters__[i] = "f_{}_{}".format(self.name, self.__filters__[i][2:])

        self.__assets__ = copy(ASSETS_STRUCTURE)
        for css in type(self).CSS:
            key, value = resource_qualifier(css)
            self.__assets__["css"][key] = value
        for js in type(self).JS:
            key, value = resource_qualifier(js)
            self.__assets__["js"][key] = value
        for static in type(self).STATICS:
            key, value = resource_qualifier(static)
            self.__assets__["static"][key] = value

    def register_nemo(self, nemo=None):
        """ Register Nemo on to the plugin instance

        :param nemo: Instance of Nemo
        """
        self.__nemo__ = nemo

    @property
    def assets(self):
        return self.__assets__

    @property
    def augment(self):
        return self.__augment__

    @property
    def clear_routes(self):
        return self.__clear_routes__

    @property
    def clear_assets(self):
        return self.__clear_assets__

    @property
    def name(self):
        return self.__instance_name__

    @property
    def static_folder(self):
        return self.__static_folder__

    @property
    def namespaced(self):
        return self.__namespaced__

    @property
    def routes(self):
        return self.__routes__

    @property
    def filters(self):
        return self.__filters__

    @property
    def templates(self):
        return self.__templates__

    @property
    def nemo(self):
        return self.__nemo__

    def render(self, **kwargs):
        """ View Rendering function that gets triggered before nemo renders the resources and adds informations to \
        pass to the templates

        :param kwargs: Dictionary of arguments to pass to the template
        :return: Dictionary of arguments to pass to the template
        """
        return kwargs

