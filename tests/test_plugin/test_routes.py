from unittest import TestCase
from flask_nemo.plugin import PluginPrototype
from .resources import make_client
import werkzeug.routing
from copy import deepcopy as copy


class PluginRoute(PluginPrototype):
    ROUTES = [
        ("/read/<collection>/<textgroup>/<work>/<version>/<passage_identifier>/<visavis>", "r_double", ["GET"])
    ]

    TEMPLATES = {
        "plugin_route": "tests/test_data/plugin_templates_main/plugin"
    }
    ROUTE_TEMPLATES = {
        "r_double": "plugin_route::r_double.html"
    }
    HAS_AUGMENT_RENDER = True

    def r_double(self, collection, textgroup, work, version, passage_identifier, visavis):
        args = self.nemo.r_passage(collection, textgroup, work, version, passage_identifier)
        # Call with other identifiers and add "visavis_" front of the argument
        args.update({
            "visavis_{0}".format(key): value for key, value in self.nemo.r_passage(
                collection, textgroup, work, visavis, passage_identifier
            ).items()
        })
        args["template"] = type(self).ROUTE_TEMPLATES["r_double"]
        return args

    def render(self, **kwargs):
        kwargs["lang"] = "fre"
        return kwargs


class PluginClearRoute(PluginRoute):
    CLEAR_ROUTES = True

    ROUTE_TEMPLATES = {
        "r_double": "plugin_cleared_route::r_double.html"
    }
    TEMPLATES = {
        "plugin_cleared_route": "tests/test_data/plugin_templates_main/plugin",
        "main": "tests/test_data/plugin_templates_main/main"
    }


class TestPluginRoutes(TestCase):
    """ Test plugin implementation of filters
    """

    def setUp(self):
        self.plugin_normal = PluginRoute(name="normal")
        self.plugin_namespacing = PluginRoute(name="test", namespacing=True)
        self.plugin_autonamespacing = PluginRoute(namespacing=True)

    def test_page_works(self):
        """ Test that passage page contains what is relevant : text and next passages"""
        query_data = str(make_client(self.plugin_normal).get("/read/farsiLit/hafez/divan/perseus-eng1/1.1/perseus-ger1").data)
        self.assertIn(
            'Ho ! Saki, pass around and offer the bowl (of love for God)', query_data,
            "English text should be displayed"
        )
        self.assertIn(
            'Finstere Schatten der Nacht!', query_data,
            "German text should be displayed"
        )

    def test_plugin_change_render(self):
        """ Check that the augmenting render function works and is correctly plugged
        """
        query_data = str(make_client(self.plugin_normal).get("/read/farsiLit/hafez").data)
        self.assertIn(
            'Perse', query_data,
            "French Translation should be displayed"
        )

    def test_plugin_clear(self):
        """ Test that passage page contains what is relevant : text and next passages """
        plugin = PluginClearRoute(name="normal")
        client = make_client(plugin)

        req = client.get("/read/farsiLit/hafez/divan/perseus-eng1/1.1")
        self.assertEqual(
            404, req.status_code,
            "Original routes should not exist anymore"
        )
        query_data = str(client.get("/read/farsiLit/hafez/divan/perseus-eng1/1.1/perseus-ger1").data)
        self.assertIn(
            'Ho ! Saki, pass around and offer the bowl (of love for God)', query_data,
            "English text should be displayed"
        )
        self.assertIn(
            'Finstere Schatten der Nacht!', query_data,
            "German text should be displayed"
        )

    def test_plugin_clear_with_error(self):
        """
            When clearing routes, we need to ensure Flask fails to run
            if there is still some other routes call
        """
        class TempPlugin(PluginClearRoute):
            TEMPLATES = copy(PluginRoute.TEMPLATES)
            ROUTE_TEMPLATES = copy(PluginRoute.ROUTE_TEMPLATES)

        plugin = TempPlugin(name="normal")
        client = make_client(plugin)

        with self.assertRaises(
                werkzeug.routing.BuildError,
                msg="Call to other routes in templates should fail to build"
        ):
            client.get("/read/farsiLit/hafez/divan/perseus-eng1/1.1/perseus-ger1")

    def test_template_overwrite(self):
        """ Checks that overwriting original templates works
        """
        class PluginTemplate(PluginPrototype):
            TEMPLATES = {
                "main": "tests/test_data/plugin_templates_main/main"
            }
        client = make_client(PluginTemplate())
        query_data = str(client.get("/read/farsiLit/hafez/divan/perseus-eng1/1.1").data)
        self.assertIn(
            'I am A CONTAINER !', query_data,
            "Container should have been overwritten"
        )
        query_data = str(client.get("/read/farsiLit/hafez").data)
        self.assertIn(
            'I am A CONTAINER !', query_data,
            "Container should have been overwritten on a second page as well"
        )
