# include <stdlib.ARKlight>


def toolbar():
    return Section(
        Button("Paste", id="btn-paste", class_name="btn btn-primary"),
        Button("Clear", id="btn-clear", class_name="btn"),
        Button("Listen", id="btn-speak", class_name="btn btn-accent"),
        Button("Pause", id="btn-pause", class_name="btn"),
        Button("Stop", id="btn-stop", class_name="btn"),
        Container(class_name="toolbar-spacer"),
        Container(
            Label("Speed", for_="rate-range"),
            Input(
                type="range",
                id="rate-range",
                min="0.5",
                max="1.8",
                step="0.1",
                value="1",
                class_name="rate-slider",
            ),
            class_name="rate-control",
        ),
        class_name="toolbar",
        id="toolbar",
    )
