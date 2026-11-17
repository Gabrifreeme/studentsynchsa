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


def configure_webview2(use_gpu):
    """Keep WebView2's compositor on the CPU unless the caller asks for the GPU.

    The display driver on this machine resets several times a day (the system
    log has hundreds of "nvlddmkm stopped responding" events), and the PC
    hard-reset while a second WebView2 window - the devtools panel - was
    opening. Software rendering keeps compositing in the CPU, where a failing
    driver cannot take the whole machine down. The UI is plain HTML, so the
    visual difference is nil.

    Flags already in the environment (a remote debugging port, for instance)
    are preserved rather than overwritten.
    """
    flags = (os.environ.get("WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS") or "").split()
    flags = [f for f in flags if f]
    if use_gpu:
        flags = [f for f in flags if f != "--disable-gpu"]
    elif "--disable-gpu" not in flags:
        flags.append("--disable-gpu")
    if flags:
        os.environ["WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS"] = " ".join(flags)


def main():
    parser = argparse.ArgumentParser(description="ACEsi desktop window")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument(
        "--devtools",
        action="store_true",
        help=(
            "enable devtools (F12, Ctrl+Shift+I, right-click Inspect). Off by "
            "default: opening the devtools window has crashed this machine."
        ),
    )
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
    # shortcuts (F12, Ctrl+Shift+I, Ctrl+R) to debug mode, so they are only on
    # for `--devtools`. The normal launch stays on the safe side: opt in
    # deliberately when you actually want to inspect something.
    # OPEN_DEVTOOLS_IN_DEBUG stays off so enabling the keys never pops the
    # panel open by itself - that window is the thing that crashed the PC.
    webview.settings["OPEN_DEVTOOLS_IN_DEBUG"] = False

    webview.start(
        debug=bool(args.devtools),
        private_mode=False,
        storage_path=storage_dir(),
    )


if __name__ == "__main__":
    main()
