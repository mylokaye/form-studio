# Manage forms

Use this reference for form settings, field constraints, validation, consent behavior, and publishing workflow. For current product behavior, verify the [Microsoft Learn guidance for managing Customer Insights - Journeys forms](https://learn.microsoft.com/en-us/dynamics365/customer-insights/journeys/real-time-marketing-manage-forms).

## Publishing and cache behavior

- Saving changes to a live form republishes the form.
- Published form content is served through a CDN and may take several minutes to refresh.
- For testing, append `#d365mkt-nocache` to the page URL to bypass the CDN cache. Do not share that cache-bypass URL with customers.
- Unpublishing removes the form from the CDN, although browser caches may still display stale content.
- For an external embed, add the exact host to allowed domains and enable external form hosting. Completing email-domain authentication is not required solely for form hosting or prefill.

Test both the Designer result and the published form after changes. Use a non-production form for structural, CSS, JavaScript, consent, and submission tests.

## Form settings

Use built-in settings before custom code where they meet the requirement:

- **Audience** controls whether the form targets leads, contacts, or a combined Lead & Contact audience. Field availability, matching rules, and mappings depend on this selection; event registration forms target Contact.
- **Prefill** fills known values into supported fields. Read-only fields can display a value without allowing edits; validation is skipped for read-only fields.
- **Web tracking** may add a tracking cookie through the form loader. Treat this as a privacy and consent decision, not merely a technical toggle.
- **Post submission action** controls the built-in thank-you notification or redirect. Use it instead of custom JavaScript for standard success behavior.
- **Error notification** and built-in submission feedback cover standard success and failure states. Use `data-preventsubmissionui="true"` only when a custom UI is intentionally implemented and tested.
- **Duplicate records** and matching rules determine whether a submission updates or creates a lead or contact. Do not assume the lead and contact defaults are identical.
- **Ignore opt-outs**, purposes, and topics affect consent capture. Review the compliance profile, channels, and checked/unchecked behavior together.

For custom success, error, redirect, or loading UI, read [Styling and submission feedback](styling-and-submission-feedback.md) and verify the current client API behavior.

## Fields and validation

Field rendering is determined by the Dataverse field type and format. Common controls include:

| Dataverse type or format | Common control |
| --- | --- |
| Single-line text, email, URL, or number | Text input with format-specific validation |
| Phone | Phone input, optionally with a preset country/region code |
| Multiple lines of text | Text area |
| Option set | Drop-down or radio buttons |
| Two options | Checkbox or radio buttons |
| Date and time | Date or date-time picker |
| Lookup | Lookup control |

The source guidance states that File and Customer fields are not supported in forms, and that a single field value is limited to 4000 characters. Confirm current limits before designing around them.

Use the Designer's required and validation settings before writing custom validation. If a custom regular expression is needed, test native browser validation, error messaging, keyboard use, and the server-side submission path.

Before publishing, check the Microsoft-documented conditions that block validation:

- a Submit button is present;
- every mapped field is linked to an editable attribute, while submission-only questions use supported unmapped fields added by the form editor;
- there are no duplicated fields;
- fields required by the matching rule are present;
- a target audience is selected.

The form must include every attribute used by the selected matching rule, and those fields should be required. Microsoft's default Contact example uses email, but the actual matching rule is authoritative. Target-table requirements can produce additional warnings, such as a required last name. Do not infer a universal required-field set from this repository's examples.

When a field is required, keep the Designer block's required metadata and the native control's `required` attribute consistent. Use the form editor to configure required state rather than changing only one marker in HTML.

Warnings can still indicate missing attributes required to create or update the target record. Treat warnings as part of the release review.

## Lookup fields

Lookup values can be exposed to anyone who can view the form. Do not place sensitive records in a public lookup. Verify the Marketing Services User Extensible role, entity/view permissions, and field-level security before shipping a lookup field.

Use unique display names when a lookup has a default value. If the current client API is needed to set or filter a lookup, read [Embed and client API](embed-and-client-api.md) and verify the supported signature before implementing it.

## Consent

- A form is associated with one compliance profile; purposes and topics in the form must be compatible with that profile.
- Review the channel, opt-in behavior, and **Ignore opt-outs** setting together. A user leaving a previously selected topic unchecked can otherwise create an unintended opt-out.
- Prefill can reduce accidental changes to existing consent choices, but it does not replace clear labels or an explicit consent review.
- Do not copy placeholder consent IDs, topic IDs, or compliance settings from an example form into a real deployment.

## HTML, CSS, and JavaScript changes

The form editor can rewrite or sanitize HTML when the form is saved. Current app versions support JavaScript in the `<body>` and move head scripts there; older versions had different placement behavior. Use `addEventListener`, because inline handlers such as `onclick` are removed, and verify that saved HTML still contains the intended script. Preserve generated Designer structure and use the specialized references:

- [Form structure](form-structure.md) for sections, containers, and blocks.
- [Custom attributes](custom-attributes.md) for Designer metadata and style settings.
- [Custom JavaScript](custom-javascript.md) for lifecycle events and scripts.
- [Styling and submission feedback](styling-and-submission-feedback.md) for CSS and submission states.
