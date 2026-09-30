# Custom JavaScript

Official references: [manage forms](https://learn.microsoft.com/dynamics365/customer-insights/journeys/real-time-marketing-manage-forms#add-custom-javascript-to-your-form), [client-side extensibility](https://learn.microsoft.com/dynamics365/customer-insights/journeys/developer/realtime-marketing-form-client-side-extensibility), and [form troubleshooting](https://learn.microsoft.com/dynamics365/customer-insights/journeys/real-time-marketing-troubleshooting-forms#the-form-editor-removes-custom-javascript-or-other-code-from-the-html-body).

## Add scripts safely

Use the form HTML editor only when a Designer option cannot meet the need: open the form editor and select the **HTML** (`</>`) control in the top toolbar. Current versions support JavaScript in the HTML `<body>` and move head scripts to the body when saving. Versions before `1.1.38813.80` had different placement behavior, so inspect the saved source when maintaining an older environment. The editor may remove unknown code and sanitizes inline event attributes such as `onclick` and `onchange`.

Attach behavior with `addEventListener` instead:

The example assumes the form markup is already present when `DOMContentLoaded` fires. For script-hosted or dynamically rendered forms, use the relevant rendered-form lifecycle event described below instead.

```js
document.addEventListener("DOMContentLoaded", () => {
  const button = document.querySelector(
    'form.marketingForm [data-editorblocktype="SubmitButton"] button[type="submit"]'
  );
  button?.addEventListener("click", () => {
    // Add narrowly scoped behavior.
  });
});
```

## Loader-hosted lifecycle events

The current dedicated client API documents:

- `d365mkt-beforeformload`;
- `d365mkt-formrender`;
- `d365mkt-afterformload`;
- cancelable `d365mkt-formsubmit`;
- `d365mkt-afterformsubmit`.

Do not substitute similarly named events from older examples. Microsoft currently documents the after-submit Boolean as `Success` in the property table but uses `event.detail.successful` in its sample. Treat this as a documentation inconsistency: check the current page and verify the actual target-environment payload before making success-dependent changes.

## Progressive field display

Use a rendered-form lifecycle event when the field belongs to a script-hosted marketing form; `DOMContentLoaded` alone may be too early. Scope selectors to the form and handle missing elements gracefully.

```js
document.addEventListener("d365mkt-afterformload", (event) => {
  const form = event.target.querySelector("form");
  const company = form?.querySelector('[name="company"]');
  const employeeCount = form?.querySelector(".employee-count-field");
  if (!company || !employeeCount) return;

  employeeCount.hidden = !company.value;
  company.addEventListener("change", () => {
    employeeCount.hidden = !company.value;
  });
});
```

Test all changes in a non-production form first, including validation errors, inaccessible-JavaScript fallback, keyboard interaction, and mobile rendering. Use Microsoft Learn MCP for current troubleshooting and form-capture guidance.
