"""
    Test the Nautilus endpoint with the app.test_client
"""


from unittest import TestCase
from tests.test_resources import NautilusDummy
from flask_nemo import Nemo
from flask_nemo.plugin import PluginPrototype
from flask_nemo.chunker import level_grouper
from flask import Flask, jsonify
from flask_caching import Cache
from random import randint
from MyCapytain.errors import UnknownCollection


class NemoTestBrowse(TestCase):
    """ Test Suite for Nemo
    """
    def make_nemo(self, app, **kwargs):
        return Nemo(app=app, **kwargs)

    def setUp(self):
        app = Flask("Nemo")
        app.debug = True
        self.nemo = self.make_nemo(
            app=app,
            base_url="",
            resolver=NautilusDummy,
            chunker={"default": lambda x, y: level_grouper(x, y, groupby=30)},
            css=[
                "./tests/test_data/empty.css",
                "//foo.bar/test.css",
                "http://bar.foo/test.css",
                "https://super.secure/mypasswordin.css"
            ],
            js=[
                "./tests/test_data/empty.js",
                "//foo.bar/test.js",
                "http://bar.foo/test.js",
                "https://super.secure/mypasswordin.js"
            ],
        )

        self.client = app.test_client()

    def test_default_template_assets(self):
        """ Test that the index menu is correctly built """
        query_data = str(self.client.get("/").data)

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

    def test_serving_secondary_assets(self):
        """ Ensure secondary assets are served
        """
        query_data = str(self.client.get("/assets/nemo.secondary/css/empty.css").data)
        self.assertIn(".empty {", query_data, "Local CSS File should be read")

        query_data = str(self.client.get("/assets/nemo.secondary/js/empty.js").data)
        self.assertIn("var empty = True;", query_data, "Local JS File should be read")

    def test_serving_primary_assets(self):
        """ Ensure primary assets are served
        """
        query_data = str(self.client.get("/assets/nemo/css/theme.min.css").data)
        self.assertIn("body, html", query_data, "Primary Assets should be served")

    def test_serving_overwritten_primary_assets(self):
        """ Ensure primary assets are served
        """
        app = Flask("Nemo")
        app.debug = True
        nemo = self.make_nemo(
            app=app,
            base_url="",
            resolver=NautilusDummy,
            chunker={"default": lambda x, y: level_grouper(x, y, groupby=30)},
            static_folder="tests/test_data/assets"
        )

        client = app.test_client()
        query_data = str(client.get("/assets/nemo/fake.png").data)
        self.assertIn("fake", query_data, "Primary Assets should be served when overwritting")

        self.assertEqual(
            client.get("/assets/nemo/css/theme.min.css").status_code, 404,
            "Old Primary Assets should not be served when overwritting"
        )

    def test_index_menu(self):
        """ Test that the index menu is correctly built """
        query_data = str(self.client.get("/").data)
        self.assertIn(
            '<a href="/collections/urn:perseus:farsiLit/farsi">Farsi</a>', query_data,
            "App should have link to farsiLit through local repository-endpoint object"
        )
        self.assertIn(
            '<a href="/collections/urn:perseus:latinLit/classical-latin">Classical Latin</a>', query_data,
            "App should have link to latinLit through local repository-endpoint object"
        )

    def test_namespace_page(self):
        """ Test that the namespace page has correct informations : """
        query_data = self.client.get("/collections/urn:perseus:farsiLit").data.decode()
        self.assertIn(
            '<a href="/collections/urn:perseus:farsiLit/farsi">Farsi</a>', query_data,
            "App should have link to farsiLit through local repository-endpoint object"
        )
        self.assertRegex(
            query_data,
            r'href="/collections/urn:cts:farsiLit:hafez/[\w\-]+">Browse \(1\)</a>',
            "App should have link to authors through local repository-endpoint object"
        )

    def test_author_page(self):
        """ Test that author page contains what is relevant : editions and translations """
        query_data = self.client.get("/collections/urn:cts:latinLit:phi1294").data.decode()
        self.assertIn(
            '<a href="/collections/urn:perseus:farsiLit/farsi">Farsi</a>', query_data,
            "App should have link to farsiLit through local repository-endpoint object"
        )
        self.assertRegex(
            query_data,
            r'href="/collections/urn:cts:latinLit:phi1294.phi002/[\w\-]+">Browse \(1\)</a>',
            "App should have link to the text object"
        )

    def test_author_page_more_count(self):
        """ Test that the namespace page has correct informations : """
        query_data = self.client.get("/collections/urn:cts:farsiLit:hafez").data.decode()
        self.assertIn(
            '<a href="/collections/urn:perseus:farsiLit/farsi">Farsi</a>', query_data,
            "App should have link to farsiLit through local repository-endpoint object"
        )
        self.assertRegex(
            query_data,
            r'href="/collections/urn:cts:farsiLit:hafez.divan/[\w\-]+">Browse \(3\)</a>',
            "App should have link to authors through local repository-endpoint object"
        )

    def test_text_page(self):
        """ Test that text page contains what is relevant : passages"""
        query_data = self.client.get("/text/urn:cts:latinLit:phi1294.phi002.perseus-lat2/references").data.decode()
        self.assertIn(
            '<a href="/collections/urn:perseus:farsiLit/farsi">Farsi</a>', query_data,
            "App should have link to farsiLit through local repository-endpoint object"
        )
        self.assertIn(
            '<a href="/text/urn:cts:latinLit:phi1294.phi002.perseus-lat2/passage/1.pr.1-1.pr.22">', query_data,
            "App should have link to farsiLit through local repository-endpoint object"
        )

    def test_passage_page(self):
        """ Test that passage page contains what is relevant : text and next passages"""
        query_data = str(self.client.get("/text/urn:cts:latinLit:phi1294.phi002.perseus-lat2/passage/1.pr.1-1.pr.22").data)
        self.assertIn(
            'Marsus, sic Pedo, sic Gaetulicus, sic quicumque perlegi', query_data,
            "Text should be visible"
        )
        self.assertIn(
            'href="/text/urn:cts:latinLit:phi1294.phi002.perseus-lat2/passage/1.1.1-1.1.6"', query_data,
            "App should have link to the next passage"
        )

    def test_json_route(self):
        """ Test that adding routes to Nemo instance (without plugin) which output json works
        """
        import json
        test_data = {"SomeDict": "IsGood"}

        class NemoJson(Nemo):
            ROUTES = Nemo.ROUTES + [("/getJson", "r_json", ["GET"])]

            def r_json(self):
                """ Route with no templates should return none as first value
                """
                return jsonify(test_data)

        app = Flask("Nemo")
        app.debug = True
        nemo = NemoJson(app=app, base_url="", resolver=NautilusDummy)
        client = app.test_client()
        query_data = json.loads(client.get("/getJson").data.decode('utf8'))

        self.assertEqual(
            query_data, test_data,
            "Original Dict and Decoded Output JSON should be equal"
        )

    def test_breadcrumb(self):
        """ Ensure breadcrumb is bydefault loaded
        """
        query_data = str(self.client.get("/collections/urn:cts:latinLit:phi1294").data)
        self.assertIn(
            '<li class="breadcrumb-item"><a href="/collections/urn:perseus:latinLit/classical-latin">Classical Latin</a></li>', query_data,
            "Breadcrumb should be visible"
        )
        self.assertIn(
            '<li class="breadcrumb-item active">Martial</li>', query_data,
            "Breadcrumb should be visible"
        )

    def test_no_default_breadcrumb(self):
        """ Ensure breadcrumb is bydefault loaded
        """

        app = Flask("Nemo")
        app.debug = True
        nemo = self.make_nemo(app=app, base_url="", resolver=NautilusDummy, original_breadcrumb=False)
        client = app.test_client()
        query_data = str(client.get("/collections/urn:cts:latinLit:phi1294").data)
        self.assertNotIn(
            '<ol class="breadcrumb">', query_data,
            "Breadcrumb should not be visible"
        )
        self.assertNotIn(
            '<li class="active">Martial</li>', query_data,
            "Breadcrumb should not be visible"
        )

    def test_main_collections(self):
        """ Test the main collection (Inventory) display
        """
        query_data = self.client.get("/collections").data.decode()
        self.assertRegex(
            query_data, r'Classical Latin<br />\s*<a class="card-link" href="/collections/urn:perseus:latinLit',
            "Link to classical latin main collection should be found"
        )
        self.assertRegex(
            query_data, r'Farsi<br />\s*<a class="card-link" href="/collections/urn:perseus:farsiLit',
            "Link to farsi main collection should be found"
        )
        self.assertRegex(
            query_data, r'Ancient Greek<br />\s*<a class="card-link" href="/collections/urn:perseus:greekLit',
            "Link to farsi main collection should be found"
        )

    def test_semantic_collections(self):
        """ Test the main collection (Inventory) display
        """
        query_data = self.client.get("/collections/urn:perseus:latinLit/something").data.decode()
        query_data_2 = self.client.get("/collections/urn:perseus:latinLit").data.decode()
        self.assertEqual(
            query_data, query_data_2, "Semantic has no effect on output"
        )

    def test_i18n_metadata(self):
        """ Ensure metadata are i18n according to requested headers
        """
        tests = [
            ("en_US", "I am English."),
            ("fr_CA", "Je suis francais."),
            ("fr_FR", "Je suis francais."),
            ("la", "Ego romanus sum."),
            ("de_DE", "Ich bin Deutsch.")
        ]
        ran = 0
        for lang, text in tests:
            data = self.client.get(
                "/collections/urn:cts:latinLit:phi1318.phi001",
                headers=[("Accept-Language", lang)]
            ).data.decode()
            self.assertIn(
                text, data
            )
            ran += 1
        self.assertEqual(ran, len(tests), "There should be as much ran tests as there is tests")

    def test_first_passage(self):
        tests = 0
        uris = [
            ("urn:cts:latinLit:phi1294.phi002.perseus-lat2", "1.pr.1-1.pr.20"),
            ("urn:cts:latinLit:phi1318.phi001.perseus-unk2", "8.pr.1-8.pr.20"),
            ("urn:cts:farsiLit:hafez.divan.perseus-ger1", "1.1.1.1-1.1.1.4")
        ]
        app = Flask("Nemo")
        _ = self.make_nemo(
            app=app,
            base_url="",
            resolver=NautilusDummy,
            original_breadcrumb=False,
            chunker={"default": lambda x, y: level_grouper(x, y, groupby=20)}
        )
        client = app.test_client()
        for oId, psg in uris:
            r = client.get("/text/{}/passage".format(oId))
            self.assertIn(
                "/text/{}/passage/{}/".format(oId, psg), r.location,
                "check that the path changed"
            )
            tests += 1
        self.assertEqual(tests, len(uris), "There should be as much ran tests as there is tests")

    def test_no_siblings_is_ok(self):
        """ Test that passage page contains what is relevant : text and next passages"""
        query_data = self.client.get("/text/urn:cts:latinLit:stoa0329c.stoa001.opp-lat1/passage/1-8").data.decode()
        self.assertIn(
            'et ibi est lapis ille', query_data,
            "Text should be visible"
        )

    def test_browse_work_identifier_on_passage_route(self):
        """ Particular case : CTS Identifiers should allow for having a work level identifier and a passage. Nemo should reroute this kind of URI
        See https://github.com/Capitains/flask-capitains-nemo/issues/106
        """
        right_response = self.client.get("/text/urn:cts:latinLit:stoa0329c.stoa001.opp-lat1/passage/1-8").data.decode()
        rerouted = self.client.get("/text/urn:cts:latinLit:stoa0329c.stoa001/passage/1-8", follow_redirects=True).data.decode()
        self.assertEqual(right_response, rerouted, "Content of reroute should be the content of right response")

        with self.assertRaises(UnknownCollection):
            failing = self.client.get("/text/urn:cts:latinLit:stoa0329c.stoa008888/passage/1-8", follow_redirects=True)

    def test_cache_options(self):
        class ReplaceTemplate(PluginPrototype):
            TEMPLATES = {
                "main": "./tests/test_data/cache_templates/main"
            }
        app = Flask("Nemo")
        _ = self.make_nemo(
            app=app,
            base_url="",
            resolver=NautilusDummy,
            chunker={"default": lambda x, y: level_grouper(x, y, groupby=30)},
            plugins=[ReplaceTemplate("ThisIsMyName")]
        )
        app.debug = True
        client = app.test_client()
        self.assertIn(
            '<title>I am A CONTAINER ! Isn\'t it sweet !</title>', client.get("/").data.decode(),
            "There should be the new title"
        )
        self.assertIn(
            "I AM NO LOGO", client.get("/").data.decode(),
            "There should be no logo"
        )

    def test_caching_plugin_route(self):
        class ReplaceTemplate(PluginPrototype):
            ROUTES = [
                ("/square/<int:x>", "r_square", ["GET"]),
                ("/random", "r_random", ["GET"])
            ]
            CACHED = ["r_square", "r_random"]

            def r_square(self, x):
                return "Square : %s" % (x*x)

            def r_random(self):
                return "%s" % randint(0, 900000)

        app = Flask("Nemo")
        _ = self.make_nemo(
            app=app,
            base_url="",
            resolver=NautilusDummy,
            chunker={"default": lambda x, y: level_grouper(x, y, groupby=30)},
            plugins=[ReplaceTemplate("ThisIsMyName")]
        )
        app.debug = True
        client = app.test_client()
        self.assertIn(
            'Square : 100', client.get("/square/10").data.decode(),
            "There should square "
        )
        sets = [client.get("/random").data.decode() for _ in range(0, 50)]
        if isinstance(self, NemoTestBrowseWithCache):
            self.assertEqual(
                len(set(sets)), 1, "Random has been cached and is not recomputed"
            )
        else:
            self.assertGreater(
                len(set(sets)), 1, "Random has been cached and is not recomputed"
            )


class NemoTestBrowseWithCache(NemoTestBrowse):
    """ Do the same tests bu with a cache object """
    def make_nemo(self, app, **kwargs):
        return Nemo(app=app, cache=Cache(app=app, config={"CACHE_TYPE": "simple"}), **kwargs)
