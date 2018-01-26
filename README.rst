
.. image:: https://readthedocs.org/projects/flask-capitains-nemo/badge/?version=latest
    :alt: Documentation
    :target: http://flask-capitains-nemo.readthedocs.org

.. image:: https://travis-ci.org/Capitains/flask-capitains-nemo.svg
    :alt: Build status
    :target: https://travis-ci.org/Capitains/flask-capitains-nemo

.. image:: https://coveralls.io/repos/Capitains/flask-capitains-nemo/badge.svg?branch=master&service=github
    :alt: Coverage
    :target: https://coveralls.io/github/Capitains/flask-capitains-nemo?branch=master

.. image:: https://badge.fury.io/py/flask_nemo.svg
    :target: https://badge.fury.io/py/flask_nemo


.. image:: https://img.shields.io/badge/License-MPL%202.0-brightgreen.svg
    :alt: License: MPL 2.0
    :target: https://opensource.org/licenses/MPL-2.0


.. image:: https://raw.githubusercontent.com/Capitains/tutorial-nemo/master/header.png
    :alt: Nemo Banner
    :target: http://capitains.org

Capitains Nemo is an User Interface built around the need to make CapiTainS an easy-to-use, human-readable standard for texts.
Capitains Nemo counts multiple language implementations, including this one in Python for Flask. Built as a classic Flask
Extension, `flask.ext.nemo` intends to be a simple, customizable interface between your end-user and your Text APIs.

If you are new to the Capitains world, feel free to get some reading time on the `generic website <http://capitains.org>`_

The Flask's extension Nemo can be customized from its stylesheets to its functions. Adding routes or removing them is
as easy as adding a XSL Stylesheet to transform the very own result of a CTS GetPassage results to your own expected output.

Tutorial and example
####################

You can find a tutorial on `Github Capitains/tutorial-nemo <https://github.com/capitains/tutorial-nemo>`_ repository and
an example server (based on this tutorial) on `Heroku <https://tutorial-nemo.herokuapp.com/>`_

Install
#######

You can now install it with pip : :code:`pip install flask_nemo`

If you want to install the latest version, please do the following

.. code-block:: shell

    git clone https://github.com/Capitains/flask-capitains-nemo.git
    cd flask-capitains-nemo
    virtualenv -p /path/to/python3 venv
    source venv/bin/activate
    python setup.py install
    
If you have trouble with dependency conflicts with MyCapitains, try running :code:`pip install MyCapytain` this before install


Running Nemo from the command line
##################################

This small tutorial takes that you have a CTS API endpoint available, here :code:`http://localhost:8000`


1. (Advised) Create a virtual environment and source it : :code:`virtualenv -p /usr/bin/python3 env`, :code:`source env/bin/activate`
2. **With development version**:
    - Clone the repository : :code:`git clone https://github.com/Capitains/flask-capitains-nemo.git`
    - Go to the directory : :code:`cd Nemo`
    - Install the source with develop option : :code:`python setup.py develop`

2. **With production version**:
    - Install from pip : :code:`pip install flask_nemo`

3. You will be able now to call capitains nemo help information through :code:`capitains-nemo --help`
4. Basic setting for testing is :code:`capitains-nemo cts-api https://cts.perseids.org/api/cts`.
