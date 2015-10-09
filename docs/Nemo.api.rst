Nemo API
=================================

.. _Nemo.api:

.. autoclass:: flask.ext.nemo.Nemo

Flask related function
######################

.. automethod:: flask.ext.nemo.Nemo.init_app
.. automethod:: flask.ext.nemo.Nemo.register_routes
.. automethod:: flask.ext.nemo.Nemo.register_filters
.. automethod:: flask.ext.nemo.Nemo.create_blueprint
.. automethod:: flask.ext.nemo.Nemo.__register_assets

Controller
##########

Specific methods
****************

.. automethod:: flask.ext.nemo.Nemo.get_inventory
.. automethod:: flask.ext.nemo.Nemo.get_collections
.. automethod:: flask.ext.nemo.Nemo.get_textgroups
.. automethod:: flask.ext.nemo.Nemo.get_works
.. automethod:: flask.ext.nemo.Nemo.get_texts
.. automethod:: flask.ext.nemo.Nemo.get_text
.. automethod:: flask.ext.nemo.Nemo.get_reffs
.. automethod:: flask.ext.nemo.Nemo.get_passage

Customization appliers
**********************

.. automethod:: flask.ext.nemo.Nemo.chunk
.. automethod:: flask.ext.nemo.Nemo.getprevnext
.. automethod:: flask.ext.nemo.Nemo.transform

Shared methods
**************

.. automethod:: flask.ext.nemo.Nemo.render
.. automethod:: flask.ext.nemo.Nemo.view_maker
.. automethod:: flask.ext.nemo.Nemo.route
.. automethod:: flask.ext.nemo.Nemo.route

Routes
######

.. _Nemo.api.r_index::
.. automethod:: flask.ext.nemo.Nemo.r_index

.. _Nemo.api.r_collection::
.. automethod:: flask.ext.nemo.Nemo.r_collection

.. _Nemo.api.r_texts::
.. automethod:: flask.ext.nemo.Nemo.r_texts

.. _Nemo.api.r_version::
.. automethod:: flask.ext.nemo.Nemo.r_version

.. _Nemo.api.r_passage::
.. automethod:: flask.ext.nemo.Nemo.r_passage

.. _Nemo.api.r_assets::
.. automethod:: flask.ext.nemo.Nemo.r_assets

Statics
#######

Filters
*******

Filters follow a naming convention : they should always start with "f_"

.. automethod:: flask.ext.nemo.Nemo.f_active_link
.. automethod:: flask.ext.nemo.Nemo.f_collection_i18n
.. automethod:: flask.ext.nemo.Nemo.f_formatting_passage_reference

Helpers
*******

.. automethod:: flask.ext.nemo.Nemo.map_urns
.. automethod:: flask.ext.nemo.Nemo.filter_urn
.. automethod:: flask.ext.nemo.Nemo.in_and_not_in
.. automethod:: flask.ext.nemo.Nemo.prevnext_callback_generator

Chunkers
********

.. automethod:: flask.ext.nemo.Nemo.default_chunker
.. automethod:: flask.ext.nemo.Nemo.line_chunker
.. automethod:: flask.ext.nemo.Nemo.scheme_chunker

PrevNexter
**********

.. automethod:: flask.ext.nemo.Nemo.default_prevnext

