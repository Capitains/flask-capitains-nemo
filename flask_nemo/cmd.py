from flask_nemo import Nemo
from flask_nemo.chunker import level_grouper
from flask import Flask
from MyCapytain.resolvers.cts.api import HttpCtsResolver
from MyCapytain.resolvers.cts.local import CtsCapitainsLocalResolver
from MyCapytain.retrievers.cts5 import HttpCtsRetriever
import argparse
import sys


class Server:
    @staticmethod
    def runner(method, address, port, host, css, xslt, groupby, debug):
        resolver = None
        app = Flask(
            __name__
        )
        if method == "cts-api":
            resolver = HttpCtsResolver(HttpCtsRetriever(address))
        elif method == "cts-local":
            resolver = CtsCapitainsLocalResolver([address])
        if xslt is not None:
            xslt = {"default": xslt}
        # We set up Nemo
        nemo = Nemo(
            app=app,
            name="nemo",
            base_url="",
            css=css,
            transform=xslt,
            resolver=resolver,
            chunker={"default": lambda x, y: level_grouper(x, y, groupby=groupby)}
        )

        # We run the app
        app.debug = debug
        app.run(port=port, host=host)
        # For test purposes
        return nemo, app

    @staticmethod
    def parser(args):
        parser = argparse.ArgumentParser(
            description="""Capitains Nemo UI
        Currently, can be used with either a CTS API Address or a local CapiTainS repository"""
        )
        parser.add_argument('method', type=str, choices=["cts-api", "cts-local"],
                           help='Method to retrieve resource')
        parser.add_argument('address', type=str, default=None,
                           help="""Path or address of the resource required by method
    - Local CapiTainS repository [ http://capitains.github.io/pages/guidelines ]
    - HTTP CTS Address
    """)
        parser.add_argument('--port', type=int, default=8000,
                           help='Port to use for the HTTP Server')
        parser.add_argument('--host', type=str, default="127.0.0.1",
                           help='Host to use for the HTTP Server')
        parser.add_argument('--css', type=str, default=None, nargs='*',
                           help='Full path to secondary css file')
        parser.add_argument('--xslt', type=str, default=None,
                           help='Default XSLT to use')
        parser.add_argument('--groupby', type=int, default=25,
                           help='Number of passage to group in the deepest level of the hierarchy')
        parser.add_argument('--debug', action="store_true", default=False, help="Set-up the application for debugging")

        args = vars(parser.parse_args(args))
        print("Running with {}".format(" ".join(["{}={}".format(k, v) for k, v in args.items()])))
        return Server.runner(**args)

    @staticmethod
    def cmd():
        return Server.parser(sys.argv[1:])

if __name__ == "__main__":
    Server.cmd()
