from jinja2 import nodes
from jinja2.ext import Extension


class FakeCacheExtension(Extension):
    """ This extension exists only to avoid breaks in Nemo if FlaskCache is not used.
    Not that if you'd load Flask Cache en

    """
    tags = set(['cache'])

    def parse(self, parser):
        lineno = next(parser.stream).lineno

        #: Parse timeout
        args = [parser.parse_expression()]

        #: Parse fragment name
        #: Grab the fragment name if it exists
        #: otherwise, default to the old method of using the templates
        #: lineno to maintain backwards compatibility.
        if parser.stream.skip_if('comma'):
            args.append(parser.parse_expression())
        else:
            args.append(nodes.Const("%s%s" % (parser.filename, lineno)))

        #: Parse vary_on parameters
        vary_on = []
        while parser.stream.skip_if('comma'):
            vary_on.append(parser.parse_expression())

        if vary_on:
            args.append(nodes.List(vary_on))
        else:
            args.append(nodes.Const([]))

        body = parser.parse_statements(['name:endcache'], drop_needle=True)
        return nodes.CallBlock(self.call_method('_do_nothing', args),
                               [], [], body).set_lineno(lineno)

    def _do_nothing(self, timeout, fragment_name, vary_on, caller):
        return caller()
