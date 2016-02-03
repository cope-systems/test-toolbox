import ez_setup
ez_setup.use_setuptools()

from setuptools import setup
from testtoolbox import __version__, __author__


setup(
    name="TestToolbox",
    version=__version__,
    author=__author__,
    author_email="rpcope1@gmail.com",
    description="Tools and extensions for testing and the unittest library.",
    license="BSD",
    keywords="test testing unittest bdd",
    url="https://bitbucket.org/rpcope1/testtoolbox",
    scripts=['ez_setup.py'],
    packages=['testtoolbox'],
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Topic :: Utilities",
        "Topic :: Software Development :: Testing",
        "License :: OSI Approved :: BSD License",
    ],
)
