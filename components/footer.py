# include <stdlib.ARKlight>


def app_footer(text: str):
    return Footer(
        Text(text),
        class_name="footer",
    )


def toast_container():
    return Container(id="toast", class_name="toast")
