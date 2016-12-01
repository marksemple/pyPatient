# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='dicomModule',
    version='0.0.1',
    description='Module with Parts for building DICOM software with Python',
    long_description=readme,
    author='Mark Semple',
    author_email='mark.joseph.semple@gmail.com.com',
    url='https://marksemple@bitbucket.org/srimedicalphysics/dicommodule.git',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)
