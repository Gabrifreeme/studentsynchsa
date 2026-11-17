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


CDP_PORT = 9222


def configure_webview2(use_gpu):
    """Set the WebView2 browser flags used for every normal launch.

    Two things matter here:

    * Software rendering (--disable-gpu). The display driver on this machine
      resets hundreds of times a day, and the PC hard-reset while a second
      WebView2 window - the devtools panel - was opening. Keeping the
      compositor on the CPU means a failing driver cannot take the machine
      down. The UI is plain HTML, so there is no visible difference.

    * A localhost CDP endpoint (--remote-debugging-port). This is what devtools
      is actually for here: it lets the ACEsi assistant inspect and debug the
      running window programmatically. A CDP connection does NOT open a
      devtools window, so it carries none of the crash risk the visible panel
      did. Chromium binds it to 127.0.0.1 only.

    Flags already in the environment are preserved; only the ones we manage
    are added or removed.
    """
    flags = (os.environ.get("WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS") or "").split()
    flags = [f for f in flags if f]

    def drop(flag):
        return [f for f in flags if f != flag and not f.startswith(flag + "=")]

    flags = drop("--disable-gpu")
    flags = drop("--remote-debugging-port")
    if not use_gpu:
        flags.append("--disable-gpu")
    flags.append("--remote-debugging-port=%d" % CDP_PORT)
    os.environ["WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS"] = " ".join(flags)


def main():
    parser = argparse.ArgumentParser(description="ACEsi desktop window")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument(
        "--gpu",
        action="store_true",
        help="use GPU rendering (software rendering is the default)",
    )
    args = parser.parse_args()

    configure_webview2(use_gpu=args.gpu)

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

    # pywebview ties devtools, the right-click menu and the browser keyboard
    # shortcuts (F12, Ctrl+Shift+I) to debug mode, so keep it on: the browser
    # version has them and that is what was asked for. What crashed the machine
    # was the devtools *window opening*, not the shortcuts, so keep that window
    # from opening by itself. For our own debugging we use the CDP endpoint
    # above, which needs no window at all.
    webview.settings["OPEN_DEVTOOLS_IN_DEBUG"] = False

    webview.start(
        debug=True,
        private_mode=False,
        storage_path=storage_dir(),
    )


if __name__ == "__main__":
    main()
