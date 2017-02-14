from tests.test_resources import NemoResource
from mock import patch
from flask_nemo.plugins.default import Breadcrumb


class TestBreadcrumb(NemoResource):
    """ Test Breadcrumb default Plugins
    """

    def test_make_collection_breadcrumb_shorter(self):
        """ collection breadcrumb should include only collection not linked
        """
        with patch("requests.get", return_value=self.getCapabilities):
            make_breadcrumbs = Breadcrumb().render
            bc = make_breadcrumbs(
                lang="eng",
                collections={
                    'current': {
                        'model': 'http://w3id.org/dts-ontology/resource',
                        'label': 'Divān (English)',
                        'type': 'http://chs.harvard.edu/xmlns/cts/CTSCollection',
                        'id': 'urn:cts:farsiLit:hafez.divan.perseus-eng1'
                    },
                    'parents': [{
                        'model': 'http://w3id.org/dts-ontology/collection',
                        'size': 3,
                        'id': 'urn:cts:farsiLit:hafez.divan',
                        'type': 'http://chs.harvard.edu/xmlns/cts/CTSCollection',
                        'label': 'Divān'
                    }, {
                        'model': 'http://w3id.org/dts-ontology/collection',
                        'size': 1,
                        'id': 'urn:cts:farsiLit:hafez',
                        'type': 'http://chs.harvard.edu/xmlns/cts/CTSCollection',
                        'label': 'Hafez'
                    }]
                }
            )["breadcrumbs"]
            self.assertEqual(bc, [{
                'title': 'Text Collections',
                'args': {},
                'link': '.r_collections'
            }, {
                'title': 'Hafez',
                'args': {
                    'objectId': 'urn:cts:farsiLit:hafez',
                    'semantic': 'hafez'
                },
                'link': '.r_collection_semantic'
            }, {
                'title': 'Divān',
                'args': {
                    'objectId': 'urn:cts:farsiLit:hafez.divan',
                    'semantic': 'divan'
                },
                'link': '.r_collection_semantic'
            }, {
                'title': 'Divān (English)',
                'args': {},
                'link': None
            }])


    def test_make_collection_breadcrumb(self):
        """ collection breadcrumb should include only collection not linked
        """
        with patch("requests.get", return_value=self.getCapabilities):
            make_breadcrumbs = Breadcrumb().render
            bc = make_breadcrumbs(
                lang="eng",
                collections={
                    'current': {
                        'model': 'http://w3id.org/dts-ontology/resource',
                        'label': 'Divān (English)',
                        'type': 'http://chs.harvard.edu/xmlns/cts/CTSCollection',
                        'id': 'urn:cts:farsiLit:hafez.divan.perseus-eng1'
                    },
                    'parents': [{
                        'model': 'http://w3id.org/dts-ontology/collection',
                        'size': 3,
                        'id': 'urn:cts:farsiLit:hafez.divan',
                        'type': 'http://chs.harvard.edu/xmlns/cts/CTSCollection',
                        'label': 'Divān'
                    }, {
                        'model': 'http://w3id.org/dts-ontology/collection',
                        'size': 1,
                        'id': 'urn:cts:farsiLit:hafez',
                        'type': 'http://chs.harvard.edu/xmlns/cts/CTSCollection',
                        'label': 'Hafez'
                    }, {
                        'model': 'http://w3id.org/dts-ontology/collection',
                        'size': 1,
                        'id': 'urn:perseus:farsiLit',
                        'type': 'http://chs.harvard.edu/xmlns/cts/CTSCollection',
                        'label': 'Farsi'
                    }]
                }
            )["breadcrumbs"]
            self.assertEqual(bc, [{
                'title': 'Text Collections',
                'args': {},
                'link': '.r_collections'
            }, {
                'title': 'Farsi',
                'args': {
                    'objectId': 'urn:perseus:farsiLit',
                    'semantic': 'farsi'
                },
                'link': '.r_collection_semantic'
            }, {
                'title': 'Hafez',
                'args': {
                    'objectId': 'urn:cts:farsiLit:hafez',
                    'semantic': 'hafez'
                },
                'link': '.r_collection_semantic'
            }, {
                'title': 'Divān',
                'args': {
                    'objectId': 'urn:cts:farsiLit:hafez.divan',
                    'semantic': 'divan'
                },
                'link': '.r_collection_semantic'
            }, {
                'title': 'Divān (English)',
                'args': {},
                'link': None
            }])
