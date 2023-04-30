import sys
import pathlib


sys.path.insert(0, (pathlib.Path(__file__).parents[2]/'src').resolve().as_posix())  # Needed for 'sphinx.ext.autodoc'


# Project
project = 'Failures'
project_copyright = '2023, MARSO Adnan'
author = 'MARSO Adnan'
release = '0.2'

# General
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "myst_parser"
]
templates_path = ['_templates']
master_doc = 'index'
exclude_patterns = []

# Autodoc
# autodoc_mock_imports = ["typing_extensions"]

# MyST Parser
myst_enable_extensions = ["attrs_block"]

# Theme
html_theme = 'furo'
html_favicon = "../_static/icon.ico"
html_logo = "../_static/logo.png"
html_title = f"{project} {release} docs"
html_short_title = f"{project} docs"
html_static_path = ['../_static']
html_theme_options = {
    "sidebar_hide_name": True,
    "navigation_with_keys": True,
    "source_repository": "https://github.com/mediadnan/failures/",
    "source_branch": "main",
    "source_directory": "docs/source/",
    # "announcement": "announcements here ...",
    "footer_icons": [{
        "name": "GitHub",
        "url": "https://github.com/mediadnan/failures",
        "html": "<svg stroke=\"currentColor\" fill=\"currentColor\" stroke-width=\"0\" viewBox=`\"0 0 16 16`\"><path fill-rule=\"evenodd\" d=\"M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z\"></path>/svg>",
        "class": ""
    }, {
        "name": "PyPI",
        "url": "https://pypi.org/project/failures/",
        "html": "<svg fill=\"currentColor\" width=\"400px\" height=\"400px\" viewBox=\"0 0 32 32\"><path fill-rule=\"evenodd\" d=\"M31.896 18.104v5.219l-4.495 1.636-0.104 0.072 0.067 0.052 4.6-1.676 0.036-0.047v-5.329l-0.073-0.047zM31.495 7.489l-4.052 1.48v5.213l4.453-1.62v-5.219zM31.896 17.943v-5.219l-4.448 1.62v5.219zM27.292 19.615v-5.213l-4.396 1.599v5.219zM22.713 26.661v-5.213l-4.416 1.604v5.219zM22.896 21.412v5.156l4.416-1.609v-5.156l-4.416 1.604zM25.683 23.917c-0.489 0.181-0.88-0.1-0.88-0.615 0-0.521 0.391-1.089 0.88-1.267 0.489-0.176 0.885 0.104 0.885 0.62 0 0.521-0.396 1.089-0.885 1.261zM17.636 12.421l0.484-0.176-4.38-1.6-4.433 1.615 0.141 0.052 4.245 1.548zM27.344 14.219v-5.219l-4.448 1.62v5.219zM22.745 15.891v-5.219l-4.401 1.604v5.213zM18.193 12.328l-4.448 1.62v5.219l4.448-1.62zM9.208 17.552l4.432 1.615v-5.219l-4.432-1.609zM13.787 10.495l4.375 1.593v-5.156l-4.375-1.593zM27.344 3.62l-4.423 1.609v5.219l4.423-1.609zM22.599 5.203l-4.301-1.563-4.36 1.589 4.303 1.563zM20.484 6.14l-2.161 0.792v5.156l4.423-1.609v-5.156zM19.964 9.844c-0.491 0.183-0.881-0.099-0.881-0.615 0-0.521 0.391-1.089 0.881-1.265 0.489-0.177 0.885 0.099 0.885 0.62 0 0.52-0.396 1.083-0.885 1.26zM13.64 24.547v-5.219l-4.432-1.615v5.219zM18.24 22.912v-5.219l-4.495 1.635v5.219zM18.344 22.869l4.396-1.599v-5.219l-4.396 1.599zM18.24 28.292l-4.495 1.635v-5.219h-0.105v5.219l-4.432-1.615v-5.219l-0.068-0.072-0.036-0.084-4.448-1.615v-5.26l0.047 0.016 4.38 1.593 0.021-0.104-4.349-1.584 4.349-1.577v-0.147l-4.344-1.583 4.344-1.584v1.167l0.104-0.072v-3.161l4.344 1.577 0.079-0.077-4.183-1.527-0.141-0.047 4.324-1.573v-0.115l-4.491 1.636v0.025l-0.036 0.027v2.025l-4.516 1.647v0.025l-0.036 0.027v5.344l-4.521 1.64v0.027l-0.031 0.025v5.323l0.031 0.052 4.537 1.652 0.011-0.011 0.009 0.016 4.532 1.651 0.011-0.011 0.009 0.016 4.532 1.645 0.021-0.011 0.015 0.011 4.599-1.672 0.037-0.052zM4.656 12.749l4.344 1.579-4.344 1.584zM4.531 26.615l-4.427-1.609v-5.219l4.427 1.609zM4.552 21.292l-4.349-1.579 4.349-1.583v3.167zM9.083 28.265l-4.427-1.609v-5.219l4.427 1.615zM31.719 7.245l-4.276-1.557v3.115zM27.183 3.527l-4.319-1.573-4.359 1.583 4.328 1.579z\"></path></svg>",
        "class": ""
    }],
    "light_css_variables": {
        "color-brand-primary": "#c33653",
        "color-brand-content": "#aa3a50",
    },
    "dark_css_variables": {
        "color-brand-primary": "#c33653",
        "color-brand-content": "#aa3a50",
    },
}

# AutoDoc configuration
autodoc_member_order = 'bysource'
autoclass_content = "both"

# ViewCode configuration

