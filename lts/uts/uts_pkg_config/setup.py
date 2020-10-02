import os
from setuptools import setup, find_packages

from uts import __version__

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

requirements = ['numpy>=1.10.4']

setup(
    name = "uts",
    version = ".".join(map(str, __version__)),
    description = "python package for unsupervised text segmentation",
    long_description = read('README.md'),
    url = 'https://github.com/intfloat/uts',
    license = 'MIT',
    author = 'Liang Wang',
    author_email = 'wangliangpeking@gmail.com',
    packages = find_packages(exclude=['tests']),
    include_package_data = True,
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    install_requires = requirements,
    tests_require = [],
)
