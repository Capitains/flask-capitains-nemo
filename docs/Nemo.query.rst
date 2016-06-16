QueryInterface Design and Components Hierarchy
==============================================

Workflow of the components
##########################

.. _QueryInterfaceWorkflow:

This workflow illustrates how QueryInterface components works together

.. image:: _static/images/nemo.queryinterface.workflow.png
    :alt: Query Interface Workflow


Description of the components
#############################

.. image:: _static/images/nemo.queryinterface.classes.png
    :alt: Query Interface Components hierarchy


QueryInterface 
**************

is an object that given a URN retrieves annotations for it.

- Query interface should be fed with a function to retrieve valid references of the text
- It should have a .getAnnotation method which returns tuple where first element is a list of annotations and the second is the number of found resources
    - :code:`*urn`  which takes a URN Object (MyCapytain)
    - :code:`wildcard` as a boolean
        - :code:`.` means exact match
        - :code:`.%` means lower match matches
        - :code:`%.` means higher match matches
        - :code:`-` in range of
        - :code:`%.%` means not level dependant
    - :code:`include, exclude` which would restrict the type of resources that can be retrieved using list of types
    - :code:`limit` as a limit of number, default to None
    - :code:`start` as the first parameter
    - :code:`expand` should automatically expand annotations matching

Annotations
***********

- Takes a resolver
- Has a read() method
- Has an .expandable properties which means the annotation might have embedded annotations
- Has an expand() methods which returns embedded annotations as a list

Resolver
********

- Decides on which retriever to use in a list of retrievers.
- Takes `retrievers=[]` as init argument
- Has a function resolve that takes an identifier argument
- Return a Retriever object

Retriever
*********

Retriever retrieves a resource given an identifier which can be cts, cite, local path, url, you name it.

- Has a `.match()` static method that returns True or False if the identifier can be retrieved by it
- Has a `.read()` method that returns the body of the resource 