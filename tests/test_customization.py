"""

    Test implementation of customization through init for example

"""

from tests.test_resources import NemoResource
from flask_nemo import Nemo
from MyCapytain.resources.collections.cts import Text
from lxml import etree
from tests.test_resources import NautilusDummy


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
            Text(
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
            Text(
                urn="urn:cts:phi1294.phi002.perseus-lat2"
            ),
            ["1.pr"]
        )
        self.assertEqual(chunked, [("1.pr", "I PR")])

    def test_transform_default_function(self):
        """ Test that the transform default is called and applied when it's a function
        """
        urn_given = "urn:cts:latinLit:phi1294.phi002.perseus-lat2"
        ref_given = "1.pr.1"

        def default(work, xml, objectId, subreference=None):
            self.assertEqual(str(work.urn), "urn:cts:latinLit:phi1294.phi002.perseus-lat2")
            self.assertEqual(objectId, urn_given, "Passage URN should be passed to transform")
            self.assertEqual(subreference, ref_given, "Passage URN should be passed to transform")
            self.assertEqual(xml, "<a></a>")
            return "<b></b>"

        nemo = Nemo(transform={
            "default": default
        })
        transformed = nemo.transform(
            Text(
                urn="urn:cts:latinLit:phi1294.phi002.perseus-lat2"
            ),
            "<a></a>",
            urn_given,
            ref_given
        )
        self.assertEqual(transformed, "<b></b>")

    def test_transform_default_none(self):
        """ Test that the transform default is called and applied
        """
        nemo = Nemo()
        transformed = nemo.transform(
            Text(
                urn="urn:cts:phi1294.phi002.perseus-lat2"
            ),
            etree.fromstring("<a/>"),
            "urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.1"
        )
        self.assertEqual(transformed, "<a/>")

    def test_transform_urn_xslt(self):
        """ Test that the transform default is called and applied
        """

        nemo = Nemo(transform={
            "default": "tests/test_data/xsl_test.xml"
        })
        transformed = nemo.transform(
            Text(
                urn="urn:cts:latinLit:phi1294.phi002.perseus-lat2"
            ),
            etree.fromstring('<tei:body xmlns:tei="http://www.tei-c.org/ns/1.0" />'),
            objectId="urn:cts:latinLit:phi1294.phi002.perseus-lat2",
            subreference="1.pr.1"
        )
        self.assertEqual(transformed, '<tei:notbody xmlns:tei="http://www.tei-c.org/ns/1.0"></tei:notbody>',
            "It should autoclose the tag"
        )

    def test_transform_match(self):
        """ Test that the transform default is called and applied
        """

        nemo = Nemo(transform={
            "default": lambda x: self.assertEqual(False, True, "This should not be run"),
            "urn:cts:latinLit:phi1294.phi002.perseus-lat2": "tests/test_data/xsl_test.xml"
        })
        transformed = nemo.transform(
            Text(
                urn="urn:cts:latinLit:phi1294.phi002.perseus-lat2"
            ),
            etree.fromstring('<tei:body xmlns:tei="http://www.tei-c.org/ns/1.0" />'),
            objectId="urn:cts:latinLit:phi1294.phi002.perseus-lat2",
            subreference="1.pr.1"
        )
        self.assertEqual(transformed, '<tei:notbody xmlns:tei="http://www.tei-c.org/ns/1.0"></tei:notbody>',
            "It should autoclose the tag"
        )
