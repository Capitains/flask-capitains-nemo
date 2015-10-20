
.. image:: https://readthedocs.org/projects/flask-capitains-nemo/badge/?version=latest
    :alt: Documentation
    :target: http://flask-capitains-nemo.readthedocs.org

.. image:: https://travis-ci.org/Capitains/flask-capitains-nemo.svg
    :alt: Build status
    :target: https://travis-ci.org/Capitains/flask-capitains-nemo

.. image:: https://coveralls.io/repos/Capitains/flask-capitains-nemo/badge.svg?branch=master&service=github
    :alt: Coverage
  :target: https://coveralls.io/github/Capitains/flask-capitains-nemo?branch=master

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
    python3 setup.py install
