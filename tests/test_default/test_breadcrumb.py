from ..resources import NemoResource
from mock import patch
from flask_nemo.default import Breadcrumb


class TestBreadcrumb(NemoResource):
    """ Test Breadcrumb default Plugins
    """
    def test_make_passage_breadcrumb(self):
        """ passage breadcrumb should include all components up to passage and passage not linked
        """
        with patch("requests.get", return_value=self.getCapabilities):
            make_breadcrumbs = Breadcrumb().render
            bc = make_breadcrumbs(
                textgroups=self.nemo.get_textgroups(),
                version=self.nemo.get_text("latinLit", "phi1294", "phi002", "perseus-lat2"),
                lang="eng",
                url={
                    "collection": "latinLit",
                    "textgroup": "phi1294",
                    "work": "phi002",
                    "version": "perseus-lat2",
                    "passage_identifier": "1.1"
                    })["breadcrumbs"]
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
            make_breadcrumbs = Breadcrumb().render
            bc = make_breadcrumbs(
                textgroups=self.nemo.get_textgroups(),
                version = self.nemo.get_text("latinLit","phi1294","phi002","perseus-lat2"),
                lang="eng",
                url={
                    "collection": "latinLit",
                    "textgroup": "phi1294",
                    "work": "phi002",
                    "version": "perseus-lat2"
                    })["breadcrumbs"]
            self.assertEqual(bc,[
                {'link': '.r_collection', 'title': 'latinLit', 'args': {'collection': 'latinLit'}},
                {'link': '.r_texts', 'title': 'Martial', 'args': {'textgroup': 'phi1294', 'collection': 'latinLit'}},
                {'link': None, 'title': 'Epigrammata Label', 'args': {'textgroup': 'phi1294', 'collection': 'latinLit', 'work':'phi002','version':'perseus-lat2'}}
            ])

    def test_make_textgroup_breadcrumb(self):
        """ textgroup breadcrumb should include all components up to textgroup and textgroup not linked
        """
        with patch("requests.get", return_value=self.getCapabilities):
            make_breadcrumbs = Breadcrumb().render
            bc = make_breadcrumbs(
                textgroups=self.nemo.get_textgroups(),
                lang="eng",
                url={
                    "collection": "latinLit",
                    "textgroup": "phi1294",
                    })["breadcrumbs"]
            self.assertEqual(bc, [
                {'link': '.r_collection', 'title': 'latinLit', 'args': {'collection': 'latinLit'}},
                {'link': None, 'title': 'Martial', 'args': {'textgroup': 'phi1294', 'collection': 'latinLit'}}
            ])

    def test_make_collection_breadcrumb(self):
        """ collection breadcrumb should include only collection not linked
        """
        with patch("requests.get", return_value=self.getCapabilities):
            make_breadcrumbs = Breadcrumb().render
            bc = make_breadcrumbs(
                lang="eng",
                url={"collection": "latinLit"})["breadcrumbs"]
            self.assertEqual(bc, [
                {'link': None, 'title': 'latinLit', 'args': {'collection': 'latinLit'}}
            ])
