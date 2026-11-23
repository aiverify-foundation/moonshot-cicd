"""Optional feature-flag name codegen hook for local monorepo API startup."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def maybe_generate_feature_flags() -> None:
    """
    Regenerate name constants when scripts/generate_feature_flags.py is present.

    No-op in Docker runtime (generator / portal tree absent). Propagates
    SystemExit if generation is attempted and fails.
    """
    start = Path(__file__).resolve()
    script: Path | None = None
    for parent in start.parents:
        candidate = parent / "scripts" / "generate_feature_flags.py"
        if candidate.is_file():
            script = candidate
            break
    if script is None:
        return

    spec = importlib.util.spec_from_file_location(
        "_moonshot_generate_feature_flags", script
    )
    if spec is None or spec.loader is None:
        return
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    module.maybe_generate_feature_flags(start)
