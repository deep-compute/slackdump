import os

from setuptools import setup, find_packages

version = '0.1.0'

setup(
    name = "slack_dump",
    version = version,
    description = "A tool to get slack dump and store in mongodb",
    keywords = "slack_dump",
    install_requires = [
        'slacker',
        'pymongo',
        'slackclient',
        'basescript',
    ],

    package_dir = {'slack_dump' : 'slack_dump'},
    packages = find_packages('.'),
    include_package_data = True,
    classifiers = [
        "Programming Language :: Python :: 2.7",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
    ],

    entry_points = {
        "console_scripts": [
            "slack_dump = slack_dump:main",
        ]
    }
)
