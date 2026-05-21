# Playwright Python Notes

## Default Coding Direction

- Prefer `async_playwright()` for this skill's reusable scripts.
- Launch Chrome with `launch_persistent_context(...)` so the script can reuse profile state and feel more like a real browser session.
- Standardize on Chromium via `playwright.chromium` with `channel="chrome"` for this skill.

## Extraction Guidance

- Use `page.goto(..., wait_until="domcontentloaded")` as a practical default.
- Add `wait_for_selector` when the useful content appears after hydration.
- Extract from a focused selector instead of dumping the entire page when the user wants a specific section.
- Return structured JSON so the caller can reuse the result in later automation steps.

## Selector Guidance

- Prefer role, text, label, placeholder, and test-id based locators.
- Avoid deep CSS chains that are likely to break.
- Let codegen suggest a locator first, then simplify it if it stays stable.
