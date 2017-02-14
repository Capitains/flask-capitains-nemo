# -*- coding: utf-8 -*-

from flask_nemo.plugin import PluginPrototype
from flask_nemo.filters import f_slugify
from pkg_resources import resource_filename


class Breadcrumb(PluginPrototype):
    """
        The Breadcrumb plugin is enabled by default in Nemo.
        It can be overwritten or removed. It simply adds a breadcrumb

    """
    HAS_AUGMENT_RENDER = True
    TEMPLATES = {"main": resource_filename("flask_nemo", "data/templates_plugins/breadcrumb")}

    def render(self, **kwargs):
        """ Make breadcrumbs for a route

        :param kwargs: dictionary of named arguments used to construct the view
        :type kwargs: dict
        :return: List of dict items the view can use to construct the link.
        :rtype: {str: list({ "link": str, "title", str, "args", dict})}
        """
        breadcrumbs = []
        # this is the list of items we want to accumulate in the breadcrumb trail.
        # item[0] is the key into the kwargs["url"] object and item[1] is the  name of the route
        # setting a route name to None means that it's needed to construct the route of the next item in the list
        # but shouldn't be included in the list itself (this is currently the case for work --
        # at some point we probably should include work in the navigation)
        breadcrumbs = []
        if "collections" in kwargs:
            breadcrumbs = [{
                "title": "Text Collections",
                "link": ".r_collections",
                "args": {}
            }]

            if "parents" in kwargs["collections"]:
                breadcrumbs += [
                        {
                            "title": parent["label"],
                            "link": ".r_collection_semantic",
                            "args": {
                                "objectId": parent["id"],
                                "semantic": f_slugify(parent["label"]),
                            },
                        }
                        for parent in kwargs["collections"]["parents"]
                  ][::-1]

            if "current" in kwargs["collections"]:
                breadcrumbs.append({
                    "title": kwargs["collections"]["current"]["label"],
                    "link": None,
                    "args": {}
                })

        # don't link the last item in the trail
        if len(breadcrumbs) > 0:
            breadcrumbs[-1]["link"] = None

        return {"breadcrumbs": breadcrumbs}
