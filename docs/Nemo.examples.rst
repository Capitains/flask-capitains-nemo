Examples
========

Simple Configuration
####################

.. note:: You can run this example using `python example.py default`

The simplest configuration of Nemo, or close to it, is to simply give an endpoint url to your Nemo extension, the app you are using
and the inventory if required :

.. highlight:: python

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
        inventory="nemo"
    )


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
