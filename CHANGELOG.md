# Changelog

All material changes to the D365 Customer Insights - Journeys Forms skill should be recorded here. Keep entries concise and describe changes that affect how the skill is discovered, used, or maintained.

## [Unreleased]

Add material changes here before the next version is released.

## [1.1.0] - 2026-09-30

### Changed

- Focused skill discovery and instructions on restyling a user's native Dynamics export and returning complete HTML for the same form.
- Consolidated the active documentation into HTML contract, styling, validation/handoff, and optional JavaScript references; preserved the former references under `docs/background/`.
- Archived historical examples and the simulated-submission smoke form, and replaced active examples with paired sanitized regression fixtures plus a separate preview harness.
- Updated the preview build for the new paths while preserving its existing root, index, and legacy test routes. Hosting configuration remains unchanged; no deployment is implied.

### Added

- Added `--original` comparison to protect functional nodes/attributes, field ownership, generated classes, options/defaults, scripts/order, original stylesheets, and doctype.
- Added separate source and introduced-finding reports, div/table layout checks, duplicate-field checks, unmanaged-control rejection, and conservative new-CSS scope warnings.
- Added preservation regression tests and a responsive styled fixture covering common mapped/unmapped controls and consent. Fixtures remain non-deployable and local checks do not establish tenant acceptance.

## Earlier unreleased changes

The following entries predate the styling-only refactor and describe the archived workflow and fixtures.

### Added

- Added published-layout width guidance covering Dynamics-generated inline `width` and `flex-basis` values, padded outer wrappers, section expansion, and computed-geometry verification.
- Added required spacing guidance for sections, containers, columns, field blocks, and basic form field defaults.
- Added explicit native-create, native-rebuild, standard-embed, and Form Capture workflows grounded in current Microsoft Learn guidance.
- Added compatibility evidence levels and a dependency-free local preflight checker with native-form and Form Capture tests.

### Changed

- Updated the basic `test.html` smoke test to budget for the `600px` inner Dynamics layout width.
- Updated the README to document standalone-versus-published rendering differences and the new width verification expectations.
- Updated `test.html` to use a white background, valid last-name markup, and required last-name/email fields.
- Reclassified the fixed template shell, 600px layout, spacing, and last-name/email rules as repository fixture conventions rather than universal Customer Insights requirements.
- Clarified that archival examples contain non-reusable consent placeholders, environment identifiers, and obsolete HIP CAPTCHA styles.
- Updated lifecycle-event, JavaScript placement, external-hosting, reCAPTCHA, table-less layout, and submission-verification guidance against Microsoft Learn MCP and current Microsoft troubleshooting documentation.

## [1.0.1] - 2026-08-20

### Added

- Added form-prefill, unmapped-field, and submitted-value guidance focused on generated form markup and form integrations, excluding CRM schema and role setup.
- Added public-form security and operations guidance covering reCAPTCHA, HIP captcha removal, client-side security boundaries, tracking privacy, service-protection limits, and `429` throttling.
- Added Dynamics form-editor instructions for uploading custom fonts and applying them through Theme text styles.

### Changed

- Updated README scope and official-source links for the new references.
- Clarified that Manrope is a project font choice rather than a universal Dynamics platform requirement, while retaining the existing fallback and testing guidance.

## [1.0.0] - 2026-08-20

Initial v1 baseline for the Dynamics 365 Customer Insights - Journeys Forms skill.

### Added

- Focused references for form structure, form management, Designer attributes, custom fonts, Designer elements, embedding, JavaScript, and submission feedback.
- Sanitized Lead and Contact form examples plus an experimental design-system stylesheet.
- Required Manrope font guidance with system and generic fallbacks.

### Changed

- Scoped the Designer element inventory to form-relevant blocks and added Consent and Topic blocks.
- Added routing for all references from `SKILL.md` and renamed generic references to `form-management.md` and `form-structure.md`.
- Updated the branded example and design-system stylesheet to use Manrope.
- Added guidance to preserve generated form metadata, structure, validation, consent settings, and environment-specific values.

### Notes

- Release stage remains Alpha / pre-development; platform behavior, APIs, generated markup, and selectors may change.
- The original default form exports remain comparison baselines.
