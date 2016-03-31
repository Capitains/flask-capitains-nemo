"""
    Test the Nautilus endpoint with the app.test_client
"""


from unittest import TestCase
from .resources import NautilusDummy
from flask_nemo import Nemo
from flask import Flask


class NemoTestRoutes(TestCase):
    """ Test Suite for Nemo
    """
    def setUp(self):
        app = Flask("Nemo")
        nemo = Nemo(
            app=app,
            base_url="",
            endpoint=NautilusDummy,
            chunker={"default": lambda x, y: Nemo.level_grouper(x, y, groupby=30)}
        )
        nemo.register_routes()
        nemo.register_filters()

        self.client = app.test_client()

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