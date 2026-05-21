# Playwright Python Codegen Workflow

Use this guide when the fastest path is to record browser actions and turn them into a reusable Python script.

## Record

Run Playwright's code generator against the target site:

```bash
playwright codegen https://example.com
```

Useful variants:

```bash
playwright codegen --save-storage=auth.json https://example.com
playwright codegen --load-storage=auth.json https://example.com
playwright codegen --device="iPhone 13" https://example.com
```

## Clean Up The Generated Python

After recording:

1. Keep the useful interactions.
2. Remove redundant clicks and duplicate waits.
3. Replace brittle selectors with stable role, label, text, or test-id locators.
4. Move the result into `scripts/` with a descriptive filename.
5. Add output behavior such as JSON logging, screenshots, or saved storage state if the script is meant to be reused.

## Save Location

Store reusable recorded scripts in this skill's `scripts/` directory, for example:

- `scripts/github_login_flow.py`
- `scripts/fill_search_form.py`
- `scripts/export_report.py`

## When To Prefer Codegen

Prefer codegen when:

- The site is easier to demonstrate than to describe
- The page has tricky locators or stateful UI
- You need a starting script quickly and will refine it afterward

Prefer `run_actions.py` when the workflow is simple and data-driven.
