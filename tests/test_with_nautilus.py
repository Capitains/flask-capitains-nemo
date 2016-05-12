"""
    Test the Nautilus endpoint with the app.test_client
"""


from unittest import TestCase
from .resources import NautilusDummy
from flask_nemo import Nemo
from flask_nemo.chunker import level_grouper
from flask import Flask, jsonify


class NemoTestRoutes(TestCase):
    """ Test Suite for Nemo
    """
    def setUp(self):
        app = Flask("Nemo")
        app.debug = True
        nemo = Nemo(
            app=app,
            base_url="",
            retriever=NautilusDummy,
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
        nemo = Nemo(
            app=app,
            base_url="",
            retriever=NautilusDummy,
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
            '<a class="" href="/read/farsiLit">farsiLit</a>', query_data,
            "App should have link to farsiLit through local repository-endpoint object"
        )
        self.assertIn(
            '<a class="" href="/read/latinLit">Latin</a>', query_data,
            "App should have link to latinLit through local repository-endpoint object"
        )

    def test_namespace_page(self):
        """ Test that the namespace page has correct informations : """
        query_data = str(self.client.get("/read/latinLit").data)
        self.assertIn(
            '<a class="" href="/read/farsiLit">farsiLit</a>', query_data,
            "App should have link to farsiLit through local repository-endpoint object"
        )
        self.assertIn(
            '<li><a class="" href="/read/latinLit/phi1294">Martial</a></li>', query_data,
            "App should have link to authors through local repository-endpoint object"
        )

    def test_author_page(self):
        """ Test that author page contains what is relevant : editions and translations """
        query_data = str(self.client.get("/read/latinLit/phi1294").data)
        self.assertIn(
            '<a class="" href="/read/farsiLit">farsiLit</a>', query_data,
            "App should have link to farsiLit through local repository-endpoint object"
        )
        self.assertIn(
            '<a href="/read/latinLit/phi1294/phi002/perseus-lat2">', query_data,
            "App should have link to the text object"
        )

    def test_text_page(self):
        """ Test that text page contains what is relevant : passages"""
        query_data = str(self.client.get("/read/latinLit/phi1294/phi002/perseus-lat2").data)
        self.assertIn(
            '<a class="" href="/read/farsiLit">farsiLit</a>', query_data,
            "App should have link to farsiLit through local repository-endpoint object"
        )
        self.assertIn(
            '<a href="/read/latinLit/phi1294/phi002/perseus-lat2/1.pr.1-1.pr.22">', query_data,
            "App should have link to farsiLit through local repository-endpoint object"
        )

    def test_passage_page(self):
        """ Test that passage page contains what is relevant : text and next passages"""
        query_data = str(self.client.get("/read/latinLit/phi1294/phi002/perseus-lat2/1.pr.1-1.pr.22").data)
        self.assertIn(
            'Marsus, sic Pedo, sic Gaetulicus, sic quicumque perlegi', query_data,
            "Text should be visible"
        )
        self.assertIn(
            'href="/read/latinLit/phi1294/phi002/perseus-lat2/1.1.1-1.3.8"', query_data,
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
        nemo = NemoJson(app=app, base_url="", retriever=NautilusDummy)
        client = app.test_client()
        query_data = json.loads(client.get("/getJson").data.decode('utf8'))

        self.assertEqual(
            query_data, test_data,
            "Original Dict and Decoded Output JSON should be equal"
        )

    def test_breadcrumb(self):
        """ Ensure breadcrumb is bydefault loaded
        """
        query_data = str(self.client.get("/read/latinLit/phi1294").data)
        self.assertIn(
            '<li><a href="/read/latinLit">latinLit</a></li>', query_data,
            "Breadcrumb should be visible"
        )
        self.assertIn(
            '<li class="active">Martial</li>', query_data,
            "Breadcrumb should be visible"
        )

    def test_no_default_breadcrumb(self):
        """ Ensure breadcrumb is bydefault loaded
        """

        app = Flask("Nemo")
        app.debug = True
        nemo = Nemo(app=app, base_url="", retriever=NautilusDummy, original_breadcrumb=False)
        client = app.test_client()
        query_data = str(client.get("/read/latinLit/phi1294").data)
        self.assertNotIn(
            '<ol class="breadcrumb">', query_data,
            "Breadcrumb should not be visible"
        )
        self.assertNotIn(
            '<li class="active">Martial</li>', query_data,
            "Breadcrumb should not be visible"
        )
