#!/usr/bin/env python3
"""Fetch rendered page content with Playwright Python."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import Page, async_playwright


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch rendered content from a page with Playwright Python.",
    )
    parser.add_argument("url", help="Page URL to open.")
    parser.add_argument(
        "--extract",
        default="title,text",
        help="Comma-separated fields: title,text,html,links,url.",
    )
    parser.add_argument(
        "--selector",
        default="body",
        help="Selector used for text/html extraction.",
    )
    parser.add_argument(
        "--wait-for-selector",
        help="Wait for this selector after navigation.",
    )
    parser.add_argument(
        "--wait-until",
        choices=("load", "domcontentloaded", "networkidle", "commit"),
        default="domcontentloaded",
        help="Navigation readiness event.",
    )
    parser.add_argument(
        "--timeout-ms",
        type=int,
        default=30000,
        help="Timeout for navigation and waits.",
    )
    parser.add_argument(
        "--delay-ms",
        type=int,
        default=0,
        help="Extra delay after page load before extraction.",
    )
    parser.add_argument("--user-data-dir", help="Persistent Chrome user data directory.")
    parser.add_argument(
        "--screenshot",
        help="Optional screenshot output path.",
    )
    parser.add_argument(
        "--output",
        help="Optional JSON output path.",
    )
    return parser.parse_args()


def default_user_data_dir() -> str:
    skill_root = Path(__file__).resolve().parent.parent
    return str(skill_root / ".playwright-user-data" / "fetch-content")


async def ensure_page(context) -> Page:
    if context.pages:
        return context.pages[0]
    return await context.new_page()


async def locator_html(page: Page, selector: str) -> str:
    return await page.locator(selector).first.evaluate("node => node.outerHTML")


async def extract_links(page: Page) -> list[dict[str, str]]:
    return await page.eval_on_selector_all(
        "a[href]",
        """elements => elements.map((el) => ({
            text: (el.textContent || '').trim(),
            href: el.href
        }))""",
    )


def write_output(data: dict[str, Any], output_path: str | None) -> None:
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    if output_path:
        Path(output_path).write_text(payload + "\n", encoding="utf-8")
    print(payload)


async def main_async() -> int:
    args = parse_args()
    fields = {item.strip() for item in args.extract.split(",") if item.strip()}
    results: dict[str, Any] = {"requested_url": args.url}
    user_data_dir = args.user_data_dir or default_user_data_dir()
    Path(user_data_dir).mkdir(parents=True, exist_ok=True)

    try:
        async with async_playwright() as playwright:
            context = await playwright.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                channel="chrome",
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                ],
                headless=False,
            )
            page = await ensure_page(context)
            await page.goto(args.url, wait_until=args.wait_until, timeout=args.timeout_ms)

            if args.wait_for_selector:
                await page.locator(args.wait_for_selector).first.wait_for(
                    timeout=args.timeout_ms
                )
            if args.delay_ms:
                await page.wait_for_timeout(args.delay_ms)

            if "url" in fields:
                results["url"] = page.url
            if "title" in fields:
                results["title"] = await page.title()
            if "text" in fields:
                results["text"] = await page.locator(args.selector).first.inner_text()
            if "html" in fields:
                results["html"] = await locator_html(page, args.selector)
            if "links" in fields:
                results["links"] = await extract_links(page)

            if args.screenshot:
                await page.screenshot(path=args.screenshot, full_page=True)
                results["screenshot"] = args.screenshot

            await context.close()
    except PlaywrightTimeoutError as exc:
        results["error"] = f"Timeout: {exc}"
        write_output(results, args.output)
        return 1
    except Exception as exc:  # pragma: no cover - runtime guard
        results["error"] = f"{type(exc).__name__}: {exc}"
        write_output(results, args.output)
        return 1

    write_output(results, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main_async()))
