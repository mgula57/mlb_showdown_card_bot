import pathlib
from setuptools import setup, find_packages

# THE DIRECTORY CONTAINING THIS FILE
HERE = pathlib.Path(__file__).parent

# LOAD README AS OBJECT
README = (HERE / "README.md").read_text()

# SETUP
setup(
    name="mlb-showdown-bot",
    version="2.6.4",
    description="Create custom MLB Showdown cards",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/mgula57/mlb_showdown_card_bot",
    author="Matthew Gula",
    author_email="mlbshowdownbot@gmail.com",
    license="Unlicense",
    classifiers=[
        "License :: OSI Approved :: The Unlicense (Unlicense)",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    python_requires='>=3.7',
    packages=['mlb_showdown_bot'],
    include_package_data=True,
    install_requires=[
        'apiclient>=1.0.4',
        'beautifulsoup4>=4.9.3',
        'bs4>=0.0.1',
        'google>=3.0.0',
        'google-api-python-client>=2.7.0',
        'lxml>=4.6.1',
        'numpy>=1.19.4',
        'oauth2client>=4.1.3',
        'pandas>=1.1.4',
        'Pillow>=7.2.0',
        'requests>=2.25.0',
        'Unidecode==1.2.0',
        'urllib3>=1.26.2',
        'xlrd>=1.2.0',
    ],
    entry_points={
        "console_scripts": [
            "showdownbot=mlb_showdown_bot.__main__:main",
        ]
    },
)