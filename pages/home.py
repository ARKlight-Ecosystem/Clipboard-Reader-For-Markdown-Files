# include <stdlib.ARKlight>

from components.footer import app_footer, toast_container
from components.reader import reader_card
from components.status_bar import status_bar
from components.toolbar import toolbar
from components.topbar import topbar
from content.site_content import (
    EMPTY_STATE_BODY,
    EMPTY_STATE_HEADING,
    EMPTY_STATE_ICON,
    FOOTER_TEXT,
    STATUS_READY,
    TAGLINE,
    TITLE,
)


def home():
    return Page(
        Container(
            topbar(TITLE, TAGLINE),
            Main(
                toolbar(),
                status_bar(STATUS_READY),
                reader_card(EMPTY_STATE_ICON, EMPTY_STATE_HEADING, EMPTY_STATE_BODY),
                class_name="content",
            ),
            app_footer(FOOTER_TEXT),
            toast_container(),
            class_name="app-shell",
        ),
        title=TITLE,
    )
