from setuptools import setup, find_packages

version = '0.1.0'
setup(
    name="slackdump",
    version=version,
    description="A tool to get the data from slack and store it in mongodb",
    keywords="slackdump",
    install_requires=[
        'slacker == 0.9.60',
        'pymongo == 3.6.0',
        'slackclient == 1.1.0',
        'basescript',
    ],
    package_dir={'slackdump': 'slackdump'},
    packages=find_packages('.'),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 2.7",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
    ],
    entry_points={
        "console_scripts": [
            "slackdump = slackdump:main",
        ]
    }
)
