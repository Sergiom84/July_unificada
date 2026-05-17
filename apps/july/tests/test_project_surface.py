from __future__ import annotations

from pathlib import Path
import unittest

from july.project_surface import analyze_repository, inspect_repository_surface


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "test_repos"


def component_keys(surface):
    return {(component.role, component.tech, component.path) for component in surface.components}


class ProjectSurfaceTests(unittest.TestCase):
    def test_detects_flutter_and_node_components_in_subdirectories(self) -> None:
        repo = FIXTURE_ROOT / "flutter_node"

        surface = inspect_repository_surface(repo)
        analysis = analyze_repository(repo)

        self.assertEqual(surface.stack, ["flutter", "node"])
        self.assertIn(("frontend", "flutter", "flutter_app/"), component_keys(surface))
        self.assertIn(("backend", "node", "backend/"), component_keys(surface))
        self.assertIn("flutter_app/pubspec.yaml", surface.manifests)
        self.assertIn("backend/package.json", surface.manifests)
        self.assertEqual(
            analysis["components"],
            [
                {"role": "frontend", "tech": "flutter", "path": "flutter_app/"},
                {"role": "backend", "tech": "node", "path": "backend/"},
            ],
        )
        self.assertEqual(analysis["project_kind"], "mobile_app")

    def test_ignores_quarantine_legacy_manifests(self) -> None:
        repo = FIXTURE_ROOT / "quarantine_legacy"

        surface = inspect_repository_surface(repo)

        self.assertEqual(surface.stack, [])
        self.assertEqual(surface.components, [])
        self.assertNotIn("quarantine/react-vite-web/package.json", surface.manifests)

    def test_detects_python_only_project(self) -> None:
        repo = FIXTURE_ROOT / "python_only"

        surface = inspect_repository_surface(repo)
        analysis = analyze_repository(repo)

        self.assertEqual(surface.stack, ["python"])
        self.assertIn(("software", "python", "./"), component_keys(surface))
        self.assertEqual(analysis["project_kind"], "software")


if __name__ == "__main__":
    unittest.main()
