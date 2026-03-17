"""Background task: refresh MakeMKV beta key once per day."""

import asyncio
import logging
import os
import shutil
import subprocess

import arm.config.config as cfg

log = logging.getLogger(__name__)

REFRESH_INTERVAL = 86400  # 24 hours in seconds


async def daily_key_refresh() -> None:
    """Run update_key.sh once every 24 hours in the background."""
    # Wait before first run — startup already calls prep_mkv on first rip
    await asyncio.sleep(REFRESH_INTERVAL)
    while True:
        try:
            cmd = [
                shutil.which("bash") or "/bin/bash",
                os.path.join(cfg.arm_config["INSTALLPATH"], "scripts/update_key.sh"),
            ]
            if cfg.arm_config.get("MAKEMKV_PERMA_KEY"):
                cmd.append(cfg.arm_config["MAKEMKV_PERMA_KEY"])

            proc = await asyncio.to_thread(
                subprocess.run, cmd, capture_output=True, timeout=30
            )
            stdout = proc.stdout.decode("utf-8", errors="replace").strip()
            if proc.returncode == 0:
                log.info("Daily MakeMKV key refresh succeeded: %s", stdout)
            else:
                log.warning(
                    "Daily MakeMKV key refresh failed (rc=%d): %s",
                    proc.returncode, stdout,
                )
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("Error during daily MakeMKV key refresh")
        await asyncio.sleep(REFRESH_INTERVAL)
