"""Configuration file for the Sphinx documentation builder."""


import os
import sys

sys.path.insert(0, os.path.abspath("../.."))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
project = "PyProBE"
copyright = (
    "2024, Thomas Holland, Electrochemical Science and Engineering Group, "
    "Imperial College London"
)

author = "Thomas Holland"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_tabs.tabs",
    "sphinxcontrib.bibtex",
    "sphinx_design",
]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
html_theme = "pydata_sphinx_theme"
html_theme_options = {"collapse_navigation": True, "show_nav_level": 4}

# -- sphinxcontrib-bibtex configuration --------------------------------------
bibtex_bibfiles = ["../../CITATIONS.bib"]
bibtex_style = "unsrt"
bibtex_footbibliography_header = """.. rubric:: References"""
bibtex_reference_style = "author_year"
bibtex_tooltips = True