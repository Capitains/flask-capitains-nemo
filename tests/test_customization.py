"""

    Test implementation of customization through init for example

"""

from .resources import NemoResource
from flask_nemo import Nemo
import MyCapytain
from lxml import etree


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
            "default": "tests/test_data/xsl_test.xml"
        })
        transformed = nemo.transform(
            MyCapytain.resources.inventory.Text(
                urn="urn:cts:phi1294.phi002.perseus-lat2"
            ),
            etree.fromstring('<tei:body xmlns:tei="http://www.tei-c.org/ns/1.0" />')
        )
        self.assertEqual(transformed, '<tei:notbody xmlns:tei="http://www.tei-c.org/ns/1.0"></tei:notbody>',
            "It should autoclose the tag"
        )
