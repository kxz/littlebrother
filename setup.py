#!/usr/bin/env python
import sys

from setuptools import setup, find_packages
from setuptools.command.test import test


class Tox(test):
    def finalize_options(self):
        test.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import tox
        errno = tox.cmdline(self.test_args)
        sys.exit(errno)


setup(
    name='littlebrother',
    description='An HTTP document title extractor for Twisted Web',
    version='0.1.3',
    author='Kevin Xiwei Zheng',
    author_email='blankplacement+littlebrother@gmail.com',
    url='https://github.com/kxz/littlebrother',
    license='X11',
    packages=find_packages(),
    package_data={
        'littlebrother': ['test/data/*']},
    install_requires=[
        'Twisted>=14.0.0',
        'pyOpenSSL',
        'service_identity',
        'ipaddress'],
    extras_require={
        'av': ['av'],
        'html': ['beautifulsoup4'],
        'image': ['Pillow']},
    tests_require=['tox'],
    cmdclass={'test': Tox})
