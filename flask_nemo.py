# -*- coding: utf-8 -*-
"""
    Capitains Nemo
    ====

    Extensions for Flask to propose a Nemo extensions
"""

__version__ = "0.0.1"

from flask import request
import MyCapytain.endpoints.cts5
import MyCapytain.resources.texts.tei
import MyCapytain.resources.inventory
import requests_cache


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
    :type base_url: int
    """

    def __init__(self, app=None, api_url="/", base_url="/nemo", cache=None, expire=3600):
        __doc__ = Nemo.__doc__
        self.base_url = base_url
        self.api_url = api_url
        self.endpoint = MyCapytain.endpoints.cts5.CTS(self.api_url)

        if app is not None:
            self.app = app
            self.init_app(self.app)
        else:
            self.app = None

        self.api_url = ""
        self.api_inventory = None
        self.cache = None
        if cache is not None:
            self.__register_cache(cache, expire)

    def __register_cache(self, sqlite_path, expire):
        """ Set up a request cache

        :param sqlite_path:
        :return:
        """
        self.cache = requests_cache.install_cache(
            sqlite_path,
            backend="sqlite",
            expire_after=expire
        )

    def init_app(self, app):
        self.api_url = app.config['CTS_API_URL']
        if "CTS_API_INVENTORY" in app.config:
            self.api_inventory = app.config['CTS_API_INVENTORY']

    def register(self):
        pass

    def get_inventory(self):
        reply = self.endpoint.getCapabilities()
        return MyCapytain.resources.inventory.TextInventory(resource=reply)
