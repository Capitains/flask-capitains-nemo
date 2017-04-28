Nemo Plugin System
==================

Since flask-capitains-nemo 1.0.0, plugins are a reality. They bring a much easy way to stack new functionalities in Nemo and provide large reusability and modularity to everyone.

Design
######

Nemo Plugins are quite close in design to the Nemo object but differ in a major way : they do not have any Flask `Blueprint <http://exploreflask.readthedocs.io/en/latest/blueprints.html>`_ instance and are not aware directly of the flask object. They only serve as a simple and efficient way to plugin in Nemo a set of resources, from routes to assets as well as filters.

The way Nemo deals with plugins is based on a stack design. Each plugin is inserted one after the other and they take effect this way. The last plugin routes for the main route `/` is always the one showed up, as it is for assets and templates namespaces.

What are plugins
################

What can plugin do
******************

- It can add assets (javascript, css or static files such as images)
- It can provide new templates to theme Nemo
- It can add new routes on top of the existing routes
- It can remove original routes, and bring new one
- It can bring new `filters <http://exploreflask.readthedocs.io/en/latest/templates.html#custom-filters>`_
- It can add new informations to what is passed to the template through their :ref:`pluginRender <pluginRender>` function


How plugin are registered
*************************

At the creation of the Blueprint in Nemo, Nemo runs a function which does the following in said order:

- Clear routes first if asked by one plugin
- Clear assets if asked by one plugin and replace by the last registered plugin ``STATIC_FOLDER``
- Register each plugin
    - Append plugin routes to registered routes
    - Append plugin filters to registered filters
    - Append templates directory to given namespaces
    - Append assets (CSS, JS, statics) to given resources 
    - Append render view (if exists) to Nemo.render stack

Inserting a plugin in a Nemo instance
*************************************

.. code-block:: python
    :linenos:
    :caption: You app.py
    :name: app.py

    # We import Flask and Nemo
    from flask import Flask
    from flask_nemo import Nemo
    # For this demo, we use the plugin prototype which does not include anything special
    from flask_nemo.plugin import PluginPrototype
    from MyCapytain.resolvers.cts.api import HttpCtsResolver
    from MyCapytain.retrievers.cts5 import HttpCtsRetriever

    # We set up a resolver which communicates with an API available in Leipzig
    resolver = HttpCtsResolver(HttpCtsRetriever("http://cts.dh.uni-leipzig.de/api/cts/"))

    # Initiate the app
    app = Flask(__name__)
    # We initiate the plugins
    proto_plug = PluginPrototype()
    # We insert the plugin into Nemo while setting up Nemo
    nemo = Nemo(
        resolver=resolver,
        plugins=[proto_plug],
        app=app
    )

Writing a plugin
################

The major properties of plugins are - and should be - class variables and copied during initiation to ensure a strong structure. There is list of core class constants which are defined below. It is recommanded to use PluginPrototype class as your parent object :


.. code-block: python
    :linenos:
    :caption: my_plugin.py
    :name: my_plugin.py

    from flask_nemo.plugin import PluginPrototype

    class MyPlugin(PluginPrototype):
        # Add new things and configure things with Plugin core constants

Assets providing
****************

There is three class variables (JS, STATICS and CSS) related to register new UI resources on to the Nemo instance. 

- Remote resources (http://, https://, //) will be simply sent to the templates css and js variables so that it can be called from here (such as ``<script src="//maxcdn.bootstrapcdn.com/bootstrap/3.3.6/css/bootstrap.min.css"></script>``)
- Local resources (such as ``/directory/assets/css/stuff.css``) will be made available through :ref:`Nemo secondary assets route <Nemo.api.r_assets>` and fed to the templates as local resources.

.. code-block: python
    :linenos:
    :caption: flask_nemo/plugin.py
    :name: flask_nemo/plugin.py

    class PluginPrototype(object):
        CSS = []
        STATICS = []
        JS = []

Adding routes, adding/overwriting templates and filters
*******************************************************

The ``ROUTES`` and ``TEMPLATES`` class variables work the same way as the Nemo one : they will be registered on to the Nemo instance on top of the existing routes. 

- Routes of plugins stack up and overwrite themselves if they are not namespaced (See ``namespacing`` argument in :ref:`pluginInit <pluginInit>`).
- Templates can provide new templates for the ``main::`` namespace as well as new templates for any other namespace (cf. :ref:`templateOrder <templateOrder>`)
- The clear route function will erase original provided routes of Nemo if set to True before registering other plugins (See :py:meth:`~flask_nemo.Nemo.register_plugins`)
- Filters works like Nemo filters. They can be namespaced using the ``namespacing`` argument.
- Routes can be cached by providing their name in ``CACHED``

.. code-block: python
    :linenos:
    :caption: flask_nemo/plugin.py
    :name: flask_nemo/plugin.py

    class PluginPrototype(object):
        ROUTES = []
        TEMPLATES = {}
        CLEAR_ROUTES = False
        FILTERS = []
        CACHED = []

Various other core parameters : render, clear assets and static folder
**********************************************************************

- Plugin.render() view brings a new stack of values to the variables that are sent to the template (cf. :ref:`renderWorkflow <renderWorkflow>`). ``HAS_AUGMENT_RENDER`` is the class variable that when set to True will make Nemo aware of the existence of the function.
- ``CLEAR_ASSETS`` clears registered defaults assets in Nemo assets dictionary.
- ``STATIC_FOLDER`` overwrites original Nemo static folder. It is recommended not to make too much use of it except if you do not need any of the original Nemo assets.

.. code-block: python
    :linenos:
    :caption: flask_nemo/plugin.py
    :name: flask_nemo/plugin.py

    class PluginPrototype(object):
        HAS_AUGMENT_RENDER = False
        CLEAR_ASSETS = False
        STATIC_FOLDER = None
