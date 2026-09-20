"""Kitaru Replay Lab — a narrow experiment, not an integration layer.

Wraps one RDAB execution path in explicit, serializable steps so a benchmark run can be
replayed from recorded model output instead of paying for it again, and so each step can
be carried into Kitaru as a session node.

Nothing here is imported by the normal runner. `dab run` is untouched.
"""

from .steps import STEP_NAMES, run_case
from .recorded import RecordedProvider, RecordedRunNotFound

__all__ = ["STEP_NAMES", "RecordedProvider", "RecordedRunNotFound", "run_case"]
