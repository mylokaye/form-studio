# Style Dynamics forms

A Codex skill for restyling HTML exported from **Dynamics 365 Customer Insights - Journeys** and returning the complete HTML to paste back into the same form.

**Release: 1.1.0 — Alpha, locally checked.** The regression fixtures and local preview are not proof of acceptance or submission processing in a Dynamics tenant.

## User workflow

1. Create and configure your form in Dynamics, including fields, validation, consent, and CAPTCHA.
2. Copy the complete HTML from its HTML editor and supply it to the skill with your desired appearance.
3. The skill preserves the original and restyles its existing div-based form, then compares the result against your export and checks the rendered appearance.
4. Receive the full styled HTML and paste it into the same Dynamics form. Keep your original as a backup.
5. Save, run **Check content**, inspect the saved HTML and published result, and verify a real test submission.

The skill keeps its existing invocation name, `$d365-customer-insights-forms`. It now focuses on this styling workflow. New field definitions, Form Capture, embedding integrations, and changes to business logic are outside the default scope.

## What is preserved

The supplied form owns its fields and behavior: generated IDs/classes, mapped and unmapped controls, target metadata, label associations, required/validation settings, choices/defaults, hidden values, consent, CAPTCHA, original stylesheets, and scripts. New styling uses scoped CSS and div containers. Table-based form layouts require re-exporting from Dynamics with its table-less layout enabled.

The source-comparison checker detects changed functional attributes/ownership, added or removed controls, duplicate field blocks, layout tables, changed scripts, and edited or reordered original stylesheets. It flags common unscoped new CSS. Existing source issues are reported separately from styling regressions. Browser checks must still verify geometry, cascade, accessibility, and validation presentation.

## Repository structure

```text
SKILL.md                       Active workflow and constraints
agents/openai.yaml             Discovery/UI metadata
references/
  html-contract.md             Preserve generated HTML and behavior
  styling.md                   Scoped CSS, fonts, mobile, accessibility
  validation-and-handoff.md    Comparison and Dynamics acceptance
  javascript.md                Optional, requested script investigation
scripts/
  validate_form.py             Native preflight and source comparison
  build-site.mjs               Existing preview-site build
tests/test_validate_form.py    Structural/preservation regressions
examples/
  preview.html                 Separate local submission-safe harness
  restyle/original.html        Sanitized baseline fixture
  restyle/styled.html          Same contract with scoped styling
docs/background/               Former broad reference material
docs/archive/                  Historical examples and old demo
```

Only the four focused references are routed by the active skill. Background material and archival examples remain for maintainers; they are not instructions or deployment templates. Root README/changelog/build metadata serve repository maintenance and preview hosting.

## Local verification

```bash
python3 -m unittest -q tests/test_validate_form.py
python3 scripts/validate_form.py examples/restyle/styled.html --mode native --original examples/restyle/original.html --json
npm run build
python3 -m http.server 8000 --bind 127.0.0.1
```

Open [the local preview](http://127.0.0.1:8000/examples/preview.html) after starting the server. The preview contains both examples in separate frames and intercepts demo submissions in its parent page. The fixture HTML has no simulated-success or submission-interception script.

The paired fixtures cover mapped/unmapped text, email, phone, textarea, select, radio, multi-select, number, date, hidden values, and consent. They use synthetic IDs and consent configuration derived from inspected markup conventions; they are not current tenant exports or usable production templates. They intentionally omit operational CAPTCHA, which is reported as an existing source warning. The styled sample demonstrates mobile overrides for generated fixed inline widths and loads the project's Manrope font from Google, with system/generic fallbacks.

The preview build continues to serve `/`, `/index.html`, and the legacy `/test.html` route, plus the two example documents. Building does not deploy or change existing hosting configuration.

The `--original` JSON report has introduced findings in `findings`/`summary`, original preflight results in `original_findings`, and remaining original issues in `source_findings`/`source_summary`. Exit status is nonzero for introduced or remaining source errors; `--strict` also fails on warnings. The older preflight `--mode capture` API remains available for compatibility, but is not used by this skill's styling workflow.

## Proof boundaries

Local comparison cannot validate Dataverse schema, matching rules, compliance relationships, bot protection, external-hosting permissions, HTML sanitization, or actual submission processing. It does not interpret JavaScript or prove that CSS preserves all runtime behavior. Keep the original generated markup and test the result after Dynamics saves and publishes it.

Report local checks, platform acceptance, published rendering, and submission verification separately. Saving changes to an already live form republishes it; use a copy/non-production form for acceptance testing where possible.

Sources: [form customization and validation](https://learn.microsoft.com/en-us/dynamics365/customer-insights/journeys/real-time-marketing-manage-forms), [div layouts and troubleshooting](https://learn.microsoft.com/en-us/troubleshoot/dynamics-365/customer-insights/journeys/forms/troubleshooting-forms), [unmapped fields](https://learn.microsoft.com/en-us/dynamics365/customer-insights/journeys/real-time-marketing-forms-custom-fields).
