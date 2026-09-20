# Read by `arklight android scaffold` (arklight.cli.android._DEFAULTS)
# -- this file lives next to site.py, one level above the build output,
# which is the layout `arklight android scaffold`'s docs describe.
CONFIG = {
    "android": {
        "app_name": "Clip Reader",
        "package_id": "com.arklight.clipreader",
        "version_name": "1.0.0",
        "version_code": 1,
        "orientation": "sensor",
        "edge_to_edge": True,
        # No hosts here -- the app never navigates off-device, so
        # `arklight android scaffold` leaves the INTERNET permission out
        # entirely. Clipboard + TTS are both on-device APIs.
        "allow_navigation": [],
    },
}
