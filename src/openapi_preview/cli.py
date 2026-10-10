import argparse
import sys
from pathlib import Path

from .server import serve

SPEC_NAMES = ("openapi.yaml", "openapi.yml", "swagger.yaml", "swagger.yml")


def port_number(value: str) -> int:
    port = int(value)
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("port must be between 1 and 65535")
    return port


def find_spec(directory: Path) -> Path:
    matches = [directory / name for name in SPEC_NAMES if (directory / name).is_file()]
    if not matches:
        raise ValueError(f"No OpenAPI spec found in {directory}")
    if len(matches) > 1:
        names = "\n".join(f"  {path.name}" for path in matches)
        raise ValueError(
            f"Multiple OpenAPI specs found in {directory}:\n{names}\nSpecify one."
        )
    return matches[0]


def resolve_spec(value: str | None) -> Path:
    if value is None:
        return find_spec(Path.cwd())
    path = Path(value).expanduser().resolve()
    if path.is_dir():
        raise ValueError(f"Expected an OpenAPI spec file, got a directory: {path}")
    if not path.is_file():
        raise ValueError(f"OpenAPI spec file not found: {path}")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(prog="openapi")
    subparsers = parser.add_subparsers(dest="command", required=True)
    preview = subparsers.add_parser("preview", help="Preview an OpenAPI spec")
    preview.add_argument("path", nargs="?", help="OpenAPI YAML file")
    preview.add_argument(
        "--port", type=port_number, help="Port to serve on (default: 8000)"
    )
    args = parser.parse_args()
    try:
        spec = resolve_spec(args.path)
        serve(spec, args.port)
    except (OSError, ValueError) as error:
        print(f"openapi: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
