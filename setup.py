from setuptools import setup
import flask_nemo

setup(
    name='flask_nemo',
    version=flask_nemo.__version__,
    py_modules=['flask_nemo'],
    url='',
    license='',
    author='thibault',
    author_email='',
    description='',
    test_suite="test_flask_nemo",
    install_requires=[
        "MyCapytain==0.0.5",
        "requests_cache==0.4.9",
        "Flask==0.10.1"
    ],
    tests_require=[
        "mock==1.0.1"
    ]
)
