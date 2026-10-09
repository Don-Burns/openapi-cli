# OpenAPI Preview

A local preview server for OpenAPI YAML files. It serves the spec with Swagger UI and refreshes the browser when the file changes.

## Usage

```sh
openapi preview [PATH] [--port PORT]
```

Examples:

```sh
# Discover a spec in the current directory
openapi preview

# Preview a specific spec
openapi preview ./api/openapi.yaml

# Request a specific port
openapi preview ./api/openapi.yaml --port 8080
```

When `PATH` is omitted, the current directory is searched for these filenames:

- `openapi.yaml`
- `openapi.yml`
- `swagger.yaml`
- `swagger.yml`

Discovery is limited to the current directory. If multiple matching files are found, the command reports them and asks you to specify one. A directory supplied as `PATH` is not valid; pass a spec file instead.

Without `--port`, the server uses port `8000` when available and otherwise selects an available port automatically. If `--port` is supplied and that port is already in use, the command exits with an error.

The server listens on the local machine and opens the preview in your browser. Swagger UI assets are bundled with the application and served locally, so loading the UI does not require a CDN or an internet connection. The selected spec is watched for changes; saving it reloads the preview page.

## Development

This project uses [uv](https://docs.astral.sh/uv/) to manage Python and project dependencies.

```sh
# Install uv first, if needed: https://docs.astral.sh/uv/getting-started/installation/

# Install project and development dependencies
uv sync --group dev

# Enable lint/type checks
uv run pre-commit install

# Run the CLI from the project environment
uv run openapi preview ./api/openapi.yaml

# Run checks and tests
uv run pre-commit run --all-files
uv run pytest
```

After changing project dependencies, update `pyproject.toml` and the lockfile with `uv add` or `uv remove`, then run `uv sync`.

Releases use [release-please](https://github.com/googleapis/release-please). Use Conventional Commit messages (`fix:`, `feat:`, and `feat!:`); release-please opens a version/changelog PR and creates the `vX.Y.Z` tag and GitHub Release when that PR is merged.

## Implementation notes

- Python provides the CLI and local HTTP server.
- [Swagger UI](https://swagger.io/open-source/swagger-ui/)'s JavaScript and CSS are packaged with the application and served from the local server.
- A file watcher detects changes to the selected spec and triggers a browser reload.
- One spec file is previewed per server process.
