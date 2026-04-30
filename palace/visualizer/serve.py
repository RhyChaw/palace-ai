from __future__ import annotations

import http.server
import socketserver
import threading
import webbrowser
from pathlib import Path

from palace.visualizer.builder import build_visualizer


def serve_visualizer(repo_path: Path, *, port: int = 8765) -> None:
    repo_path = repo_path.resolve()
    palace_out = repo_path / "palace-out"
    build_visualizer(repo_path)

    handler = http.server.SimpleHTTPRequestHandler
    httpd: socketserver.TCPServer
    with socketserver.TCPServer(("127.0.0.1", port), handler) as httpd:
        httpd.allow_reuse_address = True
        # serve from palace_out so /visualizer/index.html works
        import os

        os.chdir(palace_out)
        url = f"http://127.0.0.1:{port}/visualizer/index.html"
        webbrowser.open(url)
        print(f"Serving {palace_out} at {url} (Ctrl+C to stop)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass

