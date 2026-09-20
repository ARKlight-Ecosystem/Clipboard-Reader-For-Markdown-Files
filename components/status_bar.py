# include <stdlib.ARKlight>


def status_bar(ready_text: str):
    return Container(
        Text(ready_text, id="status-text"),
        Text("", id="meta-text"),
        class_name="status-bar",
    )
