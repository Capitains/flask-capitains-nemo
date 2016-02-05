import unittest
from flask.ext.nemo import Nemo
from mock import patch, call, Mock
import MyCapytain
from lxml import etree
from flask import Markup, Flask
from jinja2.exceptions import TemplateNotFound


def create_test_app(debug=False, config=None):
    app = Flask(__name__)
    app.debug = debug

    if config:
        app.config.update(**config)
    return app


class RequestPatch(object):
    """ Request patch object to deal with patching reply in flask.ext.nemo
    """
    def __init__(self, f):
        self.__text = f.read()

    @property
    def text(self):
        return self.__text


class RequestPatchChained(object):
    """ Request patch object to deal with patching reply in flask.ext.nemo
    """
    def __init__(self, requests):
        self.resource = [other.text for other in requests]

    @property
    def text(self):
        return self.resource.pop(0)

class NemoResource(unittest.TestCase):
    """ Test Suite for Nemo
    """
    endpoint = "http://website.com/cts/api"
    body_xsl = "testing_data/xsl_test.xml"

    def setUp(self):
        with open("testing_data/getcapabilities.xml", "r") as f:
            self.getCapabilities = RequestPatch(f)

        with open("testing_data/getvalidreff.xml", "r") as f:
            self.getValidReff_single = RequestPatch(f)
            self.getValidReff = RequestPatchChained([self.getCapabilities, self.getValidReff_single])

        with open("testing_data/getpassage.xml", "r") as f:
            self.getPassage = RequestPatch(f)
            self.getPassage_Capabilities = RequestPatchChained([self.getCapabilities, self.getPassage])

        with open("testing_data/getprevnext.xml", "r") as f:
            self.getPrevNext = RequestPatch(f)
            self.getPassage_Route = RequestPatchChained([self.getCapabilities, self.getPassage, self.getPrevNext])

        self.nemo = Nemo(
            api_url=NemoTestControllers.endpoint
        )


class NemoTestControllers(NemoResource):

    def test_flask_nemo(self):
        """ Testing Flask Nemo is set up"""
        a = Nemo()
        self.assertIsInstance(a, Nemo)
        a = Nemo()

    def test_without_inventory_request(self):
        """ Check that endpoint are derived from nemo.api_endpoint setting
        """
        #  Test without inventory
        with patch('requests.get', return_value=self.getCapabilities) as patched_get:
            self.nemo.get_inventory()
            patched_get.assert_called_once_with(
                NemoTestControllers.endpoint, params={
                    "request": "GetCapabilities"
                }
            )

    def test_with_inventory_request(self):
        """ Check that endpoint are derived from nemo.api_endpoint setting
        """
        with patch('requests.get', return_value=self.getCapabilities) as patched_get:
            #  Test with inventory
            self.nemo.api_inventory = "annotsrc"
            self.nemo.get_inventory()
            patched_get.assert_called_once_with(
                NemoTestControllers.endpoint, params={
                    "request": "GetCapabilities",
                    "inv": "annotsrc"
                }
            )
            self.nemo.api_inventory = None

    def test_inventory_parsing(self):
        """ Check that endpoint request leads to the creation of a TextInventory object
        """
        with patch('requests.get', return_value=self.getCapabilities) as patched_get:
            inventory = self.nemo.get_inventory()
            patched_get.assert_called_once_with(
                NemoTestControllers.endpoint, params={
                    "request": "GetCapabilities"
                }
            )
            self.assertIs(len(inventory.textgroups), 4)

    def test_get_collection(self):
        with patch('requests.get', return_value=self.getCapabilities) as patched_get:
            collections = self.nemo.get_collections()
            patched_get.assert_called_once_with(
                NemoTestControllers.endpoint, params={
                    "request": "GetCapabilities"
                }
            )
            self.assertEqual(collections, {"latinLit", "greekLit"})


    def test_get_authors(self):
        """ Check that authors textgroups are returned with informations
        """
        with patch('requests.get', return_value=self.getCapabilities):
            tgs = self.nemo.get_textgroups()
            self.assertIs(len(tgs), 4)
            self.assertEqual("urn:cts:greekLit:tlg0003" in [str(tg.urn) for tg in tgs], True)

    def test_get_authors_with_collection(self):
        """ Check that authors textgroups are returned when filtered by collection
        """
        with patch('requests.get', return_value=self.getCapabilities):
            tgs_2 = self.nemo.get_textgroups("greekLIT")  # With nice filtering
            self.assertIs(len(tgs_2), 1)
            self.assertEqual("urn:cts:greekLit:tlg0003" in [str(tg.urn) for tg in tgs_2], True)

    def test_get_works_with_collection(self):
        """ Check that works are returned when filtered by collection and textgroup
        """
        with patch('requests.get', return_value=self.getCapabilities):
            works = self.nemo.get_works("greekLIT", "TLG0003")  # With nice filtering
            self.assertIs(len(works), 1)
            self.assertEqual("urn:cts:greekLit:tlg0003.tlg001" in [str(work.urn) for work in works], True)

            #  Check when it fails
            works = self.nemo.get_works("greekLIT", "TLGabc003")  # With nice filtering
            self.assertIs(len(works), 0)

    def test_get_works_without_filters(self):
        """ Check that all works are returned when not filtered
        """
        with patch('requests.get', return_value=self.getCapabilities):
            #  Check when it fails
            works = self.nemo.get_works()  # With nice filtering
            self.assertIs(len(works), 13)

    def test_get_works_with_one_filter(self):
        """ Check that error are raises
        """
        with self.assertRaises(ValueError):
            works = self.nemo.get_works("a", None)  # With nice filtering

        with self.assertRaises(ValueError):
            works = self.nemo.get_works(None, "a")

    def test_get_texts_with_all_filtered(self):
        """ Check that texts are filtered
        """
        with patch('requests.get', return_value=self.getCapabilities):
            texts = self.nemo.get_texts("greekLIT", "TLG0003", "tlg001")  # With nice filtering
            self.assertIs(len(texts), 1)
            self.assertEqual("urn:cts:greekLit:tlg0003.tlg001.perseus-grc2" in [str(text.urn) for text in texts], True)

            texts = self.nemo.get_texts("greekLIT", "TLG0003", "tlg002")  # With nice filtering
            self.assertIs(len(texts), 0)

    def test_get_texts_with_none_filtered(self):
        """ Check that texts are filtered
        """
        with patch('requests.get', return_value=self.getCapabilities):
            texts = self.nemo.get_texts()  # With nice filtering
            self.assertIs(len(texts), 14)
            self.assertEqual("urn:cts:greekLit:tlg0003.tlg001.perseus-grc2" in [str(text.urn) for text in texts], True)
            self.assertEqual("urn:cts:latinLit:phi1294.phi002.perseus-lat2" in [str(text.urn) for text in texts], True)
            self.assertEqual("urn:cts:latinLit:phi1294.phi002.perseus-lat3" in [str(text.urn) for text in texts], False)

    def test_get_texts_with_work_not_filtered(self):
        """ Check that all textgroups texts are returned
        """
        with patch('requests.get', return_value=self.getCapabilities):
            texts = self.nemo.get_texts("latinLit", "phi0959")  # With nice filtering
            self.assertIs(len(texts), 10)
            self.assertEqual("urn:cts:greekLit:tlg0003.tlg001.perseus-grc2" in [str(text.urn) for text in texts], False)
            self.assertEqual("urn:cts:latinLit:phi0959.tlg001.perseus-lat2" in [str(text.urn) for text in texts], False)

    def test_get_texts_raise(self):
        with self.assertRaises(
                ValueError):
            self.nemo.get_texts("latinLit")

    def test_get_single_text(self):
        """ Check that texts are filtered
        """
        with patch('requests.get', return_value=self.getCapabilities):
            texts = self.nemo.get_text("greekLIT", "TLG0003", "tlg001", "perseus-grc2")  # With nice filtering
            self.assertIsInstance(texts, MyCapytain.resources.inventory.Text)
            self.assertEqual(str(texts.urn), "urn:cts:greekLit:tlg0003.tlg001.perseus-grc2")

    def test_get_single_text_empty_because_no_work(self):
        """ Check that texts are filtered
        """
        with patch('requests.get', return_value=self.getCapabilities):
            with patch('flask_nemo.abort') as abort:
                texts = self.nemo.get_text("latinLit", "phi0959", "phi011", "perseus-lat2")   # With nice filtering
                abort.assert_called_once_with(404)

    def test_get_single_text_abort(self):
        """ Check that texts are filtered
        """
        with patch('requests.get', return_value=self.getCapabilities):
            with patch('flask_nemo.abort') as abort:
                texts = self.nemo.get_text("greekLIT", "TLG0003", "tlg001", "perseus-grc132")  # With nice filtering
                abort.assert_called_once_with(404)

    def test_get_validreffs_without_specific_callback(self):
        """ Try to get valid reffs
        """
        self.nemo = Nemo(api_url=NemoTestControllers.endpoint, inventory="annotsrc")
        with patch('requests.get', return_value=self.getValidReff) as patched:
            text, callback = self.nemo.get_reffs("latinLit", "phi1294", "phi002", "perseus-lat2")
            self.assertIsInstance(text, MyCapytain.resources.inventory.Text)

            reffs = callback(level=3)
            self.assertIsInstance(reffs, list)
            self.assertEqual(reffs[0], "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.1")
            self.assertEqual(patched.mock_calls, [
                call(
                    NemoTestControllers.endpoint,
                    params={
                        "inv": "annotsrc",
                        "request": "GetCapabilities"
                    }
                ),
                call(
                    NemoTestControllers.endpoint,
                    params={
                        "inv": "annotsrc",
                        "request": "GetValidReff",
                        "level": "3",
                        "urn": "urn:cts:latinLit:phi1294.phi002.perseus-lat2"
                    }
                )
                ]
            )

    def test_get_passage(self):
        self.nemo = Nemo(api_url=NemoTestControllers.endpoint, inventory="annotsrc")
        with patch('requests.get', return_value=self.getPassage) as patched:
            passage = self.nemo.get_passage("latinLit", "phi1294", "phi002", "perseus-lat2", "1.pr")
            self.assertIsInstance(passage, MyCapytain.resources.texts.api.Passage)
            self.assertEqual(len(passage.xml.xpath("//tei:l[@n]", namespaces={"tei":"http://www.tei-c.org/ns/1.0"})), 6)


class TestNemoInit(NemoResource):
    def test_init_app(self):
        app = Flask(__name__)
        app.config["CTS_API_URL"] = "http://localhost"
        app.config["CTS_API_INVENTORY"] = "annotsrc"
        self.nemo.init_app(app)

        self.assertEqual(self.nemo.api_inventory, "annotsrc")
        self.assertEqual(self.nemo.api_url, "http://localhost")
        self.assertEqual(self.nemo.app, app)

    def test_overwrite_urls(self):
        routes = [("/index.html", "r_index", ["GET"])] + Nemo.ROUTES[1:]
        app = Flask(__name__)
        nemo = Nemo(app=app, urls=routes)
        nemo.register_routes()
        self.assertIn("flask_nemo", app.blueprints)

        rules = [(rule.rule, rule.endpoint) for rule in app.url_map.iter_rules()]
        self.assertIn("/nemo/index.html", [rule[0] for rule in rules])
        self.assertNotIn("/nemo/", [rule[0] for rule in rules])

    def test_static_url_path(self):
        app = Flask(__name__)
        nemo = Nemo(app=app, static_url_path="/assets/nemoOo")
        nemo.register_routes()
        self.assertIn("flask_nemo", app.blueprints)

        rules = [(rule.rule, rule.endpoint) for rule in app.url_map.iter_rules()]
        self.assertIn("/nemo/assets/nemoOo/<path:filename>", [rule[0] for rule in rules])
        self.assertIn("/nemo/assets/nemoOo.secondary/<type>/<asset>", [rule[0] for rule in rules])

    def test_static_folder(self):
        app = Flask(__name__)
        nemo = Nemo(app=app, static_folder="/examples")
        nemo.register_routes()

        self.assertEqual(nemo.static_folder, "/examples")
        self.assertEqual(nemo.blueprint.static_folder, "/examples")

    def test_template_folder(self):
        app = Flask(__name__)
        nemo = Nemo(app=app, template_folder="/examples")
        nemo.register_routes()

        self.assertEqual(nemo.template_folder, "/examples")
        self.assertEqual(nemo.blueprint.template_folder, "/examples")


class NemoTestRoutes(NemoResource):
    """ Test Suite for Nemo
    """
    def test_route_index(self):
        """ Check that index return the template
        """
        self.assertEqual(self.nemo.r_index(), {"template": self.nemo.templates["index"]})

    def test_route_collection(self):
        """ Test return values of route collection (list of textgroups
        """

        with patch('requests.get', return_value=self.getCapabilities) as patched:
            view = self.nemo.r_collection("latinLit")
            self.assertEqual(view["template"], self.nemo.templates["textgroups"])
            self.assertEqual(len(view["textgroups"]), 3)
            self.assertIn("urn:cts:latinLit:phi1294", [str(textgroup.urn) for textgroup in view["textgroups"]])
            self.assertIsInstance(view["textgroups"][0], MyCapytain.resources.inventory.TextGroup)

    def test_route_texts(self):
        """ Test return values of route texts (list of texts for a textgroup
        """

        with patch('requests.get', return_value=self.getCapabilities) as patched:
            view = self.nemo.r_texts("latinLit", "phi1294")
            self.assertEqual(view["template"], self.nemo.templates["texts"])
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
            self.assertEqual(view["template"], nemo.templates["text"])
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
            self.assertEqual(view["template"], nemo.templates["text"])
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
                self.nemo.render("index.html", test="123", value="value", url={})
                patched.assert_called_once_with(
                    "index.html",
                    collections={'latinLit', 'greekLit'},
                    test="123",
                    value="value",
                    lang="eng",
                    templates=self.nemo.templates,
                    assets=self.nemo.assets,
                    url={},
                    breadcrumbs=[]
                )

    def test_render_textgroups(self):
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
                        "textgroup": "phi1294"
                    })
                patched.assert_called_once_with(
                    "index.html",
                    collections={'latinLit', 'greekLit'},
                    test="123",
                    value="value",
                    lang="eng",
                    templates=self.nemo.templates,
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
                    templates=self.nemo.templates,
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
                template="textgroups.html",
                textgroups=self.nemo.get_textgroups("latinLit"),
                url={"collection": "latinLit"}
            )

    def test_register_route(self):
        app = Flask(__name__)
        nemo = Nemo(app=app, base_url="/perseus")
        nemo.register_routes()
        self.assertIn("flask_nemo", app.blueprints)

        rules = [(rule.rule, rule.endpoint) for rule in app.url_map.iter_rules()]
        self.assertIn("/perseus/read/<collection>/<textgroup>/<work>/<version>/<passage_identifier>", [rule[0] for rule in rules])
        self.assertIn("flask_nemo.r_passage", [rule[1] for rule in rules])

        app = Flask(__name__)
        nemo = Nemo("nemo", app=app)
        nemo.register_routes()
        self.assertIn("nemo", app.blueprints)

        rules = [(rule.rule, rule.endpoint) for rule in app.url_map.iter_rules()]
        self.assertIn("/nemo/read/<collection>/<textgroup>/<work>/<version>/<passage_identifier>", [rule[0] for rule in rules])
        self.assertIn("nemo.r_passage", [rule[1] for rule in rules])

        nemo = Nemo()
        self.assertEqual(nemo.register_routes(), None)

    def test_additional_template(self):
        # Line 568-575
        app = Flask(__name__)
        nemo = Nemo(app=app, templates={"menu": "examples/ciham.menu.html"})
        blueprint = nemo.create_blueprint()

        html, path, function = blueprint.jinja_loader.get_source("", "examples/ciham.menu.html")
        self.assertIn("Text provided by CIHAM", html)

        with self.assertRaises(TemplateNotFound):
            html, path, function = blueprint.jinja_loader.get_source("", "examples/unknown.html")
    
    def test_make_passage_breadcrumb(self):
        """ passage breadcrumb should include all components up to passage and passage not linked
        """
        with patch("requests.get", return_value=self.getCapabilities):
            bc = self.nemo.make_breadcrumbs(
                textgroups=self.nemo.get_textgroups(),
                version = self.nemo.get_text("latinLit","phi1294","phi002","perseus-lat2"),
                lang="eng",
                url={
                    "collection": "latinLit",
                    "textgroup": "phi1294",
                    "work": "phi002",
                    "version": "perseus-lat2",
                    "passage_identifier": "1.1"
                    })
            self.assertEqual(bc,[
                {'link': '.r_collection', 'title': 'latinLit', 'args': {'collection': 'latinLit'}}, 
                {'link': '.r_texts', 'title': 'Martial', 'args': {'textgroup': 'phi1294', 'collection': 'latinLit'}},
                {'link': '.r_version', 'title': 'Epigrammata Label', 'args': {'textgroup': 'phi1294', 'collection': 'latinLit', 'work':'phi002','version':'perseus-lat2'}},
                {'link': None, 'title': '1.1', 'args': {'textgroup': 'phi1294', 'collection': 'latinLit', 'work':'phi002','version':'perseus-lat2', 'passage_identifier':"1.1"}}
            ])


    def test_make_version_breadcrumb(self):
        """ version breadcrumb should include all components up to version and version not linked
        """
        with patch("requests.get", return_value=self.getCapabilities):
            bc = self.nemo.make_breadcrumbs(
                textgroups=self.nemo.get_textgroups(),
                version = self.nemo.get_text("latinLit","phi1294","phi002","perseus-lat2"),
                lang="eng",
                url={
                    "collection": "latinLit",
                    "textgroup": "phi1294",
                    "work": "phi002",
                    "version": "perseus-lat2"
                    })
            self.assertEqual(bc,[
                {'link': '.r_collection', 'title': 'latinLit', 'args': {'collection': 'latinLit'}}, 
                {'link': '.r_texts', 'title': 'Martial', 'args': {'textgroup': 'phi1294', 'collection': 'latinLit'}},
                {'link': None, 'title': 'Epigrammata Label', 'args': {'textgroup': 'phi1294', 'collection': 'latinLit', 'work':'phi002','version':'perseus-lat2'}}
            ])

    def test_make_textgroup_breadcrumb(self):
        """ textgroup breadcrumb should include all components up to textgroup and textgroup not linked
        """
        with patch("requests.get", return_value=self.getCapabilities):
            bc = self.nemo.make_breadcrumbs(
                textgroups=self.nemo.get_textgroups(),
                lang="eng",
                url={
                    "collection": "latinLit",
                    "textgroup": "phi1294",
                    })
            self.assertEqual(bc,[
                {'link': '.r_collection', 'title': 'latinLit', 'args': {'collection': 'latinLit'}}, 
                {'link': None, 'title': 'Martial', 'args': {'textgroup': 'phi1294', 'collection': 'latinLit'}}
            ])

    def test_make_collection_breadcrumb(self):
        """ collection breadcrumb should include only collection not linked
        """
        with patch("requests.get", return_value=self.getCapabilities):
            bc = self.nemo.make_breadcrumbs(
                lang="eng",
                url={ "collection": "latinLit"})
            self.assertEqual(bc,[
                {'link': None, 'title': 'latinLit', 'args': {'collection': 'latinLit'}}
            ])


class TestCustomizer(NemoResource):
    """ Test customization appliers
    """
    def test_chunker_default(self):
        """ Test that the chunker default is called and applied
        """
        def default(text, reffs):
            self.assertEqual(str(text.urn), "urn:cts:phi1294.phi002.perseus-lat2")
            self.assertEqual(reffs, ["1.pr"])
            return [("1.pr", "I PR")]

        nemo = Nemo(chunker={
            "default": default
        })
        chunked = nemo.chunk(
            MyCapytain.resources.inventory.Text(
                urn="urn:cts:phi1294.phi002.perseus-lat2"
            ),
            ["1.pr"]
        )
        self.assertEqual(chunked, [("1.pr", "I PR")])

    def test_chunker_urn(self):
        """ Test that the chunker by urn is called and applied
        """
        def urn(text, reffs):
            self.assertEqual(str(text.urn), "urn:cts:phi1294.phi002.perseus-lat2")
            self.assertEqual(reffs, ["1.pr"])
            return [("1.pr", "I PR")]

        nemo = Nemo(chunker={
            "default": lambda x, y: y,
            "urn:cts:phi1294.phi002.perseus-lat2": urn
        })
        chunked = nemo.chunk(
            MyCapytain.resources.inventory.Text(
                urn="urn:cts:phi1294.phi002.perseus-lat2"
            ),
            ["1.pr"]
        )
        self.assertEqual(chunked, [("1.pr", "I PR")])

    def test_prevnext_default(self):
        """ Test that the chunker default is called and applied
        """
        def default(text, cb):
            self.assertEqual(str(text.urn), "urn:cts:phi1294.phi002.perseus-lat2")
            self.assertEqual(cb(1), 1)
            return [("1.pr", "I PR")]

        nemo = Nemo(prevnext={
            "default": default
        })
        prevnext = nemo.getprevnext(
            MyCapytain.resources.inventory.Text(
                urn="urn:cts:phi1294.phi002.perseus-lat2"
            ),
            lambda x: x
        )
        self.assertEqual(prevnext, [("1.pr", "I PR")])

    def test_prevnext_urn(self):
        """ Test that the prevnext by urn is called and applied
        """
        def urn(text, cb):
            self.assertEqual(str(text.urn), "urn:cts:phi1294.phi002.perseus-lat2")
            self.assertEqual(cb(1), 1)
            return [("1.pr", "I PR")]

        nemo = Nemo(prevnext={
            "default": lambda x, y: y,
            "urn:cts:phi1294.phi002.perseus-lat2": urn
        })
        chunked = nemo.getprevnext(
            MyCapytain.resources.inventory.Text(
                urn="urn:cts:phi1294.phi002.perseus-lat2"
            ),
            lambda x: x
        )
        self.assertEqual(chunked, [("1.pr", "I PR")])

    def test_urntransform_default_function(self):
        """ Test that the transform default is called and applied
        """
        def default(urn):
          self.assertEqual(str(urn), "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr")
          return str(urn)

        nemo = Nemo(urntransform={
            "default": default
        })
        transformed = nemo.transform_urn(
            MyCapytain.resources.inventory.Text(
                urn="urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr"
            ).urn
        )
        self.assertEqual(transformed, "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr")

    def test_urntransform_override_function(self):
        """ Test that the transform override is called and applied
        """
        def override(urn):
          self.assertEqual(str(urn), "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr")
          return "override"

        nemo = Nemo(urntransform={
            "urn:cts:latinLit:phi1294.phi002.perseus-lat2": override
        })
        transformed = nemo.transform_urn(
            MyCapytain.resources.inventory.Text(
                urn="urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr"
            ).urn
        )
        self.assertEqual(transformed, "override")
    
    def test_transform_default_xslt(self):
        """ Test that the transform default is called and applied
        """
        def default(text, cb):
            self.assertEqual(str(text.urn), "urn:cts:phi1294.phi002.perseus-lat2")
            self.assertEqual(cb(1), 1)
            return [("1.pr", "I PR")]

        nemo = Nemo(prevnext={
            "default": default
        })
        prevnext = nemo.getprevnext(
            MyCapytain.resources.inventory.Text(
                urn="urn:cts:phi1294.phi002.perseus-lat2"
            ),
            lambda x: x
        )
        self.assertEqual(prevnext, [("1.pr", "I PR")])

    def test_transform_default_function(self):
        """ Test that the transform default is called and applied when it's a function
        """
        def default(work, xml):
            self.assertEqual(str(work.urn), "urn:cts:phi1294.phi002.perseus-lat2")
            self.assertEqual(xml, "<a></a>")
            return "<b></b>"

        nemo = Nemo(transform={
            "default": default
        })
        transformed = nemo.transform(
            MyCapytain.resources.inventory.Text(
                urn="urn:cts:phi1294.phi002.perseus-lat2"
            ),
            "<a></a>"
        )
        self.assertEqual(transformed, "<b></b>")

    def test_transform_default_none(self):
        """ Test that the transform default is called and applied
        """
        nemo = Nemo()
        transformed = nemo.transform(
            MyCapytain.resources.inventory.Text(
                urn="urn:cts:phi1294.phi002.perseus-lat2"
            ),
            etree.fromstring("<a/>")
        )
        self.assertEqual(transformed, "<a/>")

    def test_transform_urn_xslt(self):
        """ Test that the transform default is called and applied
        """

        nemo = Nemo(transform={
            "default": "testing_data/xsl_test.xml"
        })
        transformed = nemo.transform(
            MyCapytain.resources.inventory.Text(
                urn="urn:cts:phi1294.phi002.perseus-lat2"
            ),
            etree.fromstring('<tei:body xmlns:tei="http://www.tei-c.org/ns/1.0" />')
        )
        self.assertEqual(transformed, '<tei:notbody xmlns:tei="http://www.tei-c.org/ns/1.0"/>')


class TestFilters(NemoResource):

    def test_f_active_link(self):
        """ Test checking if something is in the path
        """
        wrong = Nemo.f_active_link("phi003", {"collection": "latinLit"})
        wrong2 = Nemo.f_active_link("phi003", {"collection": "latinLit", "textgroup": "phi0003"})
        right = Nemo.f_active_link("phi003", {"collection": "latinLit", "textgroup": "phi0003", "work": "phi003"})
        self.assertEqual(wrong, "")
        self.assertEqual(wrong2, "")
        self.assertEqual(right, "active")

    def test_f_collection_i18n(self):
        """ Test internationalization of collection identifier
        """
        self.assertEqual(Nemo.f_collection_i18n("latinLit"), "Latin")
        self.assertEqual(Nemo.f_collection_i18n("greekLit"), "Ancient Greek")
        self.assertEqual(Nemo.f_collection_i18n("freLit"), "freLit")

    def test_f_formatting_passage_reference(self):
        """ Test split of passage range identifier
        """
        self.assertEqual(Nemo.f_formatting_passage_reference("1.1-1.2"), "1.1")
        self.assertEqual(Nemo.f_formatting_passage_reference("1.1"), "1.1")

    def test_f_i18n_iso(self):
        """ Test split of passage range identifier
        """
        self.assertEqual(Nemo.f_i18n_iso("eng"), "English")
        self.assertEqual(Nemo.f_i18n_iso("eng", "fre"), "anglais")
        self.assertEqual(Nemo.f_i18n_iso("eng", "ger"), "English")

    def test_f_order_text_edition_translation(self):
        """ Check the reordering filter
        """
        Text = MyCapytain.resources.inventory.Text
        a, b, c, d = Text(subtype="Translation"), Text(subtype="Edition"), Text(subtype="Edition"), Text(subtype="Translation")
        self.assertEqual(Nemo.f_order_text_edition_translation([a,b,c,d]), [b, c, a, d])

    def test_register_filter(self):
        app = Flask(__name__)
        self.nemo = Nemo(app=app)
        self.nemo.register_filters()
        self.assertEqual(self.nemo.app.jinja_env.filters["formatting_passage_reference"], Nemo.f_formatting_passage_reference)
        self.assertEqual(self.nemo.app.jinja_env.filters["collection_i18n"], Nemo.f_collection_i18n)
        self.assertEqual(self.nemo.app.jinja_env.filters["active_link"], Nemo.f_active_link)

    def test_f_hierarchical_passages(self):
        """Test for normal, simple passage hierarchical conversion
        :return:
        """
        reffs = [("1.5.8", "Line 8"), ("1.5.9", "Line 9"), ("1.6.8", "Line 7"), ("2.5.8", "Line 12")]
        citation_line = MyCapytain.common.reference.Citation(name="line")
        citation_poem = MyCapytain.common.reference.Citation(name="poem", child=citation_line)
        citation_book = MyCapytain.common.reference.Citation(name="book", child=citation_poem)
        text = MyCapytain.resources.inventory.Text()
        text.citation = citation_book
        converted = Nemo.f_hierarchical_passages(reffs, text)
        self.assertEqual(converted["%book|1%"]["%poem|5%"]["Line 8"], "1.5.8")
        self.assertEqual(converted["%book|1%"]["%poem|5%"]["Line 9"], "1.5.9")
        self.assertEqual(converted["%book|1%"]["%poem|6%"]["Line 7"], "1.6.8")
        self.assertEqual(converted["%book|2%"]["%poem|5%"]["Line 12"], "2.5.8")
        self.assertEqual(len(converted), 2)
        self.assertEqual(len(converted["%book|1%"]), 2)
        self.assertEqual(len(converted["%book|1%"]["%poem|5%"]), 2)
        self.assertEqual(len(converted["%book|1%"]["%poem|6%"]), 1)
        self.assertEqual(len(converted["%book|2%"]), 1)

    def test_f_hierarchical_range_passages(self):
        """Test for range passage hierarchical conversion
        :return:
        """
        reffs = [("1.5.8-1.5.9", "Line 8"), ("1.5.9-1.5.15", "Line 9"), ("1.6.8-2.9.16", "Line 7"), ("2.5.8-16.45.928", "Line 12")]
        citation_line = MyCapytain.common.reference.Citation(name="line")
        citation_poem = MyCapytain.common.reference.Citation(name="poem", child=citation_line)
        citation_book = MyCapytain.common.reference.Citation(name="book", child=citation_poem)
        text = MyCapytain.resources.inventory.Text()
        text.citation = citation_book
        converted = Nemo.f_hierarchical_passages(reffs, text)
        self.assertEqual(converted["%book|1%"]["%poem|5%"]["Line 8"], "1.5.8-1.5.9")
        self.assertEqual(converted["%book|1%"]["%poem|5%"]["Line 9"], "1.5.9-1.5.15")
        self.assertEqual(converted["%book|1%"]["%poem|6%"]["Line 7"], "1.6.8-2.9.16")
        self.assertEqual(converted["%book|2%"]["%poem|5%"]["Line 12"], "2.5.8-16.45.928")
        self.assertEqual(len(converted), 2)
        self.assertEqual(len(converted["%book|1%"]), 2)
        self.assertEqual(len(converted["%book|1%"]["%poem|5%"]), 2)
        self.assertEqual(len(converted["%book|1%"]["%poem|6%"]), 1)
        self.assertEqual(len(converted["%book|2%"]), 1)

    def test_f_is_str(self):
        """ Test string
        """
        self.assertEqual(Nemo.f_is_str("h"), True)
        self.assertEqual(Nemo.f_is_str([]), False)

    def test_f_i18n_citation_type(self):
        self.assertEqual(Nemo.f_i18n_citation_type("%book|1%"), "Book 1")


class TestChunkers(NemoResource):

    def setUp(self):
        super(TestChunkers, self).setUp()
        self.inventory = MyCapytain.resources.inventory.TextInventory(resource=self.getCapabilities.text)

    def make_get_reff(self, asserted_level):
        def GetReff(level=1):
            self.assertEqual(level, asserted_level)  # Depth of the Citation Scheme
            return ["urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.1.7"]
        return GetReff

    def test_default_chunker(self):
        """ Test default chunker
        """
        text = self.inventory["urn:cts:latinLit:phi1294.phi002.perseus-lat2"]
        reffs = Nemo.default_chunker(text, self.make_get_reff(3))
        self.assertEqual(reffs, [
            ("1.pr.5", "1.pr.5"),
            ("1.1.7", "1.1.7")
        ])
        Nemo.default_chunker(self.inventory["urn:cts:latinLit:phi0959.phi003.perseus-lat2"], self.make_get_reff(2))

    def test_line_chunker(self):
        """ Test line grouping chunker
        """
        def validReff(level):
            self.assertEqual(level, 3)
            return ["urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.1","urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.2","urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.3","urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.4","urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.5","urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.6","urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.7","urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.8","urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.9","urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.10","urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.11","urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.12","urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.13","urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.14","urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.15","urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.16","urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.17","urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.18","urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.19","urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.20","urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.21","urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.22"]

        reffs = Nemo.line_chunker(self.inventory["urn:cts:latinLit:phi1294.phi002.perseus-lat2"], validReff, 5)
        self.assertEqual(reffs, [
            ("1.pr.1-1.pr.5","1.pr.1"),
            ("1.pr.6-1.pr.10","1.pr.6"),
            ("1.pr.11-1.pr.15","1.pr.11"),
            ("1.pr.16-1.pr.20","1.pr.16"),
            ("1.pr.21-1.pr.22","1.pr.21")
        ])

        reffs = Nemo.line_chunker(self.inventory["urn:cts:latinLit:phi1294.phi002.perseus-lat2"], validReff, 11)
        self.assertEqual(reffs, [
            ("1.pr.1-1.pr.11","1.pr.1"),
            ("1.pr.12-1.pr.22","1.pr.12")
        ])

    def test_scheme_chunker(self):
        """ Test chunking according to scheme
        """
        text = self.inventory["urn:cts:latinLit:phi1294.phi002.perseus-lat2"] # book, poem
        reffs = Nemo.scheme_chunker(text, self.make_get_reff(2))
        self.assertEqual(reffs, [
            ("1.pr.5", "1.pr.5"),
            ("1.1.7", "1.1.7")
        ])

        with patch("flask_nemo.Nemo.line_chunker", return_value=True) as line_chunker:
            self.assertEqual(Nemo.scheme_chunker(
                self.inventory["urn:cts:latinLit:phi0959.phi007.perseus-lat2"],
                self.make_get_reff(2)
            ), True)

    def test_level_chunker(self):
        """ Test chunking according to scheme
        """
        text = self.inventory["urn:cts:latinLit:phi1294.phi002.perseus-lat2"]  # book, poem
        reffs = Nemo.level_chunker(text, self.make_get_reff(2), level=2)
        """ A test is run with make_get_reff """

    def test_level_grouper(self):
        """ Test level grouper
        """
        text = self.inventory["urn:cts:latinLit:phi1294.phi002.perseus-lat2"]
        data = ["urn:cts:latinLit:phi0472.phi001.perseus-lat2:1.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:1.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:1.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:1.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:1.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:1.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:1.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:1.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:1.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:1.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:2.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:2.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:2.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:2.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:2.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:2.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:2.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:2.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:2.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:2.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:2.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:2.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:2.13", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:3.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:3.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:3.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:3.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:3.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:3.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:3.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:3.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:3.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:3.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:3.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:3.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:3.13", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:3.14", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:3.15", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:3.16", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:3.17", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:3.18", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:4.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:4.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:4.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:4.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:4.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:4.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:4.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:4.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:4.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:4.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:4.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:4.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:4.13", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:4.14", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:4.15", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:4.16", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:4.17", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:4.18", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:4.19", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:4.20", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:4.21", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:4.22", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:4.23", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:4.24", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:4.25", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:4.26", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:4.27", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:5.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:5.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:5.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:5.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:5.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:5.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:5.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:5.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:5.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:5.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:5.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:5.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:5.13", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:6.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:6.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:6.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:6.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:6.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:6.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:6.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:6.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:6.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:6.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:6.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:6.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:6.13", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:6.14", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:6.15", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:6.16", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:6.17", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:7.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:7.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:7.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:7.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:7.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:7.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:7.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:7.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:7.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:7.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:7.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:7.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:8.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:8.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:8.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:8.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:8.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:8.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:8.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:8.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:8.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:8.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:8.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:8.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:8.13", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:8.14", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:8.15", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:8.16", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:8.17", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:8.18", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:8.19", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:9.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:9.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:9.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:9.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:9.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:9.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:9.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:9.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:9.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:9.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:9.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:10.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:10.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:10.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:10.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:10.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:10.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:10.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:10.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:10.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:10.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:10.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:10.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:10.13", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:10.14", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:10.15", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:10.16", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:10.17", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:10.18", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:10.19", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:10.20", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:10.21", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:10.22", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:10.23", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:10.24", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:10.25", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:10.26", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:10.27", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:10.28", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:10.29", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:10.30", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:10.31", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:10.32", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:10.33", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:10.34", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:11.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:11.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:11.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:11.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:11.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:11.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:11.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:11.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:11.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:11.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:11.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:11.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:11.13", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:11.14", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:11.15", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:11.16", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:11.17", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:11.18", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:11.19", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:11.20", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:11.21", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:11.22", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:11.23", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:11.24", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:12.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:12.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:12.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:12.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:12.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:12.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:12.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:12.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:12.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:12.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:12.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:12.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:12.13", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:12.14", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:12.15", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:12.16", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:12.17", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:13.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:13.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:13.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:13.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:13.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:13.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:13.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:13.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:13.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:13.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:13.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:13.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:13.13", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:13.14", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:14.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:14.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:14.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:14.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:14.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:14.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:14.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:14.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:14.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:14.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:14.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:14.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:14.13", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:14.14", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:14.15", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:14.16", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:14.17", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:14.18", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:14.19", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:14.20", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:14.21", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:14.22", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:14.23", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:14b.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:14b.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:14b.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:15.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:15.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:15.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:15.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:15.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:15.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:15.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:15.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:15.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:15.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:15.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:15.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:15.13", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:15.14", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:15.15", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:15.16", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:15.17", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:15.18", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:15.19", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:16.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:16.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:16.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:16.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:16.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:16.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:16.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:16.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:16.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:16.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:16.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:16.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:16.13", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:16.14", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:17.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:17.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:17.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:17.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:17.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:17.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:17.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:17.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:17.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:17.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:17.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:17.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:17.13", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:17.14", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:17.15", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:17.16", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:17.17", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:17.18", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:17.19", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:17.20", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:17.21", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:17.22", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:17.23", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:17.24", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:17.25", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:17.26", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:21.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:21.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:21.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:21.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:21.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:21.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:21.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:21.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:21.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:21.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:21.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:21.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:21.13", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:22.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:22.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:22.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:22.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:22.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:22.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:22.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:22.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:22.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:22.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:22.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:22.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:22.13", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:22.14", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:22.15", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:22.16", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:22.17", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:22.18", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:22.19", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:22.20", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:22.21", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:23.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:23.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:23.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:23.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:23.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:23.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:23.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:23.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:23.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:23.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:23.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:23.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:23.13", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:23.14", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:23.15", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:23.16", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:23.17", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:23.18", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:23.19", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:23.20", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:23.21", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:23.22", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:23.23", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:23.24", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:23.25", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:23.26", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:23.27", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:24.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:24.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:24.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:24.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:24.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:24.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:24.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:24.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:24.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:24.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:25.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:25.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:25.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:25.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:25.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:25.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:25.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:25.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:25.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:25.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:25.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:25.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:25.13", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:26.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:26.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:26.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:26.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:26.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:27.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:27.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:27.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:27.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:27.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:27.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:27.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:28.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:28.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:28.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:28.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:28.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:28.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:28.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:28.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:28.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:28.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:28.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:28.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:28.13", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:28.14", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:28.15", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:29.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:29.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:29.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:29.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:29.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:29.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:29.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:29.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:29.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:29.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:29.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:29.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:29.13", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:29.14", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:29.15", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:29.16", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:29.17", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:29.18", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:29.19", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:29.20", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:29.21", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:29.22", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:29.23", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:29.24", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:30.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:30.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:30.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:30.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:30.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:30.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:30.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:30.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:30.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:30.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:30.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:30.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:31.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:31.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:31.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:31.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:31.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:31.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:31.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:31.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:31.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:31.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:31.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:31.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:31.13", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:31.14", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:32.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:32.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:32.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:32.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:32.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:32.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:32.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:32.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:32.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:32.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:32.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:33.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:33.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:33.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:33.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:33.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:33.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:33.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:33.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:34.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:34.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:34.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:34.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:34.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:34.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:34.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:34.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:34.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:34.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:34.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:34.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:34.13", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:34.14", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:34.15", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:34.16", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:34.17", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:34.18", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:34.19", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:34.20", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:34.21", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:34.22", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:34.23", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:34.24", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:35.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:35.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:35.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:35.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:35.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:35.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:35.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:35.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:35.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:35.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:35.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:35.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:35.13", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:35.14", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:35.15", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:35.16", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:35.17", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:35.18", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:36.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:36.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:36.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:36.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:36.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:36.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:36.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:36.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:36.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:36.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:36.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:36.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:36.13", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:36.14", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:36.15", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:36.16", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:36.17", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:36.18", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:36.19", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:36.20", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:37.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:37.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:37.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:37.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:37.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:37.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:37.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:37.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:37.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:37.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:37.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:37.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:37.13", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:37.14", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:37.15", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:37.16", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:37.17", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:37.18", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:37.19", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:37.20", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:38.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:38.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:38.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:38.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:38.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:38.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:38.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:38.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:39.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:39.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:39.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:39.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:39.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:39.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:39.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:39.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:39.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:39.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:39.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:39.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:39.13", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:39.14", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:39.15", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:39.16", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:39.17", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:39.18", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:39.19", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:39.20", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:39.21", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:40.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:40.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:40.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:40.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:40.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:40.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:40.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:40.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:41.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:41.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:41.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:41.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:41.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:41.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:41.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:41.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:42.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:42.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:42.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:42.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:42.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:42.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:42.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:42.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:42.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:42.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:42.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:42.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:42.13", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:42.14", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:42.15", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:42.16", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:42.17", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:42.18", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:42.19", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:42.20", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:42.21", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:42.22", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:42.23", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:42.24", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:43.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:43.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:43.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:43.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:43.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:43.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:43.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:43.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:44.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:44.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:44.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:44.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:44.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:44.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:44.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:44.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:44.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:44.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:44.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:44.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:44.13", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:44.14", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:44.15", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:44.16", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:44.17", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:44.18", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:44.19", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:44.20", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:44.21", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:45.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:45.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:45.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:45.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:45.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:45.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:45.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:45.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:45.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:45.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:45.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:45.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:45.13", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:45.14", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:45.15", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:45.16", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:45.17", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:45.18", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:45.19", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:45.20", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:45.21", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:45.22", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:45.23", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:45.24", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:45.25", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:45.26", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:46.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:46.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:46.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:46.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:46.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:46.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:46.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:46.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:46.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:46.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:46.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:47.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:47.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:47.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:47.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:47.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:47.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:47.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:48.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:48.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:48.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:48.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:48.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:48.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:49.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:49.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:49.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:49.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:49.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:49.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:49.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:50.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:50.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:50.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:50.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:50.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:50.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:50.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:50.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:50.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:50.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:50.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:50.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:50.13", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:50.14", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:50.15", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:50.16", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:50.17", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:50.18", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:50.19", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:50.20", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:50.21", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:51.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:51.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:51.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:51.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:51.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:51.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:51.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:51.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:51.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:51.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:51.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:51.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:51.13", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:51.14", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:51.15", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:51.16", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:52.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:52.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:52.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:52.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:53.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:53.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:53.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:53.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:53.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:54.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:54.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:54.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:54.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:54.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:54.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:54.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:55.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:55.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:55.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:55.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:55.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:55.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:55.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:55.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:55.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:55.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:55.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:55.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:55.13", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:55.14", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:55.15", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:55.16", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:55.17", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:55.18", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:55.19", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:55.20", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:55.21", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:55.22", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:56.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:56.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:56.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:56.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:56.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:56.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:56.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:57.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:57.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:57.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:57.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:57.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:57.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:57.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:57.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:57.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:57.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:58.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:58.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:58.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:58.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:58.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:58b.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:58b.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:58b.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:58b.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:58b.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:58b.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:58b.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:58b.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:58b.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:58b.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:59.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:59.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:59.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:59.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:59.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:60.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:60.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:60.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:60.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:60.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.13", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.14", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.15", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.16", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.17", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.18", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.19", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.20", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.21", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.22", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.23", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.24", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.25", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.26", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.27", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.28", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.29", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.30", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.31", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.32", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.33", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.34", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.35", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.36", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.37", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.38", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.39", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.40 118", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.41", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.42", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.43", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.44", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.45", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.46", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.47", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.48", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.49", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.50 60 138 143 148 158 163 168 173 178 183", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.51", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.52", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.53", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.54", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.55", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.56", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.57", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.58", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.59", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.50 60 138 143 148 158 163 168 173 178 183", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.61", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.62", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.63", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.64 69 74", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.65 70 75", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.66", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.67", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.68", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.64 69 74", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.65 70 75", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.71", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.72", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.73", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.64 69 74", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.65 70 75", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.76", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.77", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.78", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.79", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.80", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.81", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.82", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.83", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.84", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.85", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.86", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.87", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.88", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.89", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.90", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.91 96 106", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.92", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.93", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.94", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.95", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.91 96 106", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.97", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.98", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.99", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.100", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.101", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.102", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.103", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.104", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.105", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.91 96 106", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.107", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.108", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.109", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.110", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.111", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.112", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.113", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.114", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.115", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.116", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.117", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.40 118", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.119", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.120", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.121", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.122", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.123", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.124", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.125", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.126", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.127", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.128 133", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.129", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.130", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.131", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.132", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.128 133", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.134", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.135", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.136", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.137 142 147 157 162 167 172 177 182", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.50 60 138 143 148 158 163 168 173 178 183", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.139", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.140", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.141", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.137 142 147 157 162 167 172 177 182", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.50 60 138 143 148 158 163 168 173 178 183", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.144", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.145", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.146", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.137 142 147 157 162 167 172 177 182", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.50 60 138 143 148 158 163 168 173 178 183", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.149", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.150", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.151", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.152", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.153", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.154", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.155", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.156", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.137 142 147 157 162 167 172 177 182", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.50 60 138 143 148 158 163 168 173 178 183", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.159", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.160", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.161", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.137 142 147 157 162 167 172 177 182", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.50 60 138 143 148 158 163 168 173 178 183", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.164", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.165", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.166", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.137 142 147 157 162 167 172 177 182", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.50 60 138 143 148 158 163 168 173 178 183", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.169", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.170", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.171", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.137 142 147 157 162 167 172 177 182", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.50 60 138 143 148 158 163 168 173 178 183", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.174", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.175", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.176", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.137 142 147 157 162 167 172 177 182", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.50 60 138 143 148 158 163 168 173 178 183", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.179", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.180", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.181", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.137 142 147 157 162 167 172 177 182", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.50 60 138 143 148 158 163 168 173 178 183", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.184", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.185", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.186", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.187", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.188", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.189", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.190", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.191", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.192", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.193", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.194", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.195", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.196", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.197", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.198", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.199", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.200", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.201", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.202", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.203", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.204", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.205", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.206", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.207", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.208", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.209", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.210", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.211", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.212", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.213", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.214", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.215", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.216", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.217", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.218", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.219", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.220", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.221", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.222", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.223", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.224", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.225", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.226", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.227", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:61.228", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.5 10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.5 10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.13", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.14", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.15", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.16", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.17", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.18", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.19 25 31 38 48 66", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.20", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.21", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.22", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.23", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.24", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.19 25 31 38 48 66", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.26", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.27", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.28", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.29", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.30", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.19 25 31 38 48 66", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.32", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.33", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.34", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.35", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.36", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.37", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.19 25 31 38 48 66", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.39", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.40", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.41", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.42", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.43", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.44", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.45", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.46", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.47", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.19 25 31 38 48 66", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.49", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.50", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.51", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.52", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.53", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.54", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.55", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.56", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.57", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.58", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.59", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.60", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.61", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.62", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.63", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.64", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.65", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:62.19 25 31 38 48 66", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.13", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.14", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.15", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.16", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.17", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.18", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.19", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.20", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.21", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.22", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.23", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.24", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.25", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.26", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.27", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.28", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.29", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.30", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.31", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.32", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.33", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.34", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.35", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.36", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.37", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.38", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.39", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.40", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.41", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.42", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.43", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.44", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.45", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.46", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.47", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.48", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.49", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.50", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.51", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.52", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.53", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.54", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.55", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.56", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.57", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.58", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.59", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.60", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.61", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.62", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.63", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.64", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.65", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.66", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.67", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.68", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.69", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.70", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.71", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.72", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.73", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.74", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.75", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.76", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.77", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.78", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.79", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.80", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.81", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.82", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.83", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.84", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.85", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.86", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.87", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.88", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.89", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.90", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.91", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.92", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:63.93", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.13", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.14", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.15", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.16", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.17", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.18", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.19", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.20", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.21", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.22", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.23", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.24", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.25", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.26", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.27", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.28", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.29", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.30", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.31", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.32", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.33", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.34", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.35", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.36", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.37", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.38", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.39", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.40", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.41", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.42", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.43", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.44", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.45", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.46", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.47", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.48", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.49", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.50", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.51", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.52", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.53", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.54", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.55", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.56", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.57", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.58", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.59", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.60", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.61", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.62", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.63", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.64", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.65", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.66", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.67", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.68", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.69", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.70", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.71", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.72", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.73", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.74", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.75", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.76", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.77", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.78", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.79", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.80", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.81", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.82", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.83", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.84", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.85", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.86", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.87", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.88", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.89", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.90", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.91", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.92", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.93", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.94", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.95", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.96", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.97", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.98", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.99", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.100", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.101", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.102", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.103", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.104", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.105", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.106", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.107", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.108", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.109", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.110", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.111", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.112", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.113", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.114", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.115", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.116", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.117", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.118", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.119", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.120", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.121", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.122", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.123", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.124", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.125", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.126", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.127", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.128", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.129", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.130", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.131", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.132", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.133", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.134", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.135", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.136", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.137", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.138", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.139", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.140", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.141", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.142", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.143", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.144", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.145", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.146", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.147", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.148", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.149", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.150", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.151", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.152", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.153", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.154", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.155", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.156", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.157", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.158", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.159", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.160", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.161", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.162", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.163", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.164", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.165", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.166", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.167", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.168", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.169", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.170", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.171", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.172", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.173", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.174", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.175", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.176", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.177", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.178", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.179", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.180", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.181", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.182", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.183", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.184", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.185", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.186", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.187", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.188", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.189", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.190", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.191", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.192", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.193", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.194", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.195", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.196", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.197", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.198", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.199", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.200", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.201", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.202", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.203", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.204", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.205", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.206", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.207", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.208", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.209", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.210", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.211", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.212", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.213", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.214", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.215", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.216", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.217", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.218", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.219", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.220", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.221", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.222", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.223", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.224", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.225", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.226", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.227", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.228", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.229", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.230", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.231", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.232", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.233", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.234", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.235", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.236", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.237", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.238", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.239", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.240", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.241", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.242", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.243", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.244", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.245", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.246", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.247", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.248", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.249", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.250", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.251", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.252", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.253", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.254", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.255", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.256", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.257", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.258", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.259", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.260", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.261", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.262", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.263", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.264", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.265", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.266", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.267", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.268", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.269", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.270", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.271", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.272", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.273", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.274", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.275", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.276", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.277", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.278", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.279", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.280", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.281", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.282", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.283", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.284", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.285", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.286", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.287", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.288", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.289", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.290", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.291", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.292", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.293", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.294", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.295", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.296", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.297", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.298", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.299", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.300", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.301", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.302", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.303", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.304", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.305", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.306", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.307", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.308", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.309", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.310", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.311", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.312", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.313", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.314", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.315", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.316", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.317", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.318", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.319", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.320", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.321", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.322", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.323", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.324", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.325", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.326", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.327", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.328 334 338 343 348 353 357 362 372 376", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.329", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.330", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.331", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.332", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.333", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.328 334 338 343 348 353 357 362 372 376", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.335", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.336", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.337", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.328 334 338 343 348 353 357 362 372 376", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.339", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.340", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.341", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.342", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.328 334 338 343 348 353 357 362 372 376", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.344", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.345", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.346", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.347", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.328 334 338 343 348 353 357 362 372 376", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.349", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.350", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.351", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.352", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.328 334 338 343 348 353 357 362 372 376", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.354", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.355", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.356", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.328 334 338 343 348 353 357 362 372 376", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.358", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.359", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.360", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.361", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.328 334 338 343 348 353 357 362 372 376", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.363", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.364", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.365", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.366", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.367", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.368", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.369", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.370", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.371", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.328 334 338 343 348 353 357 362 372 376", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.373", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.374", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.375", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.328 334 338 343 348 353 357 362 372 376", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.377", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.378", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.379", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.380", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.381", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.382", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.383", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.384", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.385", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.386", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.387", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.388", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.389", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.390", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.391", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.392", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.393", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.394", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.395", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.396", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.397", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.398", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.399", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.400", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.401", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.402", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.403", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.404", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.405", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.406", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.407", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.408", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:64.409", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:65.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:65.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:65.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:65.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:65.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:65.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:65.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:65.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:65.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:65.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:65.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:65.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:65.13", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:65.14", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:65.15", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:65.16", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:65.17", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:65.18", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:65.19", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:65.20", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:65.21", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:65.22", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:65.23", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:65.24", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.13", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.14", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.15", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.16", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.17", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.18", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.19", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.20", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.21", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.22", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.23", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.24", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.25", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.26", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.27", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.28", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.29", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.30", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.31", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.32", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.33", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.34", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.35", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.36", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.37", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.38", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.39", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.40", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.41", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.42", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.43", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.44", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.45", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.46", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.47", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.48", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.49", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.50", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.51", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.52", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.53", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.54", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.55", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.56", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.57", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.58", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.59", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.60", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.61", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.62", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.63", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.64", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.65", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.66", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.67", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.68", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.69", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.70", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.71", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.72", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.73", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.74", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.75", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.76", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.77", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.78", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.79", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.80", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.81", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.82", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.83", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.84", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.85", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.86", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.87", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.88", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.89", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.90", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.91", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.92", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.93", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:66.94", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.13", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.14", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.15", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.16", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.17", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.18", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.19", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.20", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.21", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.22", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.23", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.24", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.25", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.26", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.27", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.28", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.29", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.30", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.31", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.32", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.33", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.34", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.35", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.36", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.37", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.38", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.39", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.40", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.41", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.42", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.43", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.44", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.45", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.46", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.47", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:67.48", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68a.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68a.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68a.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68a.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68a.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68a.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68a.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68a.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68a.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68a.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68a.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68a.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68a.13", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68a.14", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68a.15", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68a.16", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68a.17", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68a.18", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68a.19", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68a.20", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68a.21", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68a.22", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68a.23", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68a.24", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68a.25", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68a.26", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68a.27", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68a.28", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68a.29", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68a.30", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68a.31", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68a.32", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68a.33", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68a.34", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68a.35", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68a.36", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68a.37", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68a.38", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68a.39", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68a.40", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.13", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.14", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.15", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.16", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.17", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.18", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.19", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.20", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.21", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.22", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.23", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.24", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.25", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.26", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.27", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.28", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.29", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.30", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.31", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.32", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.33", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.34", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.35", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.36", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.37", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.38", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.39", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.40", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.41", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.42", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.43", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.44", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.45", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.46", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.47", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.48", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.49", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.50", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.51", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.52", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.53", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.54", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.55", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.56", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.57", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.58", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.59", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.60", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.61", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.62", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.63", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.64", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.65", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.66", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.67", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.68", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.69", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.70", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.71", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.72", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.73", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.74", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.75", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.76", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.77", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.78", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.79", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.80", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.81", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.82", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.83", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.84", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.85", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.86", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.87", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.88", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.89", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.90", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.91", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.92", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.93", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.94", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.95", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.96", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.97", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.98", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.99", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.100", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.101", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.102", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.103", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.104", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.105", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.106", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.107", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.108", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.109", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.110", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.111", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.112", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.113", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.114", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.115", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.116", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.117", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.118", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.119", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:68b.120", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:69.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:69.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:69.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:69.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:69.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:69.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:69.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:69.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:69.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:69.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:70.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:70.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:70.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:70.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:71.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:71.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:71.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:71.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:71.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:71.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:72.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:72.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:72.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:72.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:72.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:72.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:72.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:72.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:73.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:73.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:73.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:73.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:73.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:73.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:74.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:74.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:74.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:74.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:74.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:74.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:75.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:75.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:75.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:75.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:76.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:76.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:76.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:76.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:76.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:76.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:76.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:76.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:76.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:76.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:76.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:76.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:76.13", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:76.14", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:76.15", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:76.16", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:76.17", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:76.18", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:76.19", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:76.20", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:76.21", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:76.22", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:76.23", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:76.24", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:76.25", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:76.26", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:77.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:77.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:77.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:77.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:77.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:77.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:78.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:78.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:78.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:78.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:78.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:78.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:78b.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:78b.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:78b.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:78b.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:78b.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:79.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:79.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:79.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:79.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:80.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:80.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:80.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:80.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:80.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:80.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:80.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:80.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:81.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:81.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:81.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:81.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:81.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:81.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:82.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:82.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:82.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:82.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:83.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:83.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:83.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:83.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:83.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:83.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:84.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:84.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:84.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:84.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:84.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:84.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:84.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:84.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:84.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:84.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:84.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:84.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:85.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:85.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:86.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:86.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:86.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:86.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:86.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:86.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:87.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:87.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:87.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:87.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:88.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:88.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:88.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:88.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:88.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:88.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:88.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:88.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:89.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:89.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:89.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:89.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:89.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:89.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:90.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:90.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:90.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:90.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:90.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:90.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:91.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:91.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:91.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:91.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:91.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:91.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:91.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:91.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:91.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:91.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:92.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:92.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:92.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:92.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:93.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:93.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:94.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:94.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:95.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:95.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:95.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:95.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:95.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:95.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:95.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:95.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:95.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:95.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:96.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:96.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:96.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:96.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:96.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:96.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:97.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:97.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:97.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:97.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:97.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:97.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:97.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:97.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:97.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:97.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:97.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:97.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:98.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:98.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:98.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:98.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:98.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:98.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:99.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:99.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:99.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:99.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:99.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:99.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:99.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:99.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:99.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:99.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:99.11", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:99.12", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:99.13", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:99.14", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:99.15", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:99.16", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:100.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:100.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:100.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:100.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:100.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:100.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:100.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:100.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:101.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:101.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:101.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:101.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:101.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:101.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:101.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:101.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:101.9", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:101.10", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:102.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:102.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:102.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:102.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:103.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:103.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:103.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:103.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:104.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:104.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:104.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:104.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:105.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:105.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:106.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:106.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:107.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:107.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:107.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:107.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:107.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:107.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:107.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:107.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:108.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:108.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:108.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:108.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:108.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:108.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:109.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:109.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:109.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:109.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:109.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:109.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:110.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:110.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:110.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:110.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:110.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:110.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:110.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:110.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:111.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:111.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:111.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:111.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:112.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:112.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:113.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:113.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:113.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:113.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:114.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:114.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:114.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:114.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:114.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:114.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:115.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:115.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:115.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:115.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:115.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:115.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:115.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:115.8", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:116.1", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:116.2", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:116.3", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:116.4", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:116.5", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:116.6", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:116.7", "urn:cts:latinLit:phi0472.phi001.perseus-lat2:116.8"]
        curated_references = Nemo.level_grouper(text, lambda level: data, level=2, groupby=10)

        self.assertIn(
            ("1.1-1.10", "1.1-1.10"),
            curated_references
        )
        self.assertIn(
            ("2.1-2.10", "2.1-2.10"),
            curated_references
        )
        self.assertIn(
            ("2.11-2.13", "2.11-2.13"),
            curated_references
        )

    def test_level_grouper(self):
        """ Test level grouper
        """
        text = self.inventory["urn:cts:latinLit:phi1294.phi002.perseus-lat2"]
        data = ["urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.7", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.8", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.9", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.10", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.11", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.12", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.13", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.14", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.15", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.16", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.17", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.18", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.19", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.20", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.21", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.22", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.1.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.1.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.1.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.1.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.1.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.1.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.2.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.2.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.2.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.2.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.2.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.2.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.2.7", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.2.8", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.3.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.3.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.3.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.3.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.3.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.3.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.3.7", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.3.8", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.3.9", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.3.10", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.3.11", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.3.12", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.4.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.4.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.4.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.4.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.4.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.4.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.4.7", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.4.8", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.5.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.5.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.6.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.6.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.6.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.6.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.6.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.6.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.7.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.7.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.7.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.7.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.7.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.8.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.8.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.8.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.8.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.8.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.8.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.9.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.9.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.10.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.10.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.10.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.10.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.11.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.11.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.11.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.11.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.12.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.12.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.12.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.12.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.12.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.12.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.12.7", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.12.8", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.12.9", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.12.10", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.12.11", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.12.12", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.13.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.13.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.13.3"]
        data = data + ["urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.pr.sa", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.pr.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.pr.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.pr.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.pr.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.pr.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.pr.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.pr.7", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.pr.8", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.pr.9", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.pr.10", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.pr.11", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.pr.12", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.pr.13", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.pr.14", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.pr.15", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.1.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.1.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.1.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.1.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.1.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.1.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.1.7", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.1.8", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.1.9", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.1.10", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.1.11", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.1.12", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.2.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.2.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.2.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.2.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.2.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.2.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.3.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.3.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.4.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.4.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.4.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.4.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.4.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.4.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.4.7", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.4.8", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.5.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.5.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.5.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.5.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.5.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.5.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.5.7", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.5.8", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.6.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.6.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.6.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.6.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.6.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.6.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.6.7", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.6.8", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.6.9", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.6.10", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.6.11", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.6.12", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.6.13", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.6.14", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.6.15", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.6.16", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.6.17", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.7.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.7.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.7.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.7.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.7.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.7.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.7.7", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.7.8", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.8.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.8.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.8.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.8.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.8.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.8.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.8.7", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.8.8", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.9.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.9.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.10.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.10.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.10.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.10.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.11.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.11.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.11.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.11.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.11.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.11.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.11.7", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.11.8", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.11.9", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.11.10", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.12.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.12.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.12.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.12.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.13.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.13.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.14.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.14.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.14.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.14.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.14.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.14.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.14.7", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.14.8", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.14.9", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.14.10", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.14.11", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.14.12", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.14.13", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.14.14", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.14.15", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.14.16", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.14.17", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.14.18", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.15.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.15.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.16.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.16.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.16.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.16.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.16.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.16.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.17.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.17.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.17.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.17.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.17.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.18.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.18.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.18.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.18.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.18.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.18.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.18.7", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.18.8", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.19.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.19.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.19.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.19.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.20.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.20.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.21.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.21.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.22.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.22.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.22.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.22.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.23.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.23.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.23.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.23.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.23.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.24.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.24.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.24.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.24.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.24.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.24.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.24.7", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.24.8", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.25.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.25.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.26.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.26.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.26.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.26.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.27.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.27.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.27.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.27.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.28.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.28.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.28.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.28.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.28.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.28.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.29.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.29.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.29.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.29.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.29.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.29.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.29.7", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.29.8", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.29.9", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.29.10", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.30.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.30.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.30.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.30.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.30.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.30.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.31.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.31.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.32.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.32.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.32.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.32.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.32.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.32.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.32.7", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.32.8", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.33.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.33.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.33.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.33.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.34.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.34.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.34.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.34.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.34.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.34.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.35.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.35.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.36.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.36.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.36.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.36.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.36.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.36.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.37.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.37.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.37.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.37.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.37.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.37.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.37.7", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.37.8", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.37.9", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.37.10", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.37.11", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.38.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.38.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.39.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.39.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.40.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.40.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.40.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.40.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.40.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.40.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.40.7", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.40.8", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.41.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.41.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.41.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.41.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.41.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.41.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.41.7", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.41.8", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.41.9", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.41.10", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.41.11", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.41.12", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.41.13", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.41.14", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.41.15", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.41.16", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.41.17", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.41.18", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.41.19", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.41.20", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.41.21", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.41.22", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.41.23", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.42.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.42.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.43.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.43.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.43.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.43.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.43.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.43.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.43.7", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.43.8", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.43.9", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.43.10", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.43.11", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.43.12", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.43.13", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.43.14", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.43.15", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.43.16", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.44.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.44.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.44.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.44.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.44.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.44.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.44.7", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.44.8", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.44.9", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.44.10", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.44.11", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.44.12", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.45.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.45.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.46.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.46.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.46.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.46.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.46.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.46.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.46.7", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.46.8", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.46.9", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.46.10", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.47.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.47.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.47.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.47.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.48.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.48.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.48.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.48.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.48.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.48.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.48.7", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.48.8", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.49.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.49.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.50.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.50.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.51.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.51.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.51.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.51.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.51.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.51.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.52.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.52.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.53.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.53.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.53.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.53.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.53.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.53.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.53.7", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.53.8", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.53.9", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.53.10", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.54.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.54.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.54.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.54.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.54.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.55.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.55.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.55.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.56.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.56.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.56.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.56.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.57.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.57.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.57.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.57.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.57.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.57.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.57.7", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.57.8", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.58.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.58.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.59.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.59.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.59.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.59.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.60.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.60.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.60.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.60.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.61.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.61.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.61.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.61.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.61.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.61.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.61.7", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.61.8", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.62.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.62.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.62.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.62.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.63.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.63.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.63.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.63.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.64.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.64.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.64.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.64.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.64.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.64.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.64.7", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.64.8", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.64.9", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.64.10", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.65.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.65.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.65.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.65.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.65.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.65.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.66.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.66.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.66.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.66.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.66.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.66.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.66.7", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.66.8", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.67.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.67.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.67.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.67.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.68.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.68.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.68.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.68.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.68.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.68.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.68.7", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.68.8", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.68.9", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.69.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.69.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.69.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.69.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.69.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.69.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.69.7", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.69.8", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.70.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.70.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.70.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.70.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.70.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.71.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.71.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.71.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.71.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.71.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.71.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.72.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.72.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.72.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.72.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.72.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.72.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.72.7", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.72.8", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.73.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.74.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.74.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.74.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.74.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.74.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.74.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.74.7", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.75.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.75.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.75.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.75.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.75.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.75.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.75.7", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.75.8", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.75.9", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.75.10", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.76.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.76.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.77.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.77.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.77.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.77.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.77.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.77.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.77.7", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.77.8", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.78.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.78.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.79.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.79.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.80.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.80.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.81.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.81.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.82.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.82.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.83.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.83.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.83.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.83.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.83.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.84.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.84.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.84.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.84.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.85.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.85.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.85.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.85.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.86.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.86.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.86.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.86.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.86.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.86.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.86.7", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.86.8", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.86.9", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.86.10", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.86.11", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.86.12", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.87.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.87.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.88.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.88.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.89.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.89.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.89.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.89.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.89.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.89.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.90.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.90.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.90.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.90.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.90.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.90.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.90.7", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.90.8", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.90.9", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.90.10", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.91.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.91.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.91.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.91.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.91.5", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.91.6", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.91.7", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.91.8", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.92.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.92.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.92.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.92.4", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.93.1", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.93.2", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.93.3", "urn:cts:latinLit:phi1294.phi002.perseus-lat2:2.93.4"]
        curated_references = Nemo.level_grouper(text, lambda level: data, level=3, groupby=10)

        self.assertIn(
            ("1.pr.1-1.pr.10", "1.pr.1-1.pr.10"),
            curated_references
        )
        self.assertIn(
            ("2.1.1-2.1.10", "2.1.1-2.1.10"),
            curated_references
        )
        self.assertIn(
            ("2.1.11-2.1.12", "2.1.11-2.1.12"),
            curated_references
        )