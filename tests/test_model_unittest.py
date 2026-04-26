"""Unit tests for model.py get_full_args."""
from __future__ import annotations

import unittest

from app.zapret_manager.strategies.model import Strategy


class TestModel(unittest.TestCase):
    def test_get_full_args_basic(self):
        st = Strategy(name="v1", engine="winws", args=["--filter-tcp=443"])
        self.assertEqual(st.get_full_args(), ["--filter-tcp=443"])

    def test_get_full_args_with_winws_params(self):
        st = Strategy(name="v1", engine="winws", args=["--filter-tcp=443"], winws_params=["--hostlist-exclude", "localhost"])
        self.assertEqual(st.get_full_args(), ["--filter-tcp=443", "--hostlist-exclude", "localhost"])

    def test_get_full_args_with_wssize(self):
        st = Strategy(name="v1", engine="winws", args=["--filter-tcp=443"], wssize="1:6")
        full = st.get_full_args()
        self.assertIn("--new", full)
        self.assertIn("--filter-tcp=443", full)
        self.assertIn("--wssize", full)
        self.assertIn("1:6", full)
        self.assertNotIn("--wssize-max", full)  # bug fixed


if __name__ == "__main__":
    unittest.main()
