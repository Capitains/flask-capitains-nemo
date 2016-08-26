# -*- coding: utf-8 -*-

from flask_nemo.plugin import PluginPrototype
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
        crumbtypes = [
            ["collection", ".r_collection"],
            ["textgroup", ".r_texts"],
            ["work", None],
            ["version", ".r_version"],
            ["passage_identifier", ".r_passage"]
        ]
        for idx, crumb_type in enumerate(crumbtypes):
            if kwargs["url"] and crumb_type[0] in kwargs["url"]:
                crumb = {}
                # what we want to display as the crumb title depends upon what it is
                # in the future, having a common display_name property on the model would be helpful to avoid
                # this logic here
                if crumb_type[0] == "textgroup":
                    # get the groupname of the current textgroup
                    item = list(filter(lambda textgroup: textgroup.urn.textgroup == kwargs["url"]["textgroup"], kwargs["textgroups"]))
                    crumb["title"] = item[0].metadata["groupname"][kwargs["lang"]]
                elif crumb_type[0] == "version":
                    # get the label of the current version
                    crumb["title"] = kwargs["version"].metadata["label"][kwargs["lang"]]
                else:
                    # for everything else, just use the value as metadata isn't applicable
                    crumb["title"] = kwargs["url"][crumb_type[0]]
                # iterate through the crumb types and pull together the args that lead up to this type
                # so that we can reconstruct the route to just this part of the breadcrumb trail
                crumb_args = {}
                iteridx = idx

                while iteridx >= 0:
                    crumb_args[crumbtypes[iteridx][0]] = kwargs["url"][crumbtypes[iteridx][0]]
                    iteridx -= 1

                crumb["link"] = crumb_type[1]
                crumb["args"] = crumb_args
                # skip items in the trail that are only used to construct others
                if crumb_type[1]:
                    breadcrumbs.append(crumb)

        # don't link the last item in the trail
        if len(breadcrumbs) > 0:
            breadcrumbs[-1]["link"] = None

        return {"breadcrumbs": breadcrumbs}
