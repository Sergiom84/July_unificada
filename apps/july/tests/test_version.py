from __future__ import annotations

import unittest

import july


class VersionTests(unittest.TestCase):
    def test_package_version_is_semver(self) -> None:
        self.assertRegex(july.__version__, r"^\d+\.\d+\.\d+$")


if __name__ == "__main__":
    unittest.main()
