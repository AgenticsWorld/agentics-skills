#!/usr/bin/env python3
"""Codegen-style Playwright Python example for quick adaptation."""

import asyncio
from pathlib import Path

from playwright.async_api import Playwright, async_playwright


async def run(playwright: Playwright) -> None:
    context = await playwright.chromium.launch_persistent_context(
        user_data_dir="/Users/mathwallet/.agetics-dev/chrome/user-data",
        channel="chrome",
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
        ],
        headless=False,
    )
    page = context.pages[0] if context.pages else await context.new_page()
    await page.goto("https://demo.playwright.dev/todomvc/")
    await page.get_by_placeholder("What needs to be done?").click()
    await page.get_by_placeholder("What needs to be done?").fill("Review Playwright workflow")
    await page.get_by_placeholder("What needs to be done?").press("Enter")
    await page.get_by_placeholder("What needs to be done?").fill("Save reusable script")
    await page.get_by_placeholder("What needs to be done?").press("Enter")
    await page.get_by_label("Toggle Todo").first.check()
    await page.screenshot(path="todomvc-example.png")
    await context.close()


async def main() -> None:
    async with async_playwright() as playwright:
        await run(playwright)


if __name__ == "__main__":
    asyncio.run(main())
