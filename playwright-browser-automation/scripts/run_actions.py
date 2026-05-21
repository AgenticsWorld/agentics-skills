#!/usr/bin/env python3
"""Run declarative browser actions with Playwright Python."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a JSON browser interaction plan with Playwright Python.",
    )
    parser.add_argument("--plan", required=True, help="Path to a JSON plan file.")
    parser.add_argument("--output", help="Optional JSON output path.")
    parser.add_argument("--user-data-dir", help="Persistent Chrome user data directory.")
    return parser.parse_args()


def load_plan(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_output(data: dict[str, Any], output_path: str | None) -> None:
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    if output_path:
        Path(output_path).write_text(payload + "\n", encoding="utf-8")
    print(payload)


def default_user_data_dir() -> str:
    skill_root = Path(__file__).resolve().parent.parent
    return str(skill_root / ".playwright-user-data" / "run-actions")


def require_selector(step: dict[str, Any]) -> str:
    selector = step.get("selector")
    if not selector:
        raise ValueError(f"Action {step.get('type')} requires a selector")
    return selector


async def ensure_page(context) -> Page:
    if context.pages:
        return context.pages[0]
    return await context.new_page()


async def run_plan(plan: dict[str, Any], user_data_dir: str | None) -> dict[str, Any]:
    results: dict[str, Any] = {
        "url": plan.get("url"),
        "saved": {},
        "steps": [],
    }

    timeout_ms = int(plan.get("timeout_ms", 30000))
    actions = plan.get("actions", [])
    persistent_user_data_dir = user_data_dir or plan.get("user_data_dir") or default_user_data_dir()
    Path(persistent_user_data_dir).mkdir(parents=True, exist_ok=True)

    async with async_playwright() as playwright:
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=persistent_user_data_dir,
            channel="chrome",
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
            headless=False,
        )
        page = await ensure_page(context)
        page.set_default_timeout(timeout_ms)

        if plan.get("url"):
            await page.goto(
                plan["url"],
                wait_until=plan.get("wait_until", "domcontentloaded"),
                timeout=timeout_ms,
            )

        for index, step in enumerate(actions, start=1):
            action_type = step["type"]
            step_result: dict[str, Any] = {"index": index, "type": action_type}

            if action_type == "goto":
                await page.goto(
                    step["value"],
                    wait_until=step.get("wait_until", "domcontentloaded"),
                    timeout=timeout_ms,
                )
            elif action_type == "click":
                await page.locator(require_selector(step)).first.click()
            elif action_type == "fill":
                await page.locator(require_selector(step)).first.fill(step.get("value", ""))
            elif action_type == "press":
                await page.locator(require_selector(step)).first.press(step["value"])
            elif action_type == "hover":
                await page.locator(require_selector(step)).first.hover()
            elif action_type == "check":
                await page.locator(require_selector(step)).first.check()
            elif action_type == "uncheck":
                await page.locator(require_selector(step)).first.uncheck()
            elif action_type == "select_option":
                await page.locator(require_selector(step)).first.select_option(step["value"])
            elif action_type == "wait_for_selector":
                await page.locator(require_selector(step)).first.wait_for(
                    state=step.get("state", "visible"),
                    timeout=timeout_ms,
                )
            elif action_type == "wait_for_url":
                await page.wait_for_url(step["value"], timeout=timeout_ms)
            elif action_type == "wait_for_timeout":
                await page.wait_for_timeout(int(step["value"]))
            elif action_type == "extract_text":
                value = await page.locator(require_selector(step)).first.inner_text()
                step_result["value"] = value
                if step.get("save_as"):
                    results["saved"][step["save_as"]] = value
            elif action_type == "extract_html":
                value = await page.locator(require_selector(step)).first.evaluate(
                    "node => node.outerHTML"
                )
                step_result["value"] = value
                if step.get("save_as"):
                    results["saved"][step["save_as"]] = value
            elif action_type == "extract_attribute":
                value = await page.locator(require_selector(step)).first.get_attribute(
                    step["name"]
                )
                step_result["value"] = value
                if step.get("save_as"):
                    results["saved"][step["save_as"]] = value
            elif action_type == "screenshot":
                path = step["path"]
                await page.screenshot(
                    path=path, full_page=bool(step.get("full_page", True))
                )
                step_result["path"] = path
            elif action_type == "assert_text_contains":
                text = await page.locator(require_selector(step)).first.inner_text()
                expected = step["value"]
                if expected not in text:
                    raise AssertionError(
                        f"Expected '{expected}' in selector {step['selector']}"
                    )
            elif action_type == "assert_visible":
                if not await page.locator(require_selector(step)).first.is_visible():
                    raise AssertionError(f"Selector is not visible: {step['selector']}")
            else:
                raise ValueError(f"Unsupported action type: {action_type}")

            results["steps"].append(step_result)

        results["final_url"] = page.url
        results["title"] = await page.title()
        results["user_data_dir"] = persistent_user_data_dir

        if plan.get("save_storage"):
            await context.storage_state(path=plan["save_storage"])
            results["storage_state"] = plan["save_storage"]

        await context.close()

    return results


async def main_async() -> int:
    args = parse_args()
    plan = load_plan(args.plan)

    try:
        result = await run_plan(plan, args.user_data_dir)
    except PlaywrightTimeoutError as exc:
        result = {"error": f"Timeout: {exc}"}
        write_output(result, args.output)
        return 1
    except Exception as exc:  # pragma: no cover - runtime guard
        result = {"error": f"{type(exc).__name__}: {exc}"}
        write_output(result, args.output)
        return 1

    write_output(result, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main_async()))
