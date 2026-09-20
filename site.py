# include <stdlib.ARKlight>

from components.runtime import ClipReaderRuntime
from content.styles import register as register_styles
from pages.home import home

site = Site(
    name="clip-reader",
    max_width="46rem",
    font_family='"Literata", "Georgia", serif',
    lang="en",
)

register_styles(site)


# Real @site.page(...) decorators live here, not in pages/*.py --
# static discovery (arklight.parser.discover) only looks at the entry
# file's own source, so this is the one place routes must be declared.
# The function below just delegates to the actual page-content
# function in pages/, which is free to import components/ and
# content/ however it likes.


@site.page("/")
def home_page():
    return home()


site.register_script_extension(ClipReaderRuntime())
