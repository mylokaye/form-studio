# Validate and return the complete HTML

## Local checks

Run source preflight once, then compare the finished result to that untouched source:

```bash
python3 scripts/validate_form.py original.html --mode native
python3 scripts/validate_form.py styled.html --mode native --original original.html --json
```

Resolve the script path relative to the skill's `SKILL.md`. Do not overwrite `original.html`. The comparison is required for the styling workflow; a standalone preflight cannot detect a field removed from the original.

The JSON report separates:

- `original_findings`: issues found before styling;
- `source_findings` / `source_summary`: original issues still present in the output;
- `findings` / `summary`: introduced preflight issues and preservation failures.

Exit status is nonzero for introduced or remaining source errors. `--strict` also fails on warnings, including existing warnings. Review source warnings without treating them as styling regressions. Do not label an output ready for publishing while blocking source issues remain.

Comparison protects nonvisual attributes and ownership of functional nodes, generated classes, label/choice text, options and defaults, scripts/order, original styles, and the doctype. It allows additional styling classes, inline visual values, scoped override styles, and ordinary decorative wrappers without functional metadata. Reordering intact field blocks can pass; moving a control between blocks does not. Check keyboard order after any visual rearrangement.

The checker is a conservative DOM/attribute preflight. It is not a browser HTML conformance validator, full CSS parser, Dataverse schema validator, JavaScript runtime test, or CAPTCHA/service test. Its CSS warnings catch common unscoped selectors; inspect complex CSS manually. CSS can affect behavior without changing an attribute, so browser checks remain necessary.

Render desktop, 375px, and 320px widths. Inspect overflow, each control's bounds, label wrapping, font loading/fallback, consent text, focus, native required/format validation, and 200% zoom. Verify unrelated host content keeps its styles. Use synthetic data. Do not send real submissions from a local fixture or unknown production form.

Any local submit interception belongs in a separate preview harness. The paste-back document must retain its Dynamics-managed submission path and original scripts. Never show simulated success in that document.

## Deliverables and paste-back

Return the full `styled.html`, a rendered preview when available, and a concise report of styling changes, preservation results, existing issues, and remaining platform checks. Do not return only CSS, an embed code, or a repository template.

Tell the user to:

1. Keep a backup of their original HTML and use a copy/non-production form for acceptance testing where possible. Saving edits to an already live form republishes it.
2. Open the same form's HTML editor and replace its HTML with the complete styled document.
3. Save, run **Check content**, resolve blocking issues, and inspect the Designer result.
4. Copy the saved HTML back for comparison against the original. Investigate changed functional metadata/scripts; Dynamics can rewrite formatting, wrappers, and script placement, so comparison failures require inspection rather than automatic repair.
5. Publish and check the intended standalone/embed route, mobile geometry, validation, CAPTCHA, and feedback.
6. Submit a uniquely identifiable test record. Confirm the submission reaches **Success**, values are correct, the expected Contact/Lead or event registration is processed, and consent is correct when present.

If direct environment access is unavailable, provide these steps and report that platform/submission checks remain unverified; do not block a completed local styling handoff on access the user has not supplied.

## Evidence wording

| Level | Evidence required |
| --- | --- |
| Candidate | Styled HTML exists; local checks incomplete or blocking source issues remain |
| Locally checked | Preservation/preflight and relevant rendered checks pass; source warnings disclosed |
| Platform accepted | The target form saves and **Check content** has no blocking errors |
| Published | The current version renders correctly on the intended published route |
| Submission verified | The published test submission, resulting record, values, and applicable consent are confirmed |

Published content can take up to 10 minutes to refresh. Use `#d365mkt-nocache` only on a test URL to inspect a newly saved version; do not distribute cache-bypass URLs. External hosting must already be allowed for the intended domain. Preserve the user's hosting configuration; styling does not change it.

Sources: [save, validation, submission processing, and cache behavior](https://learn.microsoft.com/en-us/dynamics365/customer-insights/journeys/real-time-marketing-manage-forms), [published form troubleshooting](https://learn.microsoft.com/en-us/troubleshoot/dynamics-365/customer-insights/journeys/forms/troubleshooting-forms).
