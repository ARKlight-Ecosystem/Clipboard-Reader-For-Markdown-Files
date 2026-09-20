"""
ARKlight project configuration -- optional.

ARKlight works fine without this file; every section below is
commented out and only takes effect once you uncomment it. See the
"Configuration" section of the ARKlight README (or `arklight/config.py`
in the ARKlight source) for the full, current list of sections.
"""

CONFIG = {
    # Read by `arklight android scaffold` -- see
    # docs/Foundational/DESIGN-NOTES.md ("v0.0438: Android backend",
    # "App identity metadata" subsection) in the ARKlight repo for the
    # full key list and defaults.
    "android": {
        "app_name": "Clip Reader",
        "package_id": "com.arklight.clipreader",
        "version_name": "1.0.0",
        "version_code": 1,
        "orientation": "sensor",
        "edge_to_edge": True,
        # No hosts here -- the app never navigates off-device, so
        # `arklight android scaffold` leaves the INTERNET permission
        # out entirely. Clipboard + TTS are both on-device APIs.
        "allow_navigation": [],
    },
}
