import http.server
import mimetypes
import socket
import threading
import webbrowser
from pathlib import Path
from typing import cast
from urllib.parse import unquote, urlsplit

from swagger_ui_bundle import swagger_ui_path


class PreviewServer(http.server.ThreadingHTTPServer):
    def __init__(
        self,
        address: tuple[str, int],
        spec: Path,
        ui_dir: Path,
        stopping: threading.Event,
    ) -> None:
        self.spec = spec
        self.ui_dir = ui_dir
        self.stopping = stopping
        super().__init__(address, PreviewHandler)


class PreviewHandler(http.server.BaseHTTPRequestHandler):
    @property
    def preview_server(self) -> PreviewServer:
        return cast(PreviewServer, self.server)

    def do_GET(self) -> None:
        path = unquote(urlsplit(self.path).path)
        if path == "/":
            self.respond(200, "text/html; charset=utf-8", INDEX)
        elif path == "/openapi.yaml":
            try:
                data = self.preview_server.spec.read_bytes()
            except OSError:
                self.respond(404, "text/plain; charset=utf-8", "Spec file not found")
            else:
                self.respond(200, "application/yaml", data)
        elif path == "/events":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            self.wfile.write(b"retry: 1000\n\n")
            self.wfile.flush()
            try:
                previous: int | None = self.preview_server.spec.stat().st_mtime_ns
            except OSError:
                previous = None
            while not self.preview_server.stopping.wait(0.5):
                try:
                    current = self.preview_server.spec.stat().st_mtime_ns
                except OSError:
                    current = None
                try:
                    self.wfile.write(
                        b"data: reload\n\n"
                        if current != previous
                        else b": keepalive\n\n"
                    )
                    self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError):
                    break
                previous = current
        elif path.startswith("/ui/"):
            self.serve_asset(path[4:])
        else:
            self.respond(404, "text/plain; charset=utf-8", "Not found")

    def serve_asset(self, relative: str) -> None:
        ui_dir = self.preview_server.ui_dir
        target = (ui_dir / relative).resolve()
        if not target.is_relative_to(ui_dir.resolve()) or not target.is_file():
            self.respond(404, "text/plain; charset=utf-8", "Not found")
            return
        content_type = (
            mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        )
        self.respond(200, content_type, target.read_bytes())

    def respond(self, status: int, content_type: str, body: str | bytes) -> None:
        data = body.encode() if isinstance(body, str) else body
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args: object) -> None:
        pass


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def serve(spec: Path, requested_port: int | None = None) -> None:
    spec = spec.resolve()
    ui_dir = Path(swagger_ui_path)
    port = requested_port or 8000
    host = "127.0.0.1"
    stopping = threading.Event()

    try:
        server = PreviewServer((host, port), spec, ui_dir, stopping)
    except OSError as error:
        if requested_port is not None:
            raise OSError(f"Port {port} is already in use") from error
        port = free_port()
        server = PreviewServer((host, port), spec, ui_dir, stopping)
    server.daemon_threads = True
    url = f"http://{host}:{port}/"
    print(f"Previewing {spec}\n{url}", flush=True)

    threading.Timer(0.2, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stopping.set()
        server.shutdown()
        server.server_close()


INDEX = """<!doctype html>
<html><head><meta charset=\"utf-8\"><title>OpenAPI Preview</title>
<link rel=\"stylesheet\" href=\"/ui/swagger-ui.css\"></head>
<body><div id=\"swagger-ui\"></div>
<script src=\"/ui/swagger-ui-bundle.js\"></script>
<script>SwaggerUIBundle({url:'/openapi.yaml',dom_id:'#swagger-ui'});
new EventSource('/events').onmessage=()=>location.reload();</script></body></html>"""
