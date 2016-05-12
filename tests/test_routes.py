"""
    Test for routes functions : ensure responses are correct with mocked call to API
"""

from .resources import NemoResource
from .test_controller import NemoTestControllers
from flask_nemo import Nemo
from flask_nemo.default import Breadcrumb
from flask import Markup, Flask
from lxml import etree
from mock import Mock, patch, call
import MyCapytain
from jinja2.exceptions import TemplateNotFound


class NemoTestRoutes(NemoResource):
    """ Test Suite for Nemo
    """
    def test_route_index(self):
        """ Check that index return the template
        """
        self.assertEqual(self.nemo.r_index(), {"template": "main::index.html"})

    def test_route_collection(self):
        """ Test return values of route collection (list of textgroups
        """

        with patch('requests.get', return_value=self.getCapabilities) as patched:
            view = self.nemo.r_collection("latinLit")
            self.assertEqual(view["template"], "main::textgroups.html")
            self.assertEqual(len(view["textgroups"]), 3)
            self.assertIn("urn:cts:latinLit:phi1294", [str(textgroup.urn) for textgroup in view["textgroups"]])
            self.assertIsInstance(view["textgroups"][0], MyCapytain.resources.inventory.TextGroup)

    def test_route_texts(self):
        """ Test return values of route texts (list of texts for a textgroup
        """

        with patch('requests.get', return_value=self.getCapabilities) as patched:
            view = self.nemo.r_texts("latinLit", "phi1294")
            self.assertEqual(view["template"], "main::texts.html")
            self.assertEqual(len(view["texts"]), 2)
            self.assertEqual(
                sorted([str(view["texts"][0].urn), str(view["texts"][1].urn)]),
                sorted(["urn:cts:latinLit:phi1294.phi002.perseus-lat2", "urn:cts:latinLit:phi1294.phi002.perseus-eng2"])
            )
            self.assertIsInstance(view["texts"][0], MyCapytain.resources.inventory.Text)

    def test_route_version_chunker_replacement(self):
        """ Try to get valid reffs
        """

        urn = "urn:cts:latinLit:phi1294.phi002.perseus-lat2"
        def chunker(text, level):
            self.assertIsInstance(text, MyCapytain.resources.inventory.Text)
            self.assertEqual(str(text.urn), "urn:cts:latinLit:phi1294.phi002.perseus-lat2")
            return True

        nemo = Nemo(
            api_url=NemoTestControllers.endpoint,
            inventory="annotsrc",
            chunker={"default": chunker}
        )

        with patch('requests.get', return_value=self.getValidReff) as patched:
            view = nemo.r_version("latinLit", "phi1294", "phi002", "perseus-lat2")
            self.assertIsInstance(view["version"], MyCapytain.resources.inventory.Text)
            patched.assert_called_once_with(
                NemoTestControllers.endpoint,
                params={
                    "inv": "annotsrc",
                    "request": "GetCapabilities"
                }
            )
            self.assertEqual(view["reffs"], True)

    def test_route_version_default_chunker(self):
        """ Try to get valid reffs
        """
        urn = "urn:cts:latinLit:phi1294.phi002.perseus-lat2"

        with patch('requests.get', return_value=self.getValidReff) as patched:
            view = self.nemo.r_version("latinLit", "phi1294", "phi002", "perseus-lat2")
            self.assertIsInstance(view["version"], MyCapytain.resources.inventory.Text)
            self.assertEqual(view["reffs"][0], ("1.pr.1", "1.pr.1"))

    def test_route_text_without_transform(self):
        """ Try to get valid reffs
        """
        urn = "urn:cts:latinLit:phi1294.phi002.perseus-lat2"

        with patch('requests.get', return_value=self.getValidReff) as patched:
            view = self.nemo.r_version("latinLit", "phi1294", "phi002", "perseus-lat2")
            self.assertIsInstance(view["version"], MyCapytain.resources.inventory.Text)
            self.assertEqual(view["reffs"][0], ("1.pr.1", "1.pr.1"))

    def test_route_passage_without_xslt(self):
        nemo = Nemo(
            api_url=NemoTestControllers.endpoint,
            inventory="annotsrc"
        )
        with patch('requests.get', return_value=self.getPassage_Route) as patched:
            view = self.nemo.r_passage("latinLit", "phi1294", "phi002", "perseus-lat2", "1.pr.1")
            self.assertEqual(view["template"], "main::text.html")
            self.assertIsInstance(view["version"], MyCapytain.resources.inventory.Text)
            self.assertEqual(str(view["version"].urn), "urn:cts:latinLit:phi1294.phi002.perseus-lat2")
            self.assertEqual(view["prev"], "1.1.1")
            self.assertEqual(view["next"], "1.1.3")
            self.assertIsInstance(view["text_passage"], Markup)

            # Reparsing xml
            xml = etree.fromstring(str(view["text_passage"]))
            self.assertEqual(
                len(xml.xpath("//tei:body", namespaces={"tei":"http://www.tei-c.org/ns/1.0"})),
                1
            )
            self.assertEqual(
                len(xml.xpath("//tei:l", namespaces={"tei":"http://www.tei-c.org/ns/1.0"})),
                6
            )

    def test_route_passage_with_transform(self):
        """ Try with a non xslt just to be sure
        """
        urn = "urn:cts:latinLit:phi1294.phi002.perseus-lat2"
        def transformer(version, text):
            self.assertEqual(str(version.urn), "urn:cts:latinLit:phi1294.phi002.perseus-lat2")
            self.assertIsInstance(text, etree._Element)
            return "<a>Hello</a>"
        nemo = Nemo(
            api_url=NemoTestControllers.endpoint,
            inventory="annotsrc",
            transform={"default": transformer}
        )
        with patch('requests.get', return_value=self.getPassage_Route) as patched:
            view = nemo.r_passage("latinLit", "phi1294", "phi002", "perseus-lat2", "1.pr.1")
            self.assertEqual(view["text_passage"], Markup("<a>Hello</a>"))

    def test_route_passage_with_xslt(self):
        nemo = Nemo(
            api_url=NemoTestControllers.endpoint,
            inventory="annotsrc",
            transform={"default": NemoTestControllers.body_xsl}
        )
        with patch('requests.get', return_value=self.getPassage_Route) as patched:
            view = nemo.r_passage("latinLit", "phi1294", "phi002", "perseus-lat2", "1.pr.1")
            self.assertEqual(view["template"], "main::text.html")
            self.assertIsInstance(view["version"], MyCapytain.resources.inventory.Text)
            self.assertEqual(str(view["version"].urn), "urn:cts:latinLit:phi1294.phi002.perseus-lat2")
            self.assertEqual(view["prev"], "1.1.1")
            self.assertEqual(view["next"], "1.1.3")
            self.assertIsInstance(view["text_passage"], Markup)

            # Reparsing xml
            xml = etree.fromstring(str(view["text_passage"]))
            self.assertEqual(
                len(xml.xpath("//tei:notbody", namespaces={"tei":"http://www.tei-c.org/ns/1.0"})),
                1
            )

    def test_route_passage_with_urn_xslt(self):
        nemo = Nemo(
            api_url=NemoTestControllers.endpoint,
            inventory="annotsrc",
            transform={"urn:cts:latinLit:phi1294.phi002.perseus-lat2": NemoTestControllers.body_xsl}
        )
        with patch('requests.get', return_value=self.getPassage_Route) as patched:
            view = nemo.r_passage("latinLit", "phi1294", "phi002", "perseus-lat2", "1.pr.1")
            # Reparsing xml
            xml = etree.fromstring(str(view["text_passage"]))
            self.assertEqual(
                len(xml.xpath("//tei:notbody", namespaces={"tei": "http://www.tei-c.org/ns/1.0"})),
                1
            )

    def test_route_passage_without_urn_xslt(self):
        nemo = Nemo(
            api_url=NemoTestControllers.endpoint,
            inventory="annotsrc",
            transform={"urn:cts:latinLit:phi1294.phi002.perseus-lat3": NemoTestControllers.body_xsl}
        )
        with patch('requests.get', return_value=self.getPassage_Route) as patched:
            view = nemo.r_passage("latinLit", "phi1294", "phi002", "perseus-lat2", "1.pr.1")
            # Reparsing xml
            xml = etree.fromstring(str(view["text_passage"]))
            self.assertEqual(
                len(xml.xpath("//tei:body", namespaces={"tei": "http://www.tei-c.org/ns/1.0"})),
                1
            )

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

    def test_view_maker(self):
        """ View maker should take care of returning a lambda using the function self.route and the function
        identified by the parameter name
        """
        nemo = Nemo()
        nemo.route = Mock()

        view = nemo.view_maker("r_collection")
        view(collection="latinLit")
        nemo.route.assert_called_with(nemo.r_collection, collection="latinLit")

    def test_render_normal(self):
        """ Render adds informations, including url parameters in a url dict
        """
        with patch("requests.get", return_value=self.getCapabilities):
            with patch("flask_nemo.render_template") as patched:
                self.nemo.render("main::index.html", test="123", value="value", url={})
                patched.assert_called_once_with(
                    "main::index.html",
                    collections={'latinLit', 'greekLit'},
                    test="123",
                    value="value",
                    lang="eng",
                    assets=self.nemo.assets,
                    url={},
                    breadcrumbs=[]
                )

    def test_render_textgroups(self):
        """ Render adds informations, including url parameters in a url dict
        """
        with patch("requests.get", return_value=self.getCapabilities):
            with patch("flask_nemo.render_template") as patched:
                data = self.nemo.render(
                    "index.html",
                    test="123",
                    value="value",
                    url={
                        "collection": "latinLit",
                        "textgroup": "phi1294"
                    })
                patched.assert_called_once_with(
                    "index.html",
                    collections={'latinLit', 'greekLit'},
                    test="123",
                    value="value",
                    lang="eng",
                    assets=self.nemo.assets,
                    url={
                        "collection": "latinLit",
                        "textgroup": "phi1294",

                    },
                    breadcrumbs=[
                      {'link': '.r_collection', 'title': 'latinLit', 'args': {'collection': 'latinLit'}},
                      {'link': None, 'title': 'Martial', 'args': {'textgroup': 'phi1294', 'collection': 'latinLit'}}
                    ],
                    textgroups=self.nemo.get_textgroups("latinLit")
                )

    def test_render_text(self):
        """ Render adds informations, including url parameters in a url dict
        """
        with patch("requests.get", return_value=self.getCapabilities):
            with patch("flask_nemo.render_template") as patched:
                self.nemo.render(
                    "index.html",
                    test="123",
                    value="value",
                    url={
                        "collection": "latinLit",
                        "textgroup": "phi1294",
                        "work": "phi002",
                        "text": "perseus-lat2"
                    })
                patched.assert_called_once_with(
                    "index.html",
                    collections={'latinLit', 'greekLit'},
                    test="123",
                    value="value",
                    lang="eng",
                    assets=self.nemo.assets,
                    url={
                        "collection": "latinLit",
                        "textgroup": "phi1294",
                        "work": "phi002",
                        "text": "perseus-lat2"
                    },
                    breadcrumbs=[
                      {'link': '.r_collection', 'title': 'latinLit', 'args': {'collection': 'latinLit'}},
                      {'link': None, 'title': 'Martial', 'args': {'textgroup': 'phi1294', 'collection': 'latinLit'}}
                    ],
                    textgroups=self.nemo.get_textgroups("latinLit"),
                    texts=self.nemo.get_texts("latinLit", "phi1294")
                )

    def test_route(self):
        """ nemo.route should apply fn and the args given
        """
        self.nemo.render = Mock()
        with patch("requests.get", return_value=self.getCapabilities):
            route = self.nemo.route(self.nemo.r_collection, collection="latinLit")
            self.nemo.render.assert_called_once_with(
                template="main::textgroups.html",
                textgroups=self.nemo.get_textgroups("latinLit"),
                url={"collection": "latinLit"}
            )

    def test_register_route(self):
        app = Flask(__name__)
        nemo = Nemo(app=app, base_url="/perseus")
        nemo.register()
        self.assertIn("flask_nemo", app.blueprints)

        rules = [(rule.rule, rule.endpoint) for rule in app.url_map.iter_rules()]
        self.assertIn("/perseus/read/<collection>/<textgroup>/<work>/<version>/<passage_identifier>", [rule[0] for rule in rules])
        self.assertIn("flask_nemo.r_passage", [rule[1] for rule in rules])

        app = Flask(__name__)
        nemo = Nemo("nemo", app=app)
        nemo.register()
        self.assertIn("nemo", app.blueprints)

        rules = [(rule.rule, rule.endpoint) for rule in app.url_map.iter_rules()]
        self.assertIn("/nemo/read/<collection>/<textgroup>/<work>/<version>/<passage_identifier>", [rule[0] for rule in rules])
        self.assertIn("nemo.r_passage", [rule[1] for rule in rules])

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
