from flask_nemo.cmd import Server
from unittest import TestCase, mock
import sys
from io import StringIO
from mock import patch
import flask
from MyCapytain.resolvers.cts.api import HttpCtsResolver
from MyCapytain.resolvers.cts.local import CtsCapitainsLocalResolver


class TestCommands(TestCase):

    @patch("flask.Flask.run")
    def server(self, args, run=None):
        """ Run args (Splitted list of command line)
        ..note:: See https://wrongsideofmemphis.wordpress.com/2010/03/01/store-standard-output-on-a-variable-in-python/
        :param args: List of commandline arguments
        :return: Sys stdout, status
        """
        args = [sys.argv[0]] + args
        # This variable will store everything that is sent to the standard output
        result = StringIO()
        with patch("sys.stdout", result):
            # Here we can call anything we like, like external modules, and everything
            # that they will send to standard output will be stored on "result"
            with mock.patch('sys.argv', args):
                nemo, app = Server.cmd()

        # Then, get the stdout like a string and process it!
        result_string = result.getvalue()

        return nemo, app, result_string, run

    def test_run_local_no_option(self):
        """ Test a run which fails"""
        with self.assertRaises(SystemExit):
            self.server([])

    def test_run_http(self):
        """ Test a run on the remote tests passages """
        nemo, app, stdout, run = self.server(["cts-api", "https://cts.perseids.org/api/cts/"])
        run.assert_called_with(host='127.0.0.1', port=8000)  # Called with defaults
        args_called = 0
        arguments = [
            "groupby=25", "xslt=None", "address=https://cts.perseids.org/api/cts/",
            "css=None", "host=127.0.0.1", "port=8000", "debug=False", "method=cts-api", "Running", "with"
        ]
        for printed in arguments:
            self.assertIn(printed, stdout.split(), "Variables should be printed")
            args_called += 1
        self.assertEqual(args_called, len(arguments), "There should be as many tests as printed output checked")

        self.assertIsInstance(nemo.resolver, HttpCtsResolver, "We should have a CTS Remote Resolver")
        self.assertEqual(
            nemo.resolver.endpoint.endpoint,
            "https://cts.perseids.org/api/cts/",
            "We should have a CTS Remote Resolver with given address"
        )

    def test_run_local_xslt(self):
        """ Test a run on the local tests passages with XSLT"""
        nemo, app, stdout, run = self.server(
            [
                "cts-local", "./tests/test_data/nautilus/farsiLit",
                "--xslt", "./tests/test_data/xsl_test.xml"
            ]
        )
        run.assert_called_with(host='127.0.0.1', port=8000)  # Called with defaults
        args_called = 0
        arguments = [
            "groupby=25", "xslt=./tests/test_data/xsl_test.xml", "address=./tests/test_data/nautilus/farsiLit",
            "css=None", "host=127.0.0.1", "port=8000", "debug=False", "method=cts-local", "Running", "with"
        ]
        for printed in arguments:
            self.assertIn(printed, stdout.split(), "Variables should be printed")
            args_called += 1
        self.assertEqual(args_called, len(arguments), "There should be as many tests as printed output checked")

        self.assertIsInstance(nemo.resolver, CtsCapitainsLocalResolver, "We should have a CTS Remote Resolver")

        test_client = app.test_client()

        data = test_client.get("/text/urn:cts:farsiLit:hafez.divan.perseus-ger1/passage/1.1.1.1-1.1.1.4").data.decode()
        self.assertIn(
            '<tei:notbody xmlns:tei="http://www.tei-c.org/ns/1.0">', data,
            "Transformation should have happened"
        )

    def test_run_local_css(self):
        """ Test a run on the local tests passages """
        nemo, app, stdout, run = self.server(
            [
                "cts-local", "./tests/test_data/nautilus/farsiLit",
                "--css", "./tests/test_data/empty.css"
            ]
        )
        run.assert_called_with(host='127.0.0.1', port=8000)  # Called with defaults
        self.assertEqual(app.debug, False)
        args_called = 0
        arguments = [
            "groupby=25", "xslt=None", "address=./tests/test_data/nautilus/farsiLit",
            "css=['./tests/test_data/empty.css']", "host=127.0.0.1", "port=8000", "debug=False",
            "method=cts-local", "Running", "with"
        ]
        for printed in arguments:
            self.assertIn(printed, stdout.split(), "Variables should be printed")
            args_called += 1
        self.assertEqual(args_called, len(arguments), "There should be as many tests as printed output checked")

        self.assertIsInstance(nemo.resolver, CtsCapitainsLocalResolver, "We should have a CTS Remote Resolver")

        test_client = app.test_client()

        data = test_client.get("/collections/urn:cts:farsiLit:hafez.divan").data.decode()
        self.assertIn(
            '<link rel="stylesheet" href="/assets/nemo.secondary/css/empty.css">', data,
            "CSS should be there"
        )

    def test_run_local_port_address(self):
        """ Test a run on the local tests passages """
        nemo, app, stdout, run = self.server(
            [
                "cts-local", "./tests/test_data/nautilus/farsiLit",
                "--port", "5000", "--host", "localhost", "--debug"
            ]
        )
        run.assert_called_with(host='localhost', port=5000)  # Called with defaults
        self.assertEqual(app.debug, True)
        args_called = 0
        arguments = [
            "groupby=25", "xslt=None", "address=./tests/test_data/nautilus/farsiLit",
            "css=None", "host=localhost", "port=5000", "debug=True",
            "method=cts-local", "Running", "with"
        ]
        for printed in arguments:
            self.assertIn(printed, stdout.split(), "Variables should be printed")
            args_called += 1
        self.assertEqual(args_called, len(arguments), "There should be as many tests as printed output checked")

        self.assertIsInstance(nemo.resolver, CtsCapitainsLocalResolver, "We should have a CTS Remote Resolver")