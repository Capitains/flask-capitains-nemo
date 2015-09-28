Chunkers
========

In the Nemo class, you'll find static methods called chunker, which can be used in the context of
Nemo().chunker dictionary. Chunker are used to take care of grouping references when a user arrives on
the version page of a text, to select where they should go.

Nemo contains multiple chunker and accept any contributions which are providing helpful, transproject functions.

Process description
###################
.. image:: _static/images/nemo.chunker.diagram.png
    :alt: Nemo Chunker Workflow

.. topic:: User story

    A user browse available texts and select a text. He does not want a specific passages. Nemo proposes a list of passages based
    on the structure of the text.

    *Example*: The Epigrams of Martial are a group of many book, containing each hundredth of poems, which are themselves composed
    by up to 50 lines. The use would preferably be proposed the poem as the minimal citation scheme than each lines.

To propose passages to the user, Capitains Nemo uses a chunker function which will group, if needed, references together. The function is called upon returning
the list of references to the view. The function should always return a list of references, and not full urn, with a human readable version of it,
which can be the same.

Defining a chunker in your Nemo implementation instance
#######################################################

The Nemo class accepts a chunker named argument that should be a dictionary where values are chunker functions.
This dictionary should at least contain one key named "default". Any other key should represents a URN and will override
the default function if the requested version has the given urn.

>>> from flask.ext.nemo import Nemo
>>> nemo = Nemo(chunker={
>>>     "default": Nemo.default_chunker,
>>>     "urn:cts:latinLit:phi1294.phi002.perseus-lat2": Nemo.scheme_chunker,
>>>     # This will override the original function and provides a poem based reference for Martial Epigrammata in this version
>>>     "urn:cts:latinLit:phi1017.phi004.opp-lat4": lambda version, callback: Nemo.line_chunker(version, callback, lines=50)
>>>     # Use a lambda to override default line numbers returned by Nemo.line_chunker for Seneca's Medea
>>> })

:ref: Nemo.api

Methods
#######

Building your own : Structure, Parameters, Return Values
********************************************************

A chunker should take always at least two positional arguments :

- The first one will be the version, based on a MyCapytains.resources.inventory.Text class. It contains informations about
    the citation scheme for example.
- The second one is a callback function that the chunker can use to retrieve the valid references. This callback itself takes a parameters
    named level. This callback corresponds to a MyCapytains.resources.texts.api.getValidReff() method. It returns a list of string based urns.

The chunker itself should return a list of tuples where the first element is a passage reference such as "1.pr" or "1-50" and a second value
which is a readable version of this citation node.

.. note:: As see in the diagram, there is no limitation for the chunker as soon as it returns a valid list of reference
    and their human readable version. It could in theory ask a third party services to return pages based urns to browse
    a text following its OCR source / manuscript


>>> # Example of chunker for the Satura of Juvenal
>>> def satura_chunker(version, getValidReff):
>>>     reffs = [urn.split(":")[-1] for urn in getValidReff(level=2)]
>>>     # Satura scheme contains three level (book, poem, lines) but only the Satura number is sequential
>>>     # So as human readable, we give only the second member of the reference body
>>>     return [(reff, "Satura {0}".format(reff.split(".")[-1])) for reff in reffs]

Available chunkers
***************

.. automethod:: flask.ext.nemo.Nemo.default_chunker
.. automethod:: flask.ext.nemo.Nemo.line_chunker
.. automethod:: flask.ext.nemo.Nemo.scheme_chunker