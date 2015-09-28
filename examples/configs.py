from flask.ext.nemo import Nemo

configs = {
    # The CIHAM project is made of critical editions. We load for it a specific xslt to render the result of GetPassage
    # And specifics assets
   "ciham" : {
        "api_url": "http://services2.perseids.org/exist/restxq/cts",
        "base_url": "",
        "inventory": "nemo",
        "xslt": "examples/ciham.xslt",  # Use default epidoc XSLT
        "css": [
            "examples/ciham.css"
        ]
    },
    "default": {
        "api_url": "http://services2.perseids.org/exist/restxq/cts",
        "base_url": "",
        "inventory": "nemo",
        "chunker": {
            # The default chunker takes care of book, poem, lines
            # but it would be cool to have 30 lines group for Nemo
            "urn:cts:latinLit:phi1294.phi002.perseus-lat2": lambda text, cb: [(reff.split(":")[-1], reff.split(":")[-1]) for reff in cb(2)],
            "default": Nemo.scheme_chunker  # lambda text, cb: Nemo.line_grouper(text, cb, 50)
        }
    }
}
