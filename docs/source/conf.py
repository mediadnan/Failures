# -- Project information -----------------------------------------------------

project = 'Failures'
copyright = '2023, MARSO Adnan'
author = 'MARSO Adnan'
release = '0.2'

# -- General configuration ---------------------------------------------------

extensions = ["myst_parser"]
templates_path = ['_templates']
master_doc = 'index'
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------

html_theme = 'furo'
html_favicon = "../_static/icon.ico"
html_logo = "../_static/logo.png"
html_title = f"{project} {release}"
html_short_title = f"{project} docs"
html_static_path = ['_static']
html_theme_options = {
    "sidebar_hide_name": True,
    "navigation_with_keys": True,
    "source_repository": "https://github.com/mediadnan/failures/",
    "source_branch": "main",
    "source_directory": "docs/source/",
}
