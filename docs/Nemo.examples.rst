Examples
========



Simple Configuration
####################

.. topic:: User story [1]

    A **researcher** , an **ingeneer** or both is interested in **CTS** but has **no time** to develop their own application and their own theme : *flask.ext.nemo* will provide a simple, easy to use interface that you can deploy on any server. Even with a really limited knowledge of python.

.. topic:: User story [2]

    A **researcher**, an **ingeneer** or both has already a CTS endpoint and wants to check the output and the browsing system visually.


The simplest configuration of Nemo, or close to it, is to simply give an endpoint url to your Nemo extension, the app you are using
and the inventory if required. This will run a browsing interface with support for collections, textgroups, texts and passages browsing.

- The application will itself do the GetCapabilities request to retrieve the available texts and organize them through collection, textgroups and works.
- Once an edition or a translation is clicked, a page showing available referense is shown.
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

Own Chunker
###########

.. warning:: Starting from this example, the configuration and changes implied require the capacity to develop in Python.

.. topic:: User Story

    A developer wants to propose an alternative level of browsing at the text passage browsing. It should be customizable by text identifier or using available CTS metadata about the text, such as the Citation Scheme

CTS is good, but getValidReff can really be a hassle. The default generation of browsing level will always retrieve the deepest
 citations available. For the Iliad of Homer, which is composed of two levels, books and lines, this would translate to a GetValidReff
 level 2. This would mean that the generic chunker would return on the text page a link to each line of each books (it's a total of 15337 lines, if you did not know).

Chunker provides a simple, easy to develop interface to deal with such situation : for example, returning only 50 lines packs of link (1.1-1.50, 1.51-1.100, etc.). The Nemo
 class accepts a dictionary of chunker where **keys** are **urns** and where "**default**" key is the default chunker to be applied. Given a chunker named *homer_chunker* and one named *default_chunker*,
 if the urn of Homer is **urn:cts:greekLit:tlg0012.tlg001.opp-grc1** (See :ref:`Nemo.chunker.skeleton` for function skeleton):

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

.. note:: Parameters XSLT and prevnext work the same way. See relevant documentation : :ref:`Nemo.chunker` for more informations and more examples about chunkers

Adding routes
#############

.. note::
    .. autoclass:: examples.configs.NemoDouble
        :members:

Replacing routes
################
