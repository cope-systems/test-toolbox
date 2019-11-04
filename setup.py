#!/usr/bin/env python
import os
from setuptools import setup


def read_file(fname):
    try:
        return open(os.path.join(os.path.dirname(__file__), fname)).read()
    except IOError:
        return ''


REQUIREMENTS = [l for l in read_file('requirements.txt').split('\n') if l and not l.strip().startswith('#')]
DEV_REQUIREMENTS = [l for l in read_file('dev-requirements.txt').split('\n')
                    if l and not l.strip().startswith('#') and not l.strip().startswith("-r")] + REQUIREMENTS

setup(
    name="TestToolbox",
    version="0.1.1",
    url='https://github.com/cope-systems/test_toolbox',
    description='Tools and extensions for testing in Python.',
    long_description=None,
    author='Robert Cope',
    author_email='robert@copesystems.com',
    license='BSD',
    platforms='any',
    packages=["test_toolbox"],
    install_requires=REQUIREMENTS,
    tests_require=DEV_REQUIREMENTS,
    test_suite="test_this",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "Topic :: Software Development :: Testing",
        "License :: OSI Approved :: BSD License",
    ],
    include_package_data=True
)
