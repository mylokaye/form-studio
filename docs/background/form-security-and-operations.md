# Form security and operations

Use this reference for public-form bot protection, form-side security boundaries, privacy-sensitive tracking behavior, and submission throughput. It intentionally excludes Dataverse schema, role, environment, and CRM administration procedures.

Official references: [Forms security and privacy](https://learn.microsoft.com/en-us/dynamics365/customer-insights/journeys/real-time-marketing-form-security-privacy), [default form configuration](https://learn.microsoft.com/en-us/dynamics365/customer-insights/journeys/real-time-marketing-form-global-settings), and [custom submission validation](https://learn.microsoft.com/en-us/dynamics365/customer-insights/journeys/real-time-marketing-form-customize-submission-validation).

## Protect public forms from bots

Use the form editor's **reCAPTCHA** element on publicly accessible marketing and event registration forms. Add it through the **Elements** panel and preserve the generated Designer block. Do not replace it with an undocumented HTML element or rely on client-side JavaScript alone.

The Site key and Secret key are configured in the default form configuration by an administrator. The Secret key must never appear in form HTML, browser JavaScript, a query string, or a hidden field. If a custom CAPTCHA or business rule requires authoritative validation, perform that validation on the backend and return a form-validation result to the platform.

The former HIP captcha was removed from Customer Insights - Journeys in June 2026. Existing forms can continue to submit, but an older form has no bot protection after HIP removal unless reCAPTCHA is added and the form is republished. Test the published form after replacing an older CAPTCHA block.

## Hosting and security boundaries

- Form submissions are accepted only from domains added to the allowed-domain list with external form hosting enabled. This also applies to form capture. Full email-domain authentication is a separate feature and is not required merely for forms or prefill. A client-side workaround cannot bypass the form-hosting check.
- Treat every public form field, including hidden and unmapped fields, as attacker-controlled input.
- Do not put API keys, CAPTCHA secrets, internal record identifiers, or authorization decisions in client-side form code.
- Keep custom validation narrow and server-backed when it depends on existing records, rate limits, or protected business rules.

## Service protection and 429 responses

Form traffic is governed by Dataverse service-protection limits rather than a guaranteed submissions-per-minute quota. The raw form guidance records a default baseline of 6,000 API requests in a five-minute sliding window per user and web server; treat this as an operational reference, not a capacity guarantee, and verify current platform limits before load planning.

Form-related work that can consume API capacity includes:

- retrieving lookup options, generally one request per lookup field;
- CAPTCHA validation; and
- form submission.

Cached form HTML does not count as a form-render API call. The effective submission rate varies with concurrency, request duration, lookup count, CAPTCHA configuration, and other environment traffic. Handle `429 Too Many Requests` as throttling: show a recoverable error to the user and avoid automatic submission loops or duplicate retries.

## Tracking and cookies

Marketing and event registration forms do not set tracking cookies by default. Enabling **Web tracking** adds tracking behavior and cookies through the form loader, so treat that setting as a consent and privacy decision. Do not enable it merely to make ordinary form submission work.

Test bot protection, rejected submissions, throttling, consent behavior, and published-form behavior in a non-production form. Verify both the browser-visible result and the recorded submission state.
