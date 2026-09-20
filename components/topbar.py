# include <stdlib.ARKlight>


def topbar(title: str, tagline: str):
    return Header(
        Container(
            Heading(title, level=1, class_name="brand"),
            Text(tagline, class_name="tagline"),
        ),
        class_name="topbar",
    )
