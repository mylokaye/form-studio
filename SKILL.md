---
name: d365-customer-insights-forms
description: Restyle native Dynamics 365 Customer Insights - Journeys form HTML supplied by the user, preserving fields, mappings, validation, consent, and submission behavior. Use when a user copies an existing form's HTML from Dynamics and wants styled HTML to paste back into the same form.
---

# Style an exported Dynamics form

The user creates and configures the form in Dynamics, copies its HTML here, receives styled HTML, and pastes it back into the same form. Use the supplied export as the functional source of truth.

## Inputs and scope

- Obtain the complete, untouched native form HTML and the requested appearance: a screenshot, reference design, brand guidelines, or a description. Resolve ordinary visual choices from the reference and supplied form.
- For a test without a design reference, state a reasonable visual default and proceed. Describe the result as a styled candidate, not an exact design recreation.
- If native HTML is missing, request it before producing paste-back code. A screenshot or embed snippet does not contain the form's complete field contract.
- Use **div containers**, not table-based form layouts. If the export uses layout tables, ask the user to enable **Settings > Feature switches > Forms > Enable table-less layouts in Form editor**, save the form, and copy its HTML again. Do not rebuild mapped controls or convert a legacy layout by guessing metadata.
- Style the existing form. Adding fields, changing validation or consent, and changing submission logic are separate tasks that require an explicit request and appropriate Dynamics validation.
- Repository examples are sanitized test fixtures, not templates for the user's environment. Never replace the supplied HTML with an example or copy example IDs, mappings, or consent configuration into it.

## Styling workflow

1. Save the supplied HTML unchanged as `original.html`. Read [the HTML contract](references/html-contract.md) and run source preflight:

   ```bash
   python3 scripts/validate_form.py original.html --mode native
   ```

   Report existing source problems separately. Do not silently repair fields, consent, CAPTCHA, or scripts while styling. Existing warnings, such as a missing CAPTCHA block, do not authorize adding a fabricated block.

   Continue useful local styling when source errors can be preserved safely. Mark the output as a candidate with unresolved source findings; never claim it is ready for publishing. Known Designer choice-group headings can generate accessibility warnings without meaning that individual controls are missing.

2. Identify the requested colors, typography, borders, control treatment, and desktop/mobile behavior. Use the shared [Form Studio spacing preset](assets/form-spacing.css) for consistent output unless the user requests different spacing. Keep the original content and functional markup. Read [styling guidance](references/styling.md).
3. Preserve the source envelope, generated CSS, div hierarchy, IDs, metadata, controls, choices, validation, consent, hidden/default values, and scripts. Add styling classes and one scoped override `<style>` after the original styles. Keep the normal Dynamics submission path. Do not add demo submit handlers or simulated success messages.
4. Save the complete result as `styled.html`, then compare it against the untouched export:

   ```bash
   python3 scripts/validate_form.py styled.html --mode native --original original.html --json
   ```

   Resolve introduced errors and review introduced warnings. The checker distinguishes existing source findings from changes introduced by styling; it does not prove Dataverse configuration or runtime behavior.
5. Render the result at desktop and mobile widths. Check measured column/field/label gaps, overflow, control geometry, label readability, native validation, keyboard focus, zoom, and that the new CSS does not affect surrounding content. Include saved `.innerSection` wrappers in spacing checks. Put any local submission interception in a separate preview harness, never in `styled.html`.
6. Deliver the full `styled.html`, the preview when available, a brief preservation/check report, and [paste-back instructions](references/validation-and-handoff.md). Do not substitute an embed snippet, partial CSS, or a preview-only document for the complete HTML.

Resolve script paths relative to this `SKILL.md`; the example commands assume the skill directory is the current directory. Keep generated artifacts in the user's workspace, outside this installed skill unless explicitly requested.

## Preservation and evidence

- Preserve every nonvisual source attribute, including unfamiliar future Dynamics metadata. Keep original classes as runtime/CSS hooks and add new classes for styling. Keep input names, IDs, label associations, target audiences/properties, choice values/order/defaults, required markers, validation rules, consent configuration, scripts, and script order.
- Preserve generated layout metadata and inline values. Narrowly scoped responsive CSS can override visual sizing at a breakpoint when needed; it must be checked against the actual generated geometry and again after Dynamics saves/publishes. Do not adopt one fixed width or spacing pattern as a platform rule.
- Preserve existing unmapped fields and event-specific regions. A field's appearance or `data-*` attributes do not prove its mapping; the supplied export and target environment remain authoritative.
- Preserve existing CAPTCHA and post-submit behavior. If protection or validation appears broken in the source, report it for correction in Dynamics instead of fabricating configuration.
- Report **locally checked** only after comparison and relevant browser checks. Report **platform accepted** only after the target form saves and **Check content** passes. Report **submission verified** only after a published test submission and its expected record, submitted values, and consent state are confirmed.
- Treat form values, prefill tokens, and private asset URLs as sensitive. Use synthetic values for previews/tests and keep secrets out of HTML and scripts.

For a platform-specific uncertainty, use Microsoft Learn MCP search and fetch the relevant current page. If unavailable, use official Microsoft documentation. Do not make ordinary styling depend on fetching the whole documentation set.

## Focused references

- [HTML contract](references/html-contract.md): inspect the source and preserve its generated structure and behavior.
- [Styling](references/styling.md): design recreation, scoped CSS, fonts, responsive geometry, and accessibility.
- [Validation and handoff](references/validation-and-handoff.md): source comparison, browser checks, paste-back, and evidence boundaries.
- [JavaScript](references/javascript.md): read only when existing scripts need investigation or the user explicitly requests behavior changes.
