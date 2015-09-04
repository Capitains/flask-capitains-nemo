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
from MyCapytain.resources.proto.inventory import Resource as InventoryProto
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
        """ Request the api endpoint to retrieve information about the inventory

        :return: The text inventory
        :rtype: MyCapytain.resources.inventory.TextInventory
        """
        reply = self.endpoint.getCapabilities(inventory=self.api_inventory)
        return MyCapytain.resources.inventory.TextInventory(resource=reply)

    def get_collections(self):
        """ Filter inventory and make a list of available collections

        :return: A set of CTS Namespaces
        :rtype: set(str)
        """
        urns = set([textgroup.urn["cts_namespace"] for textgroup in self.get_inventory().textgroups])
        return urns

    def get_textgroups(self, collection=None):
        """ Retrieve textgroups

        :param collection: Collection to use for filtering the textgroups
        :type collection: str
        :return: List of textgroup filtered by collection
        :rtype: [MyCapytain.resources.inventory.Textgroup]
        """
        inventory = self.get_inventory()
        if collection is not None:
            return Nemo.map_urns(inventory, collection, 2, "textgroups")
        return list(inventory.textgroups.values())

    def get_works(self, collection_urn=None, textgroup_urn=None):
        """ Retrieve works

        :param collection: Collection to use for filtering the textgroups
        :type collection: str
        :param textgroup: Collection to use for filtering the works
        :type collection: str
        :return: List of work filtered by collection
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
        """ Retrieve works

        :param collection: Collection to use for filtering the textgroups
        :type collection: str
        :param textgroup: Collection to use for filtering the works
        :type collection: str
        :return: List of work filtered by collection
        :rtype: [MyCapytain.resources.inventory.Work]
        """
        if collection_urn is not None and textgroup_urn is not None and work_urn is not None:
            work = list(
                filter(lambda x: Nemo.filter_urn(x, 4, work_urn), self.get_works(collection_urn, textgroup_urn))
            )
            if len(work) == 1:
                return work[0].texts.values()
            else:
                return []
        elif collection_urn is None and textgroup_urn is None and work_urn is None:
            return [
                text
                for textgroup in self.get_inventory().textgroups.values()
                for work in textgroup.works.values()
                for text in work.texts.values()
            ]
        else:
            raise ValueError("Get_Work takes either two None value or two set up value")


    @staticmethod
    def map_urns(items, query, part_of_urn=1, attr="textgroups"):
        """ Small function to map urns to filter out a list of items or on a parent item

        :param items: Inventory object
        :type items: ?
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

