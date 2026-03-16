#!/usr/bin/env python3
"""
Cron runner: executes PWA file checks, collects results as JSON,
and POSTs them to the N8N webhook.
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Setup project root
script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir))
os.chdir(script_dir)

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from src.utils.folder_checker import FolderChecker
from src.utils.file_operations import FileOperations
from src.config.settings import BASE_DIR, CONSULTAS_DIR, AUTOREMOVE_DIRS

N8N_WEBHOOK_URL = "https://n8n.srv921079.hstgr.cloud/webhook/b657fab8-c7ff-4a0c-90cc-0b49ce9a7411"

LOG_FILE = script_dir / "cron_runner.log"
logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def run_checks() -> dict:
    """Run all checks and return structured results."""
    results = {
        "timestamp": datetime.now().isoformat(),
        "base_dir": str(BASE_DIR),
        "checks": {},
    }

    # 0. Auto-remove junk folders
    import shutil
    removed = []
    for dirname in AUTOREMOVE_DIRS:
        target = BASE_DIR / dirname
        if target.exists():
            shutil.rmtree(target)
            removed.append(dirname)
    results["checks"]["autoremoved_folders"] = removed

    # 1. Inactive folders
    try:
        folder_checker = FolderChecker(BASE_DIR)
        inactive = folder_checker.find_inactive_folders(CONSULTAS_DIR)
        results["checks"]["inactive_folders"] = {
            "count": len(inactive),
            "folders": inactive,
        }
    except Exception as e:
        results["checks"]["inactive_folders"] = {"error": str(e)}

    # 2. Folder sizes
    try:
        file_ops = FileOperations(BASE_DIR)
        folder_sizes = file_ops.get_folder_sizes()
        top_10 = sorted(folder_sizes.items(), key=lambda x: x[1], reverse=True)[:10]
        results["checks"]["folder_sizes"] = {
            "top_10": [{"name": name, "size_mb": size} for name, size in top_10],
        }
    except Exception as e:
        results["checks"]["folder_sizes"] = {"error": str(e)}

    # 3. Model file replacement
    try:
        file_ops = FileOperations(BASE_DIR)
        success = file_ops.replace_model_files()
        results["checks"]["model_files_replaced"] = {"success": success}
    except Exception as e:
        results["checks"]["model_files_replaced"] = {"error": str(e)}

    # 4. Nonconforming names
    try:
        file_ops = FileOperations(BASE_DIR)
        nonconforming = file_ops.check_nonconforming_names()
        results["checks"]["nonconforming_names"] = {
            "count": len(nonconforming),
            "items": nonconforming,
        }
    except Exception as e:
        results["checks"]["nonconforming_names"] = {"error": str(e)}

    # 5. File naming issues
    try:
        file_ops = FileOperations(BASE_DIR)
        issues = file_ops.check_file_naming_issues()
        results["checks"]["file_naming_issues"] = {
            category: {"count": len(items), "items": items}
            for category, items in issues.items()
        }
    except Exception as e:
        results["checks"]["file_naming_issues"] = {"error": str(e)}

    return results


def post_to_webhook(data: dict) -> bool:
    """POST JSON results to N8N webhook via curl (handles TLS better)."""
    import subprocess
    import tempfile

    try:
        # Write JSON to temp file to avoid shell escaping issues
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f, ensure_ascii=False)
            tmp_path = f.name

        result = subprocess.run(
            [
                "curl", "-s", "-w", "%{http_code}",
                "-X", "GET",
                "-H", "Content-Type: application/json",
                "-d", f"@{tmp_path}",
                "--max-time", "30",
                N8N_WEBHOOK_URL,
            ],
            capture_output=True,
            text=True,
            timeout=35,
        )

        os.unlink(tmp_path)

        # Last 3 chars are the HTTP status code
        output = result.stdout
        status_code = output[-3:] if len(output) >= 3 else "000"
        body = output[:-3]

        if result.returncode == 0 and status_code.startswith("2"):
            logger.info(f"Webhook POST success: HTTP {status_code} - {body}")
            return True
        else:
            logger.error(f"Webhook POST failed: HTTP {status_code}, curl exit {result.returncode}, body: {body}, stderr: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Webhook POST failed: {e}")
        return False


def main():
    logger.info("=== Cron runner started ===")

    results = run_checks()
    logger.info(f"Checks completed. Found {len(results['checks'])} check categories.")

    # Save latest results locally as well
    results_file = script_dir / "latest_results.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    logger.info(f"Results saved to {results_file}")

    # Post to N8N
    if post_to_webhook(results):
        logger.info("Results posted to N8N successfully.")
    else:
        logger.error("Failed to post results to N8N.")

    logger.info("=== Cron runner finished ===")


if __name__ == "__main__":
    main()
