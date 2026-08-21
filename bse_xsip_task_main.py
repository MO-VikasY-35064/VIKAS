from __future__ import annotations

import json
import logging
import os
import traceback
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

from dotenv import load_dotenv
from playwright.sync_api import Browser, BrowserContext, Page, TimeoutError as PlaywrightTimeoutError, sync_playwright

load_dotenv()


def as_bool(value: str | None, default: bool = True) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y"}


@dataclass(frozen=True)
class AppConfig:
    username: str
    member_id: str
    password: str
    base_url: str
    login_url: str
    output_dir: Path
    log_dir: Path
    screenshot_dir: Path
    headless: bool
    timeout_ms: int
    slow_mo_ms: int


def load_config() -> AppConfig:
    username = os.getenv("BSE_USERNAME", "044607").strip()
    member_id = os.getenv("BSE_MEMBER_ID", "0446").strip()
    password = os.getenv("BSE_PASSWORD", "").strip()
    base_url = os.getenv("BSE_BASE_URL", "https://www.bsestarmf.in").strip()
    login_url = os.getenv("BSE_LOGIN_URL", "https://www.bsestarmf.in/StarMFWeb/Login.aspx").strip()
    output_dir = Path(os.getenv("OUTPUT_DIR", "output/downloads"))
    log_dir = Path(os.getenv("LOG_DIR", "output/logs"))
    screenshot_dir = Path(os.getenv("SCREENSHOT_DIR", "output/logs/screenshots"))
    headless = as_bool(os.getenv("HEADLESS"), True)
    timeout_ms = int(os.getenv("TIMEOUT_MS", "60000"))
    slow_mo_ms = int(os.getenv("SLOW_MO_MS", "0"))

    if not password:
        raise ValueError("Missing required environment variable: BSE_PASSWORD")

    output_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    screenshot_dir.mkdir(parents=True, exist_ok=True)

    return AppConfig(
        username=username,
        member_id=member_id,
        password=password,
        base_url=base_url,
        login_url=login_url,
        output_dir=output_dir,
        log_dir=log_dir,
        screenshot_dir=screenshot_dir,
        headless=headless,
        timeout_ms=timeout_ms,
        slow_mo_ms=slow_mo_ms,
    )


SELECTORS = {
    "username": [
        "input[name='txtUserId']",
        "input[id*='txtUserId']",
        "input[placeholder*='User']",
    ],
    "member_id": [
        "input[name='txtMemberId']",
        "input[id*='txtMemberId']",
        "input[placeholder*='Member']",
    ],
    "password": [
        "input[type='password']",
        "input[name='txtPassword']",
        "input[id*='txtPassword']",
    ],
    "login_button": [
        "input[type='submit'][value*='Login']",
        "button:has-text('Login')",
        "input[id*='btnLogin']",
    ],
    "post_login_marker": [
        "text=Daily Downloads",
        "text=XSIP/SIP",
    ],
    "daily_downloads_menu": [
        "text=Daily Downloads",
        "a:has-text('Daily Downloads')",
    ],
    "xsip_sip_menu": [
        "text=XSIP/SIP",
        "a:has-text('XSIP/SIP')",
    ],
    "matured_report_menu": [
        "text=Matured XSIP Registration Report",
        "a:has-text('Matured XSIP Registration Report')",
    ],
    "from_date": [
        "input[name*='From']",
        "input[id*='From']",
        "input[placeholder*='From']",
    ],
    "to_date": [
        "input[name*='To']",
        "input[id*='To']",
        "input[placeholder*='To']",
    ],
    "generate_button": [
        "input[type='submit'][value*='Generate']",
        "button:has-text('Generate')",
        "input[value*='View']",
        "button:has-text('Download')",
        "input[value*='Download']",
    ],
    "report_page_marker": [
        "text=Matured XSIP Registration Report",
        "text=From Date",
    ],
}


def setup_logger(log_dir: Path) -> logging.Logger:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"bse_xsip_maturity_{timestamp}.log"

    logger = logging.getLogger("bse_xsip_maturity")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info("Logger initialized")
    logger.info("Log file: %s", log_file)
    return logger


def first_day_of_current_month_ddmmyyyy() -> str:
    return datetime.now().replace(day=1).strftime("%d-%m-%Y")


def execution_timestamp_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def resolve_download_filename(suggested_filename: str | None) -> str:
    if suggested_filename and suggested_filename.strip():
        return suggested_filename.strip()
    return f"matured_xsip_registration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.dat"


def verify_file_downloaded(path: Path) -> bool:
    return path.exists() and path.is_file() and path.stat().st_size > 0


def click_first_available(page: Page, candidates: Iterable[str], timeout_ms: int) -> bool:
    for selector in candidates:
        locator = page.locator(selector).first
        try:
            locator.wait_for(state="visible", timeout=timeout_ms // 3)
            locator.click()
            return True
        except Exception:
            continue
    return False


def fill_first_available(page: Page, candidates: Iterable[str], value: str, timeout_ms: int) -> bool:
    for selector in candidates:
        locator = page.locator(selector).first
        try:
            locator.wait_for(state="visible", timeout=timeout_ms // 3)
            locator.fill("")
            locator.fill(value)
            return True
        except Exception:
            continue
    return False


def get_input_value_if_available(page: Page, candidates: Iterable[str]) -> Optional[str]:
    for selector in candidates:
        locator = page.locator(selector).first
        try:
            if locator.count() > 0:
                return locator.input_value()
        except Exception:
            continue
    return None


def capture_failure_screenshot(page: Page | None, screenshot_dir: Path, logger, label: str) -> str | None:
    if page is None:
        return None

    screenshot_path = screenshot_dir / f"{label}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    try:
        page.screenshot(path=str(screenshot_path), full_page=True)
        logger.info("Failure screenshot saved: %s", screenshot_path)
        return str(screenshot_path)
    except Exception as exc:
        logger.error("Unable to capture screenshot: %s", exc)
        return None


def persist_summary(config: AppConfig, logger: logging.Logger, summary: dict) -> None:
    summary_file = config.log_dir / f"execution_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    summary["summary_file"] = str(summary_file)
    summary_file.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Execution summary: %s", json.dumps(summary, ensure_ascii=False))


def login(page: Page, config: AppConfig, logger: logging.Logger) -> bool:
    logger.info("Opening login URL: %s", config.login_url)
    page.goto(config.login_url, wait_until="domcontentloaded", timeout=config.timeout_ms)

    username_ok = fill_first_available(page, SELECTORS["username"], config.username, config.timeout_ms)
    member_ok = fill_first_available(page, SELECTORS["member_id"], config.member_id, config.timeout_ms)
    password_ok = fill_first_available(page, SELECTORS["password"], config.password, config.timeout_ms)

    if not (username_ok and member_ok and password_ok):
        logger.error("Unable to locate one or more login fields")
        return False

    if not click_first_available(page, SELECTORS["login_button"], config.timeout_ms):
        logger.error("Unable to locate login button")
        return False

    for marker in SELECTORS["post_login_marker"]:
        try:
            page.locator(marker).first.wait_for(state="visible", timeout=config.timeout_ms)
            logger.info("Login successful")
            return True
        except Exception:
            continue

    logger.error("Login may have failed: post-login markers not found")
    return False


def navigate_to_report(page: Page, config: AppConfig, logger: logging.Logger) -> bool:
    logger.info("Navigating to Matured XSIP Registration Report")

    if not click_first_available(page, SELECTORS["daily_downloads_menu"], config.timeout_ms):
        logger.error("Daily Downloads menu not found")
        return False

    if not click_first_available(page, SELECTORS["xsip_sip_menu"], config.timeout_ms):
        logger.error("XSIP/SIP menu not found")
        return False

    if not click_first_available(page, SELECTORS["matured_report_menu"], config.timeout_ms):
        logger.error("Matured XSIP Registration Report menu not found")
        return False

    for marker in SELECTORS["report_page_marker"]:
        try:
            page.locator(marker).first.wait_for(state="visible", timeout=config.timeout_ms)
            logger.info("Report navigation successful")
            return True
        except Exception:
            continue

    logger.error("Report page markers not found after navigation")
    return False


def set_from_date_leave_to_date_unchanged(page: Page, config: AppConfig, logger: logging.Logger) -> tuple[str, bool]:
    from_date = first_day_of_current_month_ddmmyyyy()
    logger.info("Calculated From Date: %s", from_date)

    if not fill_first_available(page, SELECTORS["from_date"], from_date, config.timeout_ms):
        raise RuntimeError("Unable to locate/fill From Date field")

    to_date_before = get_input_value_if_available(page, SELECTORS["to_date"])
    logger.info("Current To Date value before submission: %s", to_date_before if to_date_before else "<not readable>")

    return from_date, True


def generate_and_download(page: Page, config: AppConfig, logger: logging.Logger) -> tuple[bool, str | None]:
    logger.info("Starting report generation/download")

    with page.expect_download(timeout=config.timeout_ms) as download_info:
        if not click_first_available(page, SELECTORS["generate_button"], config.timeout_ms):
            raise RuntimeError("Unable to locate Generate/Download button")

    download = download_info.value
    filename = resolve_download_filename(download.suggested_filename)
    final_path = config.output_dir / filename
    download.save_as(str(final_path))

    if verify_file_downloaded(final_path):
        logger.info("Download successful: %s", final_path.name)
        return True, final_path.name

    logger.error("Download verification failed for file: %s", final_path)
    return False, final_path.name


def run_automation() -> int:
    config = load_config()
    logger = setup_logger(config.log_dir)

    summary = {
        "login_status": "failed",
        "report_navigation_status": "failed",
        "from_date_selected": None,
        "to_date_unchanged": True,
        "download_status": "failed",
        "downloaded_filename": None,
        "execution_timestamp": execution_timestamp_iso(),
        "summary_file": None,
        "failure_screenshot": None,
        "error_message": None,
    }

    playwright = None
    browser: Browser | None = None
    context: BrowserContext | None = None
    page: Page | None = None

    try:
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(headless=config.headless, slow_mo=config.slow_mo_ms)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        page.set_default_timeout(config.timeout_ms)

        if login(page, config, logger):
            summary["login_status"] = "successful"
        else:
            summary["failure_screenshot"] = capture_failure_screenshot(page, config.screenshot_dir, logger, "login_failed")
            persist_summary(config, logger, summary)
            return 1

        if navigate_to_report(page, config, logger):
            summary["report_navigation_status"] = "successful"
        else:
            summary["failure_screenshot"] = capture_failure_screenshot(page, config.screenshot_dir, logger, "navigation_failed")
            persist_summary(config, logger, summary)
            return 1

        from_date, to_date_unchanged = set_from_date_leave_to_date_unchanged(page, config, logger)
        summary["from_date_selected"] = from_date
        summary["to_date_unchanged"] = to_date_unchanged

        download_ok, downloaded_filename = generate_and_download(page, config, logger)
        summary["download_status"] = "successful" if download_ok else "failed"
        summary["downloaded_filename"] = downloaded_filename

        if not download_ok:
            summary["failure_screenshot"] = capture_failure_screenshot(page, config.screenshot_dir, logger, "download_failed")

        persist_summary(config, logger, summary)
        return 0 if download_ok else 1

    except PlaywrightTimeoutError as exc:
        logger.error("Playwright timeout error: %s", exc)
        logger.debug(traceback.format_exc())
        summary["error_message"] = str(exc)
        summary["failure_screenshot"] = capture_failure_screenshot(page, config.screenshot_dir, logger, "timeout")
        persist_summary(config, logger, summary)
        return 1
    except Exception as exc:
        logger.error("Unhandled error: %s", exc)
        logger.debug(traceback.format_exc())
        summary["error_message"] = str(exc)
        summary["failure_screenshot"] = capture_failure_screenshot(page, config.screenshot_dir, logger, "exception")
        persist_summary(config, logger, summary)
        return 1
    finally:
        try:
            if context:
                context.close()
        finally:
            try:
                if browser:
                    browser.close()
            finally:
                if playwright:
                    playwright.stop()


if __name__ == "__main__":
    raise SystemExit(run_automation())