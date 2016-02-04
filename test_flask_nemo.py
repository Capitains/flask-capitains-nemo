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
