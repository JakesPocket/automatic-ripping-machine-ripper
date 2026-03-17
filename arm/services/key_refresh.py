"""Background task: refresh MakeMKV beta key once per day and cache validity."""

import asyncio
import logging
import os
import shutil
import subprocess

import arm.config.config as cfg

log = logging.getLogger(__name__)

REFRESH_INTERVAL = 86400  # 24 hours in seconds

# Cached result — None means "haven't checked yet"
_key_valid: bool | None = None


def is_key_valid() -> bool | None:
    """Return cached key validity. None = not yet checked."""
    return _key_valid


def _run_key_update() -> bool:
    """Run update_key.sh synchronously. Returns True if the key is valid."""
    cmd = [
        shutil.which("bash") or "/bin/bash",
        os.path.join(cfg.arm_config["INSTALLPATH"], "scripts/update_key.sh"),
    ]
    if cfg.arm_config.get("MAKEMKV_PERMA_KEY"):
        cmd.append(cfg.arm_config["MAKEMKV_PERMA_KEY"])

    proc = subprocess.run(cmd, capture_output=True, timeout=30)
    return proc.returncode == 0


async def daily_key_refresh() -> None:
    """Check and update the MakeMKV key at startup, then every 24 hours."""
    global _key_valid
    while True:
        try:
            ok = await asyncio.to_thread(_run_key_update)
            _key_valid = ok
            if ok:
                log.info("MakeMKV key is valid.")
            else:
                log.warning("MakeMKV key refresh failed — key may be expired.")
        except asyncio.CancelledError:
            raise
        except Exception:
            _key_valid = False
            log.exception("Error during MakeMKV key refresh")
        await asyncio.sleep(REFRESH_INTERVAL)
