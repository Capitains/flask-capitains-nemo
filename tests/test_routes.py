"""
    Test for routes functions : ensure responses are correct with mocked call to API
"""

from tests.test_resources import NemoResource
from flask_nemo import Nemo
from flask import Flask
from mock import Mock, patch, call
from jinja2.exceptions import TemplateNotFound


class NemoTestRoutesBusiness(NemoResource):
    """ Test Suite for Nemo
    """
    def test_route_index(self):
        """ Check that index return the template
        """
        self.assertEqual(self.nemo.r_index(), {"template": "main::index.html"})

    def test_route_assets_404(self):
        with patch('flask_nemo.abort') as abort:
            self.nemo.r_assets("js", "wrong-js.js")
            abort.assert_called_once_with(404)

    def test_route_assets_all(self):
        nemo = Nemo(
            statics=["testing_data/getcapabilities.xml"],
            js=["testing_data/getcapabilities.xml"],
            css=["testing_data/style.css"]
        )
        nemo.blueprint = Mock()
        nemo.register_assets()
        with patch("flask_nemo.send_from_directory") as patched:
            nemo.r_assets("js", "getcapabilities.xml")
            nemo.r_assets("static", "getcapabilities.xml")
            nemo.r_assets("css", "style.css")
            patched.assert_has_calls([
                call(directory="testing_data", filename="getcapabilities.xml"),
                call(directory="testing_data", filename="getcapabilities.xml"),
                call(directory="testing_data", filename="style.css")
            ])

    def test_register_route(self):
        app = Flask(__name__)
        nemo = Nemo(app=app, base_url="/perseus")
        nemo.register()
        self.assertIn("flask_nemo", app.blueprints)

        rules = [(rule.rule, rule.endpoint) for rule in app.url_map.iter_rules()]
        self.assertIn("/perseus/collections/<objectId>", [rule[0] for rule in rules])
        self.assertIn("flask_nemo.r_collection", [rule[1] for rule in rules])

        app = Flask(__name__)
        nemo = Nemo("nemo", app=app)
        nemo.register()
        self.assertIn("nemo", app.blueprints)

        rules = [(rule.rule, rule.endpoint) for rule in app.url_map.iter_rules()]
        self.assertIn("/nemo/collections/<objectId>", [rule[0] for rule in rules])
        self.assertIn("nemo.r_collection", [rule[1] for rule in rules])

        nemo = Nemo()
        self.assertEqual(nemo.register(), None)

    def test_additional_template(self):
        # Line 568-575
        app = Flask(__name__)
        nemo = Nemo(app=app, templates={"addendum": "tests/test_data/plugin_templates_main/main"})
        blueprint = nemo.create_blueprint()

        html, path, function = blueprint.jinja_loader.get_source("", "addendum::container.html")
        self.assertIn("I am A CONTAINER ! Isn't it sweet !", html)

        with self.assertRaises(TemplateNotFound):
            html, path, function = blueprint.jinja_loader.get_source("", "addendum::unknown.html")