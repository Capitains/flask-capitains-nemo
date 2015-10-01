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
            "menu": "examples/ciham.menu.html"
        },
        additional_static=[
            "path/to/picture.png"
        ]
    )

.. topic:: Additional CSS, JS or Statics in Templates

    To call or make a link to a static in your own template, you should always use the helper `url_for` and the route name `secondary_assets`. Additional statics can be linked to using the filename (be sure they do not collide !) and the type : css, js or static. Example : `{{url_for('nemo.secondary_assets', type='static', asset='picture.png')}}`.

.. note:: Templates are written with `Jinja2 <http://jinja.pocoo.org/docs/dev/>`_. See also `Templates documentation`_ . For XSL, we have some unfortunate restrictions, see :ref:`lxml.strip-spaces`

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

.. note::
    .. autoclass:: examples.configs.NemoDouble
        :members:

Replacing routes
################
