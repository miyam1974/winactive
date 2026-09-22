"""Tests for winactive.py. Run with: python -m unittest discover -s tests"""

from __future__ import annotations

import argparse
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import winactive  # noqa: E402  (import after sys.path setup)


class ParseDurationTests(unittest.TestCase):
    def test_seconds_suffix(self) -> None:
        self.assertEqual(winactive.parse_duration("5s"), 5)

    def test_minutes_suffix(self) -> None:
        self.assertEqual(winactive.parse_duration("30m"), 1800)

    def test_hours_suffix(self) -> None:
        self.assertEqual(winactive.parse_duration("2h"), 7200)

    def test_no_suffix_defaults_to_minutes(self) -> None:
        self.assertEqual(winactive.parse_duration("90"), 5400)

    def test_decimal_value(self) -> None:
        self.assertEqual(winactive.parse_duration("1.5h"), 5400)

    def test_empty_string_raises(self) -> None:
        with self.assertRaises(argparse.ArgumentTypeError):
            winactive.parse_duration("")

    def test_non_numeric_value_raises(self) -> None:
        with self.assertRaises(argparse.ArgumentTypeError):
            winactive.parse_duration("abc")

    def test_zero_duration_raises(self) -> None:
        with self.assertRaises(argparse.ArgumentTypeError):
            winactive.parse_duration("0s")

    def test_negative_duration_raises(self) -> None:
        with self.assertRaises(argparse.ArgumentTypeError):
            winactive.parse_duration("-5m")


class BuildFlagsTests(unittest.TestCase):
    def test_default_keeps_display_awake(self) -> None:
        flags = winactive.build_flags(keep_display=True, away_mode=False)
        expected = (
            winactive.ES_CONTINUOUS
            | winactive.ES_SYSTEM_REQUIRED
            | winactive.ES_DISPLAY_REQUIRED
        )
        self.assertEqual(flags, expected)

    def test_no_display_allows_screen_off(self) -> None:
        flags = winactive.build_flags(keep_display=False, away_mode=False)
        expected = winactive.ES_CONTINUOUS | winactive.ES_SYSTEM_REQUIRED
        self.assertEqual(flags, expected)

    def test_away_mode_adds_flag(self) -> None:
        flags = winactive.build_flags(keep_display=True, away_mode=True)
        expected = (
            winactive.ES_CONTINUOUS
            | winactive.ES_SYSTEM_REQUIRED
            | winactive.ES_DISPLAY_REQUIRED
            | winactive.ES_AWAYMODE_REQUIRED
        )
        self.assertEqual(flags, expected)


@unittest.skipUnless(sys.platform == "win32", "SetThreadExecutionState is Windows-only")
class SetExecutionStateTests(unittest.TestCase):
    def test_success_does_not_raise(self) -> None:
        with mock.patch.object(
            winactive.ctypes.windll.kernel32,
            "SetThreadExecutionState",
            return_value=1,
        ):
            winactive.set_execution_state(winactive.ES_CONTINUOUS)

    def test_failure_raises_winerror(self) -> None:
        with mock.patch.object(
            winactive.ctypes.windll.kernel32,
            "SetThreadExecutionState",
            return_value=0,
        ):
            with self.assertRaises(OSError):
                winactive.set_execution_state(winactive.ES_CONTINUOUS)


@unittest.skipUnless(sys.platform == "win32", "winactive only runs on Windows")
class SmokeTestCli(unittest.TestCase):
    def test_once_flag_exits_successfully(self) -> None:
        script = Path(__file__).resolve().parent.parent / "winactive.py"
        result = subprocess.run(
            [sys.executable, str(script), "--once"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Smoke test succeeded.", result.stdout)


if __name__ == "__main__":
    unittest.main()
