#!/usr/bin/env python3
"""Explicit rejection shim for the retired v2.1-oa contract."""

from __future__ import annotations


LEGACY_SCHEMA = "v2.1-oa"
REJECTION_MESSAGE = (
    "v2.1-oa is unsupported. Create a fresh v2.2-oa case from stage-zero "
    "pre-application 1.1 source materials; no migration is provided."
)


def upgrade_to_v21(*_args: object, **_kwargs: object) -> None:
    raise RuntimeError(REJECTION_MESSAGE)


if __name__ == "__main__":
    raise SystemExit(REJECTION_MESSAGE)
