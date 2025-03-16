"""Sphinx configuration file for the Secure Video Summarizer documentation."""

import os
import sys
import datetime

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath('../..'))

# Import the project's version
from version import __version__

# Project information
project = 'Secure Video Summarizer'
copyright = f'{datetime.datetime.now().year}, SecureVideoSummarizer Team'
author = 'SecureVideoSummarizer Team'
version = __version__
release = __version__

# General configuration
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
]

templates_path = ['_templates']
exclude_patterns = []
source_suffix = '.rst'
master_doc = 'index'
language = 'en'
pygments_style = 'sphinx'

# HTML output configuration
html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    'navigation_depth': 4,
    'collapse_navigation': False,
    'sticky_navigation': True,
    'includehidden': True,
    'titles_only': False,
}
html_static_path = ['_static']
html_logo = '../../Assets/SVS.jpg'
html_favicon = '../../Assets/SVS.jpg'
htmlhelp_basename = 'SecureVideoSummarizerdoc'

# Grouping the document tree
latex_elements = {}
latex_documents = [
    (master_doc, 'SecureVideoSummarizer.tex', 'Secure Video Summarizer Documentation',
     'SecureVideoSummarizer Team', 'manual'),
]

# Manual page output
man_pages = [
    (master_doc, 'securevideoummarizer', 'Secure Video Summarizer Documentation',
     [author], 1)
]

# Texinfo output
texinfo_documents = [
    (master_doc, 'SecureVideoSummarizer', 'Secure Video Summarizer Documentation',
     author, 'SecureVideoSummarizer', 'Privacy-focused video summarization tool.',
     'Miscellaneous'),
]

# Extension configuration
todo_include_todos = True

# Intersphinx configuration
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'flask': ('https://flask.palletsprojects.com/en/2.0.x/', None),
} 