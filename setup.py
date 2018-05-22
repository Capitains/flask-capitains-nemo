from setuptools import setup, find_packages

version = "1.0.3"

setup(
    name='flask_nemo',
    version=version,
    packages=find_packages(exclude=["examples", "tests"]),
    url='https://github.com/capitains/flask-capitains-nemo',
    license='Mozilla Public License Version 2.0',
    author='Thibault Clerice',
    author_email='leponteineptique@gmail.com',
    description='Flask Extension to browse CTS Repository',
    test_suite="tests",
    install_requires=[
        "MyCapytain>=2.0.0",
        "requests_cache>=0.4.9",
        "Flask>=0.12",
        "requests>=2.10.0",
        "python-slugify==1.2.1",
        "Flask-Caching>=1.2.0"
    ],
    tests_require=[
        "mock>=2.0.0",
    ],
    entry_points={
        'console_scripts': ['capitains-nemo=flask_nemo.cmd:server'],
    },
    include_package_data=True,
    zip_safe=False
)
