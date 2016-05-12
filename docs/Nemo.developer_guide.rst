Nemo Developper Guide
=====================

How to contribute ? Our github Etiquette
########################################

- Open Issues
- Do Pull Request
- Ensure Unit Tests
- Do not decide yourself on changing the version

Writing and running tests
#########################

- Add tests which are not taking care of the rendering (Testing the function itself)
- Add a "navigational test" in `tests/test_with_nautilus`

Ultimately, tests should be part of the right file and take a name starting with "test_" :

.. code-block:: python
    :linenos:

    from unittest import TestCase

    class TestUnit(TestCase):
        """ Description of the general group of test represented by TestUnit """

        def test_a_function(self):
            """ Simple definition of this test prupose """
            do = 1
            self.assertEqual(
                do, 1,
                "A human friendly message explaining what we check and we expect"
            )

Running tests
*************

In flask-capitains-nemo repository

.. code-block:: shell
    :linenos:

    virtualenv env -p /usr/bin/python3
    source env/bin/activate
    python setup.py tests

Writing and building documentations
###################################

- Add your new function to docs/Nemo.api.rst
- In you add a chunker, ensure to register it in Nemo.chunker.rst
- If the change has any impact on the general behaviour, make sure to check `Nemo.examples.rst` usecases

Coding guidelines
#################

- Routes start with `r_`
- Filters start with `f_`
- Private variables should not be modified after `__init__`
