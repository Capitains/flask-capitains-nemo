Examples
========



Simple Configuration
####################

.. topic:: User story [1]

    A **researcher** , an **engineer** or both is interested in **CTS** but has **no time** to develop their own application and their own theme : *flask.ext.nemo* will provide a simple, easy to use interface that you can deploy on any server. Even with a really limited knowledge of python.

.. topic:: User story [2]

    A **researcher**, an **engineer** or both has already a CTS endpoint and wants to check the output and the browsing system visually.


The simplest configuration of Nemo, or close to it, is to simply give an endpoint url to your Nemo extension, the app you are using
and the name of a CTS inventory (if required). This will run a browsing interface with support for collections, textgroups, texts and passages browsing.

- The application will itself do the GetCapabilities request to retrieve the available texts and organize them through collection, textgroups and works.
- Once an edition or a translation is clicked, a page showing available references is shown.
- Once a passage is clicked, the passage is shown with available metadata.

.. _example1.code::

.. code-block:: python

    # We import Flask
    from flask import Flask
    # We import Nemo
    from flask.ext.nemo import Nemo
    # We create an application. You can simply use your own
    app = Flask(
        "My Application"
    )
    # We register a Nemo object with the minimal settings
    nemo = Nemo(
        # API URL is the URL of your endpoint.
        api_url="http://services2.perseids.org/exist/restxq/cts",
        # We set up the base url to be empty. If you want nemo to be on a
        # subpath called "cts", you would have
        # base_url="cts",
        base_url="",
        # In our case, we have an inventory named "nemo"
        inventory="nemo",
        # We give thee ap object
        app=app
    )
    # We register its routes
    nemo.register_routes()
    # We register its filters
    nemo.register_filters()
    # We run the application
    app.run()

.. note:: You can run this example using `python example.py default`

XSLT, CSS and Javascript addons
###############################

.. topic:: User Story

    A developer, with no or only limited understanding of python, wants to expose their CTS works but have some modifications to do regarding the design.


Because Python is not a natural language and because not everybody knows it in academia, you might find yourself in a situation where you don't know it. On the other hand, XML TEI, HTML, CSS - and thus xsl and sometimes Javascript - are quite common languages known to both researchers and engineers. Capitains Nemo for Flask accepts custom templates, CSS, Javascript, XSL and statics. And in a simple, nice way :

.. code-block:: python

    # ...
    nemo = Nemo(
        # Required API informations
        api_url="http://services2.perseids.org/exist/restxq/cts",
        base_url="",
        inventory="ciham",
        # For transform parameters, we provide a path to an xsl which will be used for every
        transform={"default" : "examples/ciham.xslt"},
        # For urntransform parameters, we provide a function which will be used to transform the urn for display
        # this example just adds explanatory text
        urntransform={"default" : lambda urn: "Stable URI:" + str(urn)},
        # CSS value should be a list of path to CSS own files
        css=[
            "examples/ciham.css"
        ],
        # JS follows the same scheme
        js=[
            # use own js file to load a script to go from normalized edition to diplomatic one.
            "examples/ciham.js"
        ],
        templates={
            "main": "examples/ciham"
        },
        additional_static=[
            "path/to/picture.png"
        ]
    )

.. topic:: Additional CSS, JS or Statics in Templates

    To call or make a link to a static in your own template, you should always use the helper `url_for` and the route name `secondary_assets`. Additional statics can be linked to using the filename (be sure they do not collide !) and the type : css, js or static. Example : `{{url_for('nemo.secondary_assets', type='static', asset='picture.png')}}`.

.. note:: Templates are written with `Jinja2 <http://jinja.pocoo.org/docs/dev/>`_. See also :ref:`Templates.documentation`. For XSL, we have some unfortunate restrictions, see :ref:`lxml.strip-spaces`

.. note:: You can run an example using css, js, templates and transform with `python example.py ciham`

Own Chunker
###########

.. warning:: Starting from this example, the configuration and changes implied require the capacity to develop in Python.

.. topic:: User Story

    A developer wants to add a custom scheme for browsing text passages by groups that are not part of the citation scheme of the text.  The custom scheme should be triggered by text identifier or using available CTS metadata about the text, such as the Citation Scheme.

  CTS is good, but getValidReff can really be a hassle. The default generation of browsing level will always retrieve the deepest level of citations available. For the Iliad of Homer, which is composed of two levels, books and lines, this would translate to a GetValidReff level 2. This would mean that the generic chunker would return on the text page a link to each line of each book (it's a total of 15337 lines, if you did not know).

  Chunker provides a simple, easy to develop interface to deal with such a situation : for example, returning only 50 lines groups of links (1.1-1.50, 1.51-1.100, etc.). The Nemo class accepts a chunker dictionary where **keys** are **urns** and where the key "**default**" is the default chunker to be applied. Given a chunker named *homer_chunker* and one named *default_chunker*,  if the urn of Homer is **urn:cts:greekLit:tlg0012.tlg001.opp-grc1** (See :ref:`Nemo.chunker.skeleton` for function skeleton):

.. code-block:: python

    # ...
    nemo = Nemo(
        # ...
        chunker= {
            "urn:cts:greekLit:tlg0012.tlg001.opp-grc1" : homer_chunker,
            "default": default_chunker
        }
       )

.. note:: You can run an example using chunker with `python example.py chunker`

.. note:: Parameters XSLT and prevnext work the same way. See relevant documentation : :ref:`Nemo.chunker` for more information about and examples of chunkers

Adding routes
#############

.. topic:: User story

    The user has needs in terms of new routes that would cover specific needs, like vis-a-vis edition.

There is multiple way to deal with this kind of situation. The best way is to create a subclass of Nemo. The idea behind that is that you rely on specific functionalities of Nemo and its context object. To deal with that and make as much as possible a good use of Nemo extension, you just need to add a new route to url using a tuple : first value would be the route, according to Flask standards, *ie* `/read/<collection>/<textgroup>/<work>/<version>/<passage_identifier>/<visavis>` , the name of the function or method (naming convention makes them start by r\_), *ie* `r_double`, and a list of methods, by default ["GET"].

As you will most likely use a new template, don't forget to register it with the templates parameter !

.. code-block:: python

    # #We create a class based on Nemo
    class NemoDouble(Nemo):
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
            args.update({ "visavis_{0}".format(key):value for key, value in self.r_passage(collection, textgroup, work, visavis, passage_identifier).items()})
            args["template"] = "double::r_double.html"
            return args

    nemo = NemoDouble(
        api_url="http://services2.perseids.org/exist/restxq/cts",
        base_url="",
        inventory="nemo",
        # We reuse Nemo.Routes and add a new one
        urls= Nemo.ROUTES + [("/read/<collection>/<textgroup>/<work>/<version>/<passage_identifier>/<visavis>", "r_double", ["GET"])],
        css=[
            "examples/translations.css"
        ],
        # We think about registering the new route
        templates={
            "double": "./examples/translations"
        }
    )

.. note:: You can run an example using chunker with `python example.py translations`