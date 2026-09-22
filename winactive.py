"""Keep a Windows session awake while long-running work is active.

This uses SetThreadExecutionState instead of simulating mouse or keyboard input.
"""

from __future__ import annotations

import argparse
import ctypes
import signal
import sys
import time
from datetime import datetime, timedelta


ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002
ES_AWAYMODE_REQUIRED = 0x00000040


def set_execution_state(flags: int) -> None:
    result = ctypes.windll.kernel32.SetThreadExecutionState(flags)
    if result == 0:
        raise ctypes.WinError()


def parse_duration(value: str) -> int:
    units = {"s": 1, "m": 60, "h": 3600}
    text = value.strip().lower()
    if not text:
        raise argparse.ArgumentTypeError("duration cannot be empty")

    suffix = text[-1]
    if suffix in units:
        number = text[:-1]
        multiplier = units[suffix]
    else:
        number = text
        multiplier = 60

    try:
        amount = float(number)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid duration: {value}") from exc

    seconds = int(amount * multiplier)
    if seconds <= 0:
        raise argparse.ArgumentTypeError("duration must be greater than zero")
    return seconds


def build_flags(keep_display: bool, away_mode: bool) -> int:
    flags = ES_CONTINUOUS | ES_SYSTEM_REQUIRED
    if keep_display:
        flags |= ES_DISPLAY_REQUIRED
    if away_mode:
        flags |= ES_AWAYMODE_REQUIRED
    return flags


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prevent Windows sleep/display idle while this process is running."
    )
    parser.add_argument(
        "--duration",
        type=parse_duration,
        help="Stop automatically after this duration. Examples: 30m, 2h, 90. Default unit is minutes.",
    )
    parser.add_argument(
        "--interval",
        type=parse_duration,
        default=60,
        help="How often to refresh the execution state. Default: 60 seconds.",
    )
    parser.add_argument(
        "--no-display",
        action="store_true",
        help="Keep the system awake but allow the display to turn off.",
    )
    parser.add_argument(
        "--away-mode",
        action="store_true",
        help="Request away mode as well. Useful mainly on desktop-class Windows systems.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Set the execution state once, print success, then restore it. Used for smoke tests.",
    )
    args = parser.parse_args()

    if sys.platform != "win32":
        print("winactive only works on Windows.", file=sys.stderr)
        return 2

    print(parser.format_help())
    flags = build_flags(keep_display=not args.no_display, away_mode=args.away_mode)
    stop_requested = False

    def request_stop(_signum: int, _frame: object) -> None:
        nonlocal stop_requested
        stop_requested = True

    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)

    end_at = datetime.now() + timedelta(seconds=args.duration) if args.duration else None

    try:
        set_execution_state(flags)
        print("Windows execution state is active. Press Ctrl+C to stop.")
        if args.once:
            print("Smoke test succeeded.")
            return 0

        while not stop_requested:
            if end_at and datetime.now() >= end_at:
                print("Duration elapsed; stopping.")
                break
            time.sleep(args.interval)
            set_execution_state(flags)
    finally:
        set_execution_state(ES_CONTINUOUS)
        print("Windows execution state restored.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())