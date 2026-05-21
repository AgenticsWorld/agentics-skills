---
name: playwright-browser-automation
description: Use when an agent needs to fetch rendered web content or automate browser interactions with Playwright Python. Trigger on requests to scrape JavaScript-heavy pages, extract title, text, HTML, or links after page load, take screenshots, log in and click through flows, fill forms, replay or adapt Playwright Python codegen output, or save reusable browser automation scripts under a skill's scripts/ directory.
---

# Playwright Browser Automation

## Overview

Use Playwright Python to read dynamically rendered pages and automate multi-step browser workflows. Keep reusable executable scripts in `scripts/`, and keep process guidance in `references/`.

## Workflow

1. Classify the request as one of:
- Content retrieval from a rendered page
- Reusable browser interaction flow
- Codegen capture that should be cleaned and saved as a reusable script

2. Use the async Playwright API and launch Chrome with a persistent context. Standardize browser startup on:

```python
await playwright.chromium.launch_persistent_context(
    user_data_dir=user_data_dir,
    channel="chrome",
    args=[
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox"
    ],
    headless=False
)
```

3. Before writing new code, check whether one of the bundled scripts already fits:
- `scripts/fetch_content.py` for rendered-page extraction
- `scripts/run_actions.py` for declarative click/fill/wait/extract flows
- `scripts/generated_interaction_example.py` for codegen-style adaptation

4. When the user wants a recorded browser flow, use Playwright codegen, then clean the generated Python and save the reusable result in this skill's `scripts/` directory instead of leaving it as an ad hoc snippet.

5. Prefer resilient selectors:
- Role, text, label, placeholder, and test-id based locators first
- Avoid brittle CSS chains unless the page gives no better hook
- Preserve useful waits around navigation, dialogs, and dynamic content

6. Return structured outputs whenever possible:
- JSON for extracted page data
- File paths for screenshots or saved storage state
- A small summary of what the script did and any assumptions made

## Script Patterns

### Fetch rendered content

Use `scripts/fetch_content.py` when the task is "open a page and get the content after JavaScript runs". It can extract title, text, HTML, and links, and can optionally save a screenshot.

Example:

```bash
python scripts/fetch_content.py "https://example.com" \
  --extract title,text,links \
  --user-data-dir ./chrome-profile \
  --wait-for-selector "main" \
  --output result.json
```

### Automate interactions declaratively

Use `scripts/run_actions.py` when the workflow can be described as a JSON plan. This keeps many browser jobs reusable without regenerating Python every time.

Plan shape:

```json
{
  "url": "https://example.com/login",
  "user_data_dir": "./chrome-profile",
  "actions": [
    {"type": "fill", "selector": "input[name='email']", "value": "user@example.com"},
    {"type": "fill", "selector": "input[name='password']", "value": "secret"},
    {"type": "click", "selector": "button[type='submit']"},
    {"type": "wait_for_url", "value": "**/dashboard"},
    {"type": "extract_text", "selector": "main", "save_as": "dashboard_text"}
  ]
}
```

Then run:

```bash
python scripts/run_actions.py --plan plan.json --output result.json
```

### Capture a flow with codegen

Use Playwright's official code generator when a task is easier to record than to hand-write. Save the cleaned Python result under `scripts/` with a specific name such as `scripts/github_login_flow.py`.

Use `references/codegen-workflow.md` for the recording steps and cleanup checklist.

## Notes

Keep generated scripts executable, single-purpose, and easy to patch. If authentication is involved, prefer `--save-storage` / `--load-storage` flows over hard-coding credentials inside the script.

These bundled scripts always use `async_api` plus `launch_persistent_context(...)` with Chrome and `headless=False`.

Read `references/playwright-python-notes.md` when you need install commands, browser setup reminders, or selector guidance.
