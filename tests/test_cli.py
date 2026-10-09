import argparse
import tempfile
import unittest
from pathlib import Path

from openapi_preview.cli import find_spec, port_number, resolve_spec


class CliTests(unittest.TestCase):
    def test_discovery_and_ambiguous_specs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            spec = root / "openapi.yaml"
            spec.touch()
            self.assertEqual(find_spec(root), spec)
            self.assertEqual(resolve_spec(str(spec)), spec)
            (root / "swagger.yml").touch()
            with self.assertRaisesRegex(ValueError, "Multiple"):
                find_spec(root)

    def test_port_range(self):
        self.assertEqual(port_number("8000"), 8000)
        with self.assertRaises(argparse.ArgumentTypeError):
            port_number("0")


if __name__ == "__main__":
    unittest.main()
