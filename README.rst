
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

Capitains Nemo is an User Interface built around the need to make CTS a easy to use, human readable standard for texts. 
Capitains Nemo counts multiple language implementation, including this one in Python for Flask. Presentend as a classic Flask
Extension, `flask.ext.nemo` intends to be a simple, customizable interface between your enduser and your CTS5 API.

The Flask's extension Nemo can be customized from its stylesheets to its functionalities. Adding routes or removing them is
as easy as adding a XSL Stylesheet to transform the very own result of a CTS GetPassage results to your own expected output.

Install
#######

You can now install it with pip : `pip install flask_nemo`

If you want to install the latest version, please do the following

.. code-block:: shell

    git clone https://github.com/Capitains/flask-capitains-nemo.git
    cd flask-capitains-nemo
    virtualenv -p /path/to/python3 venv
    source venv/bin/activate
    python setup.py install
    
If you have trouble with dependency conflicts with MyCapitains, try running :code:`pip install MyCapytain` this before install


Running Nemo from the command line
######################################

This small tutorial takes that you have a CTS API endpoint available, here :code:`http://localhost:8000`


1. (Advised) Create a virtual environment and source it : :code:`virtualenv -p /usr/bin/python3 env`, :code:`source env/bin/activate`
2. **With development version:**
    - Clone the repository : :code:`git clone https://github.com/Capitains/flask-capitains-nemo.git`
    - Go to the directory : :code:`cd Nemo`
    - Install the source with develop option : :code:`python setup.py develop`
2. **With production version:**
    - Install from pip : :code:`pip install flask_nemo`
3. You will be able now to call capitains nemo help information through :code:`capitains-nemo --help`
4. Basic setting for testing an api is :code:`capitains-nemo http://localhost:8000`.
