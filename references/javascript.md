# Existing JavaScript and requested enhancements

Ordinary restyling preserves the user's scripts, their attributes, resource URLs, and execution order. Do not add JavaScript for basic typography, layout, focus, or native controls. The default source comparison rejects script changes.

Read this only when an existing script needs investigation or the user explicitly requests a behavior change. Treat that change as an extension with its own acceptance tests, not as a silent exception to preservation. Report intentional script changes and resulting comparison failures clearly; do not weaken the checker to make them disappear.

- Current Dynamics versions support body scripts and can move head scripts into the body on save. Verify the saved source and the target app's current behavior.
- Inline event attributes such as `onclick` and `onchange` are sanitized. Use `addEventListener` for an explicitly requested extension.
- Dynamically loaded forms need documented form-loader lifecycle events; `DOMContentLoaded` alone can run too early. Scope initialization to the actual rendered form and avoid repeated listeners.
- Preserve submission ownership, validation, and existing redirects. Do not add `preventDefault()` or a custom success handler during ordinary styling.
- Native loader and Form Capture APIs are separate. A capture/embedding integration is outside this skill's restyling workflow.
- Verify the actual success event payload before success-dependent code. Historical Microsoft examples have used inconsistent success-property names; do not copy a fallback without target testing.
- Never log form values, tokens, or personal information. Keep authorization and secrets out of browser code.

Use current Microsoft Learn MCP search/fetch for the relevant API before writing an extension, or official Microsoft documentation if the connector is unavailable. Then test load timing, repeated initialization, rejection, validation, and actual submission processing as appropriate.

Sources: [JavaScript customization](https://learn.microsoft.com/en-us/dynamics365/customer-insights/journeys/real-time-marketing-manage-forms#advanced-form-customization), [form-loader API](https://learn.microsoft.com/en-us/dynamics365/customer-insights/journeys/developer/realtime-marketing-form-client-side-extensibility).
