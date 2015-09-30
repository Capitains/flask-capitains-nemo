Examples
========



Simple Configuration
####################

.. topic:: User story [1]

    A **researcher**, an **ingeneer** or both is interested in **CTS** but has **no time** to
        - develop their own application
        - develop their own theme
    *flask.ext.nemo* will provide a simple, easy to use interface that you can deploy on any server. Even with a really limited knowledge of python.

.. topic:: User story [2]

    A **researcher**, an **ingeneer** or both has already a CTS endpoint and wants to check the output and the browsing system visually.

.. note:: You can run this example using `python example.py default`

The simplest configuration of Nemo, or close to it, is to simply give an endpoint url to your Nemo extension, the app you are using
and the inventory if required. This will run a browsing interface with support for collections, textgroups, texts and passages browsing.

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
        # We set up the base url to be empty. If you want nemo to be on a subpath called "cts", you would have
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


Own Chunker
###########

XSLT, CSS and Javascript addons
###############################

Adding routes
#############

.. note::
    .. autoclass:: examples.configs.NemoDouble
        :members:

Replacing routes
################
