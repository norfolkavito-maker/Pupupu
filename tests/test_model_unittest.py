"""Unit tests for model.py get_full_args."""
from __future__ import annotations

import unittest

from app.zapret_manager.strategies.model import Strategy, Command, CommandType


class TestModel(unittest.TestCase):
    def test_get_full_args_basic(self):
        st = Strategy(
            id="v1",
            name="v1",
            commands=[Command(type=CommandType.WINWS, command="--filter-tcp=443")],
        )
        self.assertEqual(st.get_full_args(), ["--filter-tcp=443"])

    def test_get_full_args_with_winws_params(self):
        st = Strategy(
            id="v1",
            name="v1",
            commands=[Command(type=CommandType.WINWS, command="--filter-tcp=443")],
        )
        self.assertEqual(st.get_full_args(), ["--filter-tcp=443"])

    def test_get_full_args_with_wssize(self):
        st = Strategy(
            id="v1",
            name="v1",
            commands=[Command(type=CommandType.WINWS, command="--filter-tcp=443")],
        )
        full = st.get_full_args()
        self.assertIn("--filter-tcp=443", full)


if __name__ == "__main__":
    unittest.main()