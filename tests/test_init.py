"""
    Test for simple init parameters override
"""
from .resources import NemoResource, NautilusDummy
from flask_nemo import Nemo
from flask import Flask


class TestNemoInit(NemoResource):
    def test_init_app(self):
        """ Test that application initiation uses config parameters
        """
        app = Flask(__name__)
        app.config["CTS_API_URL"] = "http://localhost"
        app.config["CTS_API_INVENTORY"] = "annotsrc"
        self.nemo.init_app(app)

        self.assertEqual(self.nemo.api_inventory, "annotsrc")
        self.assertEqual(self.nemo.api_url, "http://localhost")
        self.assertEqual(self.nemo.app, app)

    def test_overwrite_urls(self):
        """ Check that routes can be added or modified
        """
        routes = [("/index.html", "r_index", ["GET"])] + Nemo.ROUTES[1:]
        app = Flask(__name__)
        nemo = Nemo(app=app, urls=routes)
        nemo.register()
        self.assertIn("flask_nemo", app.blueprints)

        rules = [(rule.rule, rule.endpoint) for rule in app.url_map.iter_rules()]
        self.assertIn("/nemo/index.html", [rule[0] for rule in rules])
        self.assertNotIn("/nemo/", [rule[0] for rule in rules])

    def test_static_url_path(self):
        """ Test that the extension static url path is changing when set up
        """
        app = Flask(__name__)
        nemo = Nemo(app=app, static_url_path="/assets/nemoOo")
        nemo.register()
        self.assertIn("flask_nemo", app.blueprints, "Nemo is a registered blueprint")

        rules = [(rule.rule, rule.endpoint) for rule in app.url_map.iter_rules()]
        self.assertIn("/nemo/assets/nemoOo/<path:filename>", [rule[0] for rule in rules])
        self.assertIn("/nemo/assets/nemoOo.secondary/<type>/<asset>", [rule[0] for rule in rules])

    def test_static_folder(self):
        """ Test the use of static fikder parameter to implement assets customization
        """
        app = Flask(__name__)
        nemo = Nemo(app=app, static_folder="/examples")
        nemo.register()

        self.assertEqual(nemo.static_folder, "/examples")
        self.assertEqual(nemo.blueprint.static_folder, "/examples")

    def test_template_folder(self):
        """ Test the parameter to set up a different template folder
        """
        app = Flask(__name__)
        nemo = Nemo(app=app, template_folder="/examples")
        nemo.register()

        self.assertEqual(nemo.template_folder, "/examples")
        self.assertEqual(nemo.blueprint.template_folder, "/examples")

    def test_other_endpoint(self):
        """ Test when an endpoint is set """
        nemo = Nemo(retriever=NautilusDummy)
        self.assertEqual(nemo.retriever, NautilusDummy, "Endpoint should be set through endpoint parameter")

        nemo = Nemo(api_url="http://foo.bar", retriever=NautilusDummy)
        self.assertEqual(nemo.retriever, NautilusDummy,
                         "Endpoint should be set through endpoint parameter, regardless of api_url")
        self.assertEqual(nemo.api_url, "http://foo.bar",
                         "api_urlshould be set through endpoint parameter, regardless of endpoint")
