from flask import Flask
from flask_nemo import Nemo
from flask_nemo.plugin import PluginPrototype
from flask_nemo.filters import f_formatting_passage_reference
from tests.resources import NemoResource


class FilterPlugin(PluginPrototype):
    FILTERS = ["f_make_string"]

    def f_make_string(self, number):
        return str(number)


class FilterPluginOverride(PluginPrototype):
    FILTERS = ["f_formatting_passage_reference"]

    def f_formatting_passage_reference(self, number):
        return str(number)


class TestPluginFilters(NemoResource):
    """ Test plugin implementation of filters
    """

    def test_register_filter(self):
        app = Flask(__name__)
        plug = FilterPlugin()
        self.nemo = Nemo(app=app, plugins=[plug])
        self.assertEqual(
            self.nemo.app.jinja_env.filters["formatting_passage_reference"],
            f_formatting_passage_reference,
            "Original Nemo filters should be kept"
        )
        self.assertEqual(
            self.nemo.app.jinja_env.filters["make_string"],
            plug.f_make_string,
            "Plugin filters should be registered"
        )

    def test_register_filter_override(self):
        app = Flask(__name__)
        plug = FilterPluginOverride()
        self.nemo = Nemo(app=app, plugins=[plug])
        self.assertEqual(
            self.nemo.app.jinja_env.filters["formatting_passage_reference"],
            plug.f_formatting_passage_reference,
            "Original Nemo filters should be override by newly registered filters"
        )

    def test_register_filter_namespace(self):
        app = Flask(__name__)

        plug = FilterPluginOverride(namespacing=True, name="no_override")
        plug_noname = FilterPluginOverride(namespacing=True)

        self.nemo = Nemo(app=app, plugins=[plug, plug_noname])
        self.assertEqual(
            self.nemo.app.jinja_env.filters["formatting_passage_reference"],
            f_formatting_passage_reference,
            "Original Nemo filters should be kept when namespacing is done"
        )
        self.assertEqual(
            self.nemo.app.jinja_env.filters["no_override_formatting_passage_reference"],
            plug.f_formatting_passage_reference,
            "Original Nemo filters should be override by newly registered filters"
        )
        self.assertEqual(
            self.nemo.app.jinja_env.filters["FilterPluginOverride_formatting_passage_reference"],
            plug_noname.f_formatting_passage_reference,
            "Original Nemo filters should be override by newly registered filters"
        )