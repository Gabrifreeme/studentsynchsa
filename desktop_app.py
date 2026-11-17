"""Open the ACEsi desktop window (pywebview -> WebView2).

`launch.ps1` starts the Flask server and then runs this file. It lives in its
own module instead of inside `python -c "..."` for three reasons:

  * the launcher can find and close the previous window by command line,
  * quoting survives paths that contain spaces,
  * the URL gets a per-launch cache-buster. WebView2 keeps its own copy of the
    document, and a cached copy is exactly what makes the desktop app look a
    few edits behind the browser.
"""
import argparse
import os
import time

import webview

DEFAULT_PORT = 5000


def storage_dir():
    """Persistent WebView2 profile, kept with the app's other local data.

    The UI remembers the chosen model/provider and the explorer layout in
    localStorage. Private mode (the pywebview default) would forget those on
    every launch, which the browser version does not do.
    """
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    path = os.path.join(base, "ACESi", "webview")
    os.makedirs(path, exist_ok=True)
    return path


def main():
    parser = argparse.ArgumentParser(description="ACEsi desktop window")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument(
        "--debug",
        action="store_true",
        help="start with devtools enabled (F12 / right-click -> Inspect)",
    )
    args = parser.parse_args()

    url = "http://127.0.0.1:%d/?v=%d" % (args.port, int(time.time() * 1000))

    webview.create_window(
        "ACESi",
        url,
        width=1200,
        height=800,
        min_size=(900, 600),
        # The browser lets you select chat text; the pywebview default does not.
        text_select=True,
    )
    webview.start(
        debug=args.debug,
        private_mode=False,
        storage_path=storage_dir(),
    )


if __name__ == "__main__":
    main()
