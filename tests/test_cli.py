import argparse
from pathlib import Path

import pytest

from openapi_preview.cli import find_spec, port_number, resolve_spec


def test_discovery_and_ambiguous_specs(tmp_path: Path) -> None:
    spec = tmp_path / "openapi.yaml"
    spec.touch()
    assert find_spec(tmp_path) == spec
    assert resolve_spec(str(spec)) == spec
    (tmp_path / "swagger.yml").touch()
    with pytest.raises(ValueError, match="Multiple"):
        find_spec(tmp_path)


def test_port_range() -> None:
    assert port_number("8000") == 8000
    with pytest.raises(argparse.ArgumentTypeError):
        port_number("0")
