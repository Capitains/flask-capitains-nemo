from unittest import TestCase
from flask_nemo.plugin import PluginPrototype
from tests.test_plugin.test_resources import make_client


class PluginAssets(PluginPrototype):
    CSS = [
        "./tests/test_data/empty.css",
        "//foo.bar/test.css",
        "http://bar.foo/test.css",
        "https://super.secure/mypasswordin.css"
    ]
    JS = [
        "./tests/test_data/empty.js",
        "//foo.bar/test.js",
        "http://bar.foo/test.js",
        "https://super.secure/mypasswordin.js"
    ]
    STATICS = [
        "./tests/test_data/assets/fake.png"
    ]


class PluginClearAssets(PluginAssets):
    CLEAR_ASSETS = True
    STATIC_FOLDER = "tests/test_data/plugin_assets"


class TestPluginAssets(TestCase):
    """ Test plugin implementation of filters
    """

    def test_plugin_assets_in_templates(self):
        client = make_client(PluginAssets(name="One"))
        query_data = str(client.get("/").data)

        jss = [
            "//foo.bar/test.js",
            "http://bar.foo/test.js",
            "https://super.secure/mypasswordin.js"
        ]
        assert_length_js = len(jss)
        for js in jss:
            self.assertIn(
                '<script src="{0}"></script>'.format(js), query_data,
                "Templates should correctly link external js"
            )
            assert_length_js -= 1
        self.assertEqual(assert_length_js, 0, "All js file should have been checked")

        csss = [
            "//foo.bar/test.css",
            "http://bar.foo/test.css",
            "https://super.secure/mypasswordin.css"
        ]
        assert_length_js = len(csss)
        for css in csss:
            self.assertIn(
                '<link rel="stylesheet" href="{0}">'.format(css), query_data,
                "Templates should correctly link external css"
            )
            assert_length_js -= 1
        self.assertEqual(assert_length_js, 0, "All css files should have been checked")

        self.assertIn(
            '<link rel="stylesheet" href="/assets/nemo.secondary/css/empty.css">', query_data,
            "Secondary Internal CSS should be linked"
        )
        self.assertIn(
            '<script src="/assets/nemo.secondary/js/empty.js"></script>', query_data,
            "Secondary Internal JS should be retrieved"
        )

    def test_check_original_status(self):
        """ This test just check that by default, the value we use are not in the directory
        """
        client = make_client()
        query_data = str(client.get("/").data)
        self.assertNotIn(
            '<script src="//foo.bar/test.js"></script>', query_data,
            "Templates should not have it by default"
        )

    def test_serving_assets(self):
        """ Ensure plugins assets are served
        """
        client = make_client(PluginAssets())
        query_data = str(client.get("/assets/nemo.secondary/css/empty.css").data)
        self.assertIn(".empty {", query_data, "Local CSS File should be read")

        query_data = str(client.get("/assets/nemo.secondary/js/empty.js").data)
        self.assertIn("var empty = True;", query_data, "Local JS File should be read")

        query_data = str(client.get("/assets/nemo.secondary/static/fake.png").data)
        self.assertIn("fake", query_data, "Local Static should be read")

    def test_clearing_assets(self):
        client = make_client(PluginClearAssets())
        query_data = str(client.get("/assets/nemo.secondary/css/empty.css").data)
        self.assertIn(".empty {", query_data, "Local Secondary CSS File should be read")

        query_data = str(client.get("/assets/nemo.secondary/js/empty.js").data)
        self.assertIn("var empty = True;", query_data, "Local Secondary JS File should be read")

        query_data = str(client.get("/assets/nemo/plugin.css").data)
        self.assertIn(".pluginstuff", query_data, "Primary Assets should be served when overwritting")

        self.assertEqual(
            client.get("/assets/nemo/css/theme.min.css").status_code, 404,
            "Old Primary Assets should not be served when overwritting"
        )

    def test_prevent_clearing_assets(self):
        client = make_client(PluginClearAssets(), prevent_plugin_clearing_assets=True)
        query_data = str(client.get("/assets/nemo/css/theme.min.css").data)
        self.assertIn("body, html", query_data, "Nemo Primary Assets should be not served when prevent is on")

        self.assertEqual(
            client.get("/assets/nemo/plugin.css").status_code, 404,
            "Plugin Primary Assets should not be served when prevent is on"
        )
