"""

Test file for chunkers and groupers.

- Chunkers and groupers are supposed to be app context dependant
- They should always take the same kind of data

"""

from MyCapytain.resources.collections.cts import XmlCtsTextInventoryMetadata
from tests.test_resources import NemoResource, NautilusDummy
from flask_nemo.chunker import default_chunker, line_chunker, scheme_chunker, level_chunker, level_grouper


class TestChunkers(NemoResource):

    def setUp(self):
        super(TestChunkers, self).setUp()
        self.inventory = XmlCtsTextInventoryMetadata.parse(resource=self.getCapabilities.text)

    def test_default_chunker(self):
        """ Test default chunker
        """
        text = self.inventory["urn:cts:latinLit:phi1294.phi002.perseus-lat2"]
        reffs = default_chunker(text, lambda level: NautilusDummy.getReffs('urn:cts:latinLit:phi1294.phi002.perseus-lat2',
                                                                           level=3))
        self.assertIn(("1.pr.1", "1.pr.1"), reffs)
        self.assertIn(('1.1.6', '1.1.6'), reffs)

    def test_line_chunker(self):
        """ Test line grouping chunker
        """

        text = self.inventory["urn:cts:latinLit:phi1294.phi002.perseus-lat2"]
        validReff = lambda level: NautilusDummy.getReffs('urn:cts:latinLit:phi1294.phi002.perseus-lat2', level=level)
        reffs = line_chunker(text, validReff, 5)
        for x in [
            ("1.pr.1-1.pr.5", "1.pr.1"),
            ("1.pr.6-1.pr.10", "1.pr.6"),
            ("1.pr.11-1.pr.15", "1.pr.11"),
            ("1.pr.16-1.pr.20", "1.pr.16"),
            ("1.pr.21-1.1.3", "1.pr.21") # should cross over the boundary of the single poem
        ]:
            self.assertIn(x, reffs)

        reffs = line_chunker(text, validReff, 11)
        for x in [
            ("1.pr.1-1.pr.11", "1.pr.1"),
            ("1.pr.12-1.pr.22", "1.pr.12")
        ]:
            self.assertIn(x, reffs)

    def test_scheme_chunker(self):
        """ Test chunking according to scheme
        """
        # When the scheme is book, poem, line, the scheme_chunker should chunk poems together
        text = self.inventory["urn:cts:latinLit:phi1294.phi002.perseus-lat2"] # book, poem, line
        reffs = scheme_chunker(text, lambda level: NautilusDummy.getReffs('urn:cts:latinLit:phi1294.phi002.perseus-lat2',
                                                                          level=level))
        for x in [
            ("1.pr", "1.pr"),
            ("2.15", "2.15")
        ]:
            self.assertIn(x, reffs)

        # If the scheme is only book and line, the line chunker should be used
        text = self.inventory['urn:cts:latinLit:phi0959.phi007.perseus-lat2'] # book, line
        reffs = scheme_chunker(text, lambda level: NautilusDummy.getReffs('urn:cts:latinLit:phi1294.phi002.perseus-lat2',
                                                                          level=level))
        # The chunks are not actually lines but, instead, full poems.
        # But it still shows that the scheme_chunker works correctly.
        for x in [
            ("1.pr-1.29", "1.pr"),
            ("1.90-2.pr", "1.90")
        ]:
            self.assertIn(x, reffs)

        # If the scheme does not contain poem, then it should use the default chunker
        text = NautilusDummy.getMetadata('urn:cts:latinLit:stoa0275.stoa027.perseus-lat2') # chapter, section
        reffs = scheme_chunker(text, lambda level: NautilusDummy.getReffs('urn:cts:latinLit:stoa0275.stoa027.perseus-lat2',
                                                                          level=level))
        for x in [
            ("1.1", "1.1"),
            ("2.1", "2.1")
        ]:
            self.assertIn(x, reffs)

    def test_level_chunker(self):
        """ Test chunking according to scheme
        """
        # level 1
        text = self.inventory["urn:cts:latinLit:phi1294.phi002.perseus-lat2"]  # book, poem
        reffs = level_chunker(text, lambda level: NautilusDummy.getReffs('urn:cts:latinLit:phi1294.phi002.perseus-lat2',
                                                                          level=level), level=1)
        for x in [
            ("1", "1"),
            ("2", "2")
        ]:
            self.assertIn(x, reffs)

        # level 2
        text = self.inventory["urn:cts:latinLit:phi1294.phi002.perseus-lat2"]  # book, poem
        reffs = level_chunker(text, lambda level: NautilusDummy.getReffs('urn:cts:latinLit:phi1294.phi002.perseus-lat2',
                                                                          level=level), level=2)
        for x in [
            ("1.1", "1.1"),
            ("2.1", "2.1")
        ]:
            self.assertIn(x, reffs)

        # level 3
        text = self.inventory["urn:cts:latinLit:phi1294.phi002.perseus-lat2"]  # book, poem
        reffs = level_chunker(text, lambda level: NautilusDummy.getReffs('urn:cts:latinLit:phi1294.phi002.perseus-lat2',
                                                                          level=level), level=3)
        for x in [
            ("1.1.1", "1.1.1"),
            ("2.1.1", "2.1.1")
        ]:
            self.assertIn(x, reffs)

    def test_level_grouper(self):
        """ Test level grouper
        """
        text = self.inventory["urn:cts:latinLit:phi1294.phi002.perseus-lat2"]
        curated_references = level_grouper(text, lambda level: NautilusDummy.getReffs('urn:cts:latinLit:phi1294.phi002.perseus-lat2',
                                                                                      level=level),
                                           level=2, groupby=10)

        self.assertIn(
            ('1.pr-1.9', '1.pr-1.9'),
            curated_references
        )
        self.assertIn(
            ('2.pr-2.9', '2.pr-2.9'),
            curated_references
        )
        self.assertIn(
            ('2.90-2.93', '2.90-2.93'),
            curated_references
        )

        """
            Second part of the test
        """

        curated_references = level_grouper(text, lambda level: NautilusDummy.getReffs('urn:cts:latinLit:phi1294.phi002.perseus-lat2',
                                                                                      level=level),
                                           level=3, groupby=10)

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
