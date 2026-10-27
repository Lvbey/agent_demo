import tempfile
import unittest
from pathlib import Path

import tools


class ToolSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_workspace = tools.WORKSPACE
        tools.WORKSPACE = Path(self.temp_dir.name).resolve()

    def tearDown(self):
        tools.WORKSPACE = self.original_workspace
        self.temp_dir.cleanup()

    def test_workspace_file_round_trip(self):
        written = tools.write_file("notes/todo.txt", "第一项\n第二项")
        self.assertTrue(written["ok"], written)
        read = tools.read_file("notes/todo.txt")
        self.assertTrue(read["ok"], read)
        self.assertEqual(read["content"], "第一项\n第二项")

    def test_path_traversal_is_rejected(self):
        with self.assertRaises(ValueError):
            tools._inside_workspace("../outside.txt")

    def test_absolute_path_is_rejected(self):
        with self.assertRaises(ValueError):
            tools._inside_workspace(str(Path(self.temp_dir.name).parent / "outside.txt"))

    def test_local_web_address_is_blocked_before_request(self):
        result = tools.read_webpage("http://127.0.0.1/")
        self.assertFalse(result["ok"])
        self.assertIn("blocked", result["error"].lower())

    def test_non_http_scheme_is_rejected(self):
        result = tools.read_webpage("file:///etc/passwd")
        self.assertFalse(result["ok"])
        self.assertIn("http", result["error"].lower())


if __name__ == "__main__":
    unittest.main()
