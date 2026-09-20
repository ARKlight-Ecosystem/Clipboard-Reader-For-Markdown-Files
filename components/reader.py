# include <stdlib.ARKlight>


def reader_card(empty_icon: str, empty_heading: str, empty_body: str):
    return Container(
        Container(
            Text(empty_icon, class_name="empty-state-icon"),
            Heading(empty_heading, level=2),
            Text(empty_body),
            id="empty-state",
            class_name="empty-state",
        ),
        Article(id="md-preview", class_name="md-preview hidden"),
        class_name="reader-card",
        id="reader-card",
    )
