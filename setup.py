# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='tamarack',
    version='0.1.0',
    description='A bot for automating common pull request tasks on GitHub.'
                'Tamarack is specifically designed for use with the SaltStack '
                'repositories.',
    author='Nicole Thomas',
    author_email='nicole@saltstack.com',
    url='https://github.com/rallytime/tamarack',
    license="http://www.apache.org/licenses/LICENSE-2.0",
    packages=['tamarack'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    install_requires=[
        'tornado',
    ],
)
