import lxml.etree as etree
from flask import Markup
from flask_nemo.chunker import scheme_chunker, level_grouper
from flask.ext.nemo import Nemo


configs = {
    # The CIHAM project is made of critical editions. We load for it a specific xslt to render the result of GetPassage
    # And specifics assets
    "ciham": {
        "api_url": "http://services2.perseids.org/exist/restxq/cts",
        "base_url": "",
        "inventory": "nemo",
        "transform": {"default" : "examples/ciham.xslt"},  # Use own xsl
        "css": [
            # USE Own CSS
            "examples/ciham.css"
        ],
        "js": [
            # use own js file to load a script to go from normalized edition to diplomatic one.
            "examples/ciham.js"
        ],
        "templates":{
            "menu": "examples/ciham"
        },
        "chunker": {
            # The default chunker takes care of book, poem, lines
            # but it would be cool to have 30 lines group for Nemo
            "urn:cts:froLit:jns915.jns1856.ciham-fro1": lambda text, cb: [(reff.split(":")[-1], reff.split(":")[-1]) for reff in cb(1)],
            "default": scheme_chunker  # lambda text, cb: Nemo.line_grouper(text, cb, 50)
        }
    },
    "translations": {
        "api_url": "http://services2.perseids.org/exist/restxq/cts",
        "base_url": "",
        "inventory": "nemo",
        "urls" : Nemo.ROUTES + [("/read/<collection>/<textgroup>/<work>/<version>/<passage_identifier>/<visavis>", "r_double", ["GET"])],
        "css": [
            "examples/translations.css"
        ],
        "chunker": {
            # The default chunker takes care of book, poem, lines
            # but it would be cool to have 30 lines group for Nemo
            "urn:cts:froLit:jns915.jns1856.ciham-fro1": lambda text, cb: [(reff.split(":")[-1], reff.split(":")[-1]) for reff in cb(1)],
            "default": scheme_chunker  # lambda text, cb: Nemo.line_grouper(text, cb, 50)
        },
        "templates": {
            "double": "./examples/translations"
        }
    },
    "chunker": {
        "api_url": "http://localhost:5000",
        "base_url": "",
        "inventory": "nemo",
        "chunker": {
            # The default chunker takes care of book, poem, lines
            # but it would be cool to have 30 lines group for Nemo
            "urn:cts:latinLit:phi1294.phi002.perseus-lat2": lambda text, cb: [(reff.split(":")[-1], reff.split(":")[-1]) for reff in cb(2)],
            "default": level_grouper  # lambda text, cb: Nemo.line_grouper(text, cb, 50)
        },
        "css" : [
            # Use teibp from default nemo configuration
            "examples/tei.pb.min.css"
        ]
    },
    "default": {
        "api_url": "http://services2.perseids.org/exist/restxq/cts",
        "base_url": "",
        "inventory": "nemo",
        "css" : [
            # Use teibp from default nemo configuration
            "examples/tei.pb.min.css",
            "static/nemo.min.css"
        ]
    }
}


class NemoDouble(Nemo):
    """ Implementation of Nemo with a new route accepting a second version for comparison.

    """
    def r_double(self, collection, textgroup, work, version, passage_identifier, visavis):
        """ Optional route to add a visavis version

        :param collection: Collection identifier
        :type collection: str
        :param textgroup: Textgroup Identifier
        :type textgroup: str
        :param work: Work identifier
        :type work: str
        :param version: Version identifier
        :type version: str
        :param passage_identifier: Reference identifier
        :type passage_identifier: str
        :param version: Visavis version identifier
        :type version: str
        :return: Template, version inventory object and Markup object representing the text
        :rtype: {str: Any}

        .. todo:: Change text_passage to keep being lxml and make so self.render turn etree element to Markup.
        """

        # Simply call the url of the
        args = self.r_passage(collection, textgroup, work, version, passage_identifier)
        # Call with other identifiers and add "visavis_" front of the argument
        args.update({"visavis_{0}".format(key): value for key, value in self.r_passage(collection, textgroup, work, visavis, passage_identifier).items()})
        args["template"] = "double::r_double.html"
        return args


classes = {
    "default": Nemo,
    "ciham": Nemo,
    "chunker": Nemo,
    "translations": NemoDouble
}
