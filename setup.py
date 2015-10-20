from setuptools import setup, find_packages

setup(
    name='flask_nemo',
    version="0.0.1",
    packages = find_packages(exclude=["examples"]),
    url='https://github.com/capitains/flask-capitains-nemo',
    license='GNU GPL',
    author='Thibault Clerice',
    author_email='leponteineptique@gmail.com',
    description='Flask Extension to Browse CTS Repository',
    test_suite="test_flask_nemo",
    install_requires=[
        "MyCapytain==0.0.6",
        "requests_cache==0.4.9",
        "Flask==0.10.1"
    ],
    tests_require=[
        "mock==1.0.1"
    ],
    include_package_data=True,
    zip_safe=False
)
