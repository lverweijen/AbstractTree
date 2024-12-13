# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

# Code is in src. Make sure sphinx can find it
import sys
from pathlib import Path
src_folder = Path(__file__).parent.parent.parent / "src"
print(src_folder)
sys.path.insert(0, str(src_folder.resolve(strict=True)))

from setuptools_scm import get_version

project = 'AbstractTree'
copyright = '2024, Laurent Verweijen'
author = 'Laurent Verweijen'
release = get_version('abstracttree')

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.githubpages',
    'sphinx.ext.viewcode',
    'myst_parser',
    'sphinxcontrib.mermaid'
]

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']


myst_enable_extensions = ["colon_fence"]

