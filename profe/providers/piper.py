"""旧名字，留着兼容。

2026-09-25 起离线合成换成了 local.py（拉美 Kokoro dora / 西班牙 Piper davefx），
`--provider piper` 仍然可用，走的就是 local。
"""

from .local import LocalProvider as PiperProvider  # noqa: F401
from .local import CACHE_DIR, ensure_model, rate_to_speed  # noqa: F401
