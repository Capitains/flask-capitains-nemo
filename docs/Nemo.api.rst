Nemo API
=================================

.. _Nemo.api:

.. autoclass:: flask_nemo.Nemo

Flask related function
######################

.. automethod:: flask_nemo.Nemo.init_app
.. automethod:: flask_nemo.Nemo.create_blueprint
.. automethod:: flask_nemo.Nemo.register_assets
.. automethod:: flask_nemo.Nemo.register_plugins
.. automethod:: flask_nemo.Nemo.register_filters

Controller
##########

Specific methods
****************

.. automethod:: flask_nemo.Nemo.get_inventory
.. automethod:: flask_nemo.Nemo.get_collections
.. automethod:: flask_nemo.Nemo.get_textgroups
.. automethod:: flask_nemo.Nemo.get_works
.. automethod:: flask_nemo.Nemo.get_texts
.. automethod:: flask_nemo.Nemo.get_text
.. automethod:: flask_nemo.Nemo.get_reffs
.. automethod:: flask_nemo.Nemo.get_passage

Customization appliers
**********************

.. automethod:: flask_nemo.Nemo.chunk
.. automethod:: flask_nemo.Nemo.getprevnext
.. automethod:: flask_nemo.Nemo.transform
.. automethod:: flask_nemo.Nemo.transform_urn

Shared methods
**************

.. automethod:: flask_nemo.Nemo.render
.. automethod:: flask_nemo.Nemo.view_maker
.. automethod:: flask_nemo.Nemo.route

Routes
######

.. _Nemo.api.r_index:
.. automethod:: flask_nemo.Nemo.r_index

.. _Nemo.api.r_collection:
.. automethod:: flask_nemo.Nemo.r_collection

.. _Nemo.api.r_texts:
.. automethod:: flask_nemo.Nemo.r_texts

.. _Nemo.api.r_version:
.. automethod:: flask_nemo.Nemo.r_version

.. _Nemo.api.r_passage:
.. automethod:: flask_nemo.Nemo.r_passage

.. _Nemo.api.r_assets:
.. automethod:: flask_nemo.Nemo.r_assets

Statics
#######

Filters
*******

Filters follow a naming convention : they should always start with :code:`f_`

.. automethod:: flask_nemo.filters.f_active_link
.. automethod:: flask_nemo.filters.f_collection_i18n
.. automethod:: flask_nemo.filters.f_formatting_passage_reference
.. automethod:: flask_nemo.filters.f_order_text_edition_translation
.. automethod:: flask_nemo.filters.f_i18n_citation_type
.. automethod:: flask_nemo.filters.f_is_str
.. automethod:: flask_nemo.filters.f_annotation_filter

Helpers
*******

.. automethod:: flask_nemo.Nemo.map_urns
.. automethod:: flask_nemo.Nemo.filter_urn
.. automethod:: flask_nemo.Nemo.in_and_not_in
.. automethod:: flask_nemo.Nemo.prevnext_callback_generator

Chunkers
********

.. automethod:: flask_nemo.chunker.default_chunker
.. automethod:: flask_nemo.chunker.line_chunker
.. automethod:: flask_nemo.chunker.scheme_chunker
.. automethod:: flask_nemo.chunker.level_grouper
.. automethod:: flask_nemo.chunker.level_chunker

PrevNexter
**********

.. automethod:: flask_nemo.Nemo.default_prevnext

Plugin
######

.. _pluginInit:
.. autoclass:: flask_nemo.plugin.PluginPrototype
.. automethod:: flask_nemo.plugin.PluginPrototype.render


Default Plugins
###############

.. autoclass:: flask_nemo.plugins.default.Breadcrumb

.. _pluginRender:
.. automethod:: flask_nemo.plugins.default.Breadcrumb.render

Common
######

.. autofunction:: flask_nemo.common.resource_qualifier


Query Interfaces and Annotations
################################

Annotations
***********

.. autoclass:: flask_nemo.query.annotation.AnnotationResource
.. automethod:: flask_nemo.query.annotation.AnnotationResource.read
.. automethod:: flask_nemo.query.annotation.AnnotationResource.expand

.. autoclass:: flask_nemo.query.annotation.Target
.. automethod:: flask_nemo.query.annotation.Target.to_json

Query Interfaces
****************

Prototype
---------

.. autoclass:: flask_nemo.query.proto.QueryPrototype
.. automethod:: flask_nemo.query.proto.QueryPrototype.getAnnotations
.. automethod:: flask_nemo.query.proto.QueryPrototype.getResource

Simple Query
------------

.. autoclass:: flask_nemo.query.interface.SimpleQuery
.. automethod:: flask_nemo.query.interface.SimpleQuery.process

Resolver and Retrievers
***********************

.. autoclass:: flask_nemo.query.resolve.UnresolvableURIError

.. autoclass:: flask_nemo.query.resolve.Resolver
.. automethod:: flask_nemo.query.resolve.Resolver.resolve

.. autoclass:: flask_nemo.query.resolve.RetrieverPrototype
.. automethod:: flask_nemo.query.resolve.RetrieverPrototype.match
.. automethod:: flask_nemo.query.resolve.RetrieverPrototype.read

.. autoclass:: flask_nemo.query.resolve.HTTPRetriever
.. automethod:: flask_nemo.query.resolve.HTTPRetriever.match
.. automethod:: flask_nemo.query.resolve.HTTPRetriever.read

.. autoclass:: flask_nemo.query.resolve.LocalRetriever
.. automethod:: flask_nemo.query.resolve.LocalRetriever.match
.. automethod:: flask_nemo.query.resolve.LocalRetriever.read

.. autoclass:: flask_nemo.query.resolve.CTSRetriever
.. automethod:: flask_nemo.query.resolve.CTSRetriever.match
.. automethod:: flask_nemo.query.resolve.CTSRetriever.read

Plugins
#######

AnnotationApi
*************

.. autoclass:: flask_nemo.plugins.annotations_api.AnnotationsApiPlugin
.. automethod:: flask_nemo.plugins.annotations_api.AnnotationsApiPlugin.r_annotations
.. automethod:: flask_nemo.plugins.annotations_api.AnnotationsApiPlugin.r_annotation
.. automethod:: flask_nemo.plugins.annotations_api.AnnotationsApiPlugin.r_annotation_body