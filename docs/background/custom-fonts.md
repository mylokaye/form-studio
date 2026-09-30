# Custom fonts

Use this reference when applying a custom font, including Manrope, to a Customer Insights - Journeys form. Dynamics supports inheriting the host page's font for embedded forms and uploading a custom font through the form Theme for standalone pages. If Manrope is a project requirement, keep it as the primary font; it is not a universal platform requirement.

For current product behavior, verify the [Microsoft Learn guidance on custom fonts](https://learn.microsoft.com/en-us/dynamics365/customer-insights/journeys/use-custom-fonts).

## Upload a custom font in Dynamics

For a standalone form, upload the font through the form editor so Dynamics can use it in the generated Theme styles:

1. Open the form in Customer Insights - Journeys and select **Edit**.
2. Select the brush icon to open **Theme**.
3. Open the **Custom fonts** section and choose the option to browse the font library or upload font files.
4. Select the licensed font file from your computer. Prefer a web-compatible `.woff2` or `.woff` file when the upload flow supports those formats.
5. Save the form and publish it. If the form was already published, allow for CDN refresh before checking the public page.

Use only fonts whose license permits web use and hosting in Dynamics. Uploading a font does not make it a safe substitute for testing; check fallback behavior, readability, and loading on the published form.

## Apply the uploaded font to the form

After the upload, select the uploaded font in the Theme **Text styles** definitions that should use it. Apply it consistently to headings, paragraphs, labels, inputs, buttons, links, consent text, and validation messages as needed. The Theme route is preferred because Dynamics can preserve the generated font configuration when the form is saved.

For an externally embedded form where the host page already owns typography, set the form's font to `inherit` in the supported Theme controls instead of uploading a second font. Do not assume that a font uploaded for a standalone page is automatically available to arbitrary external CSS.

## Embed Manrope in the form

Add the font import at the beginning of the form's existing `<style>` block. Keep it before the other CSS rules. If the form editor removes external font imports, use an approved self-hosted font URL or the platform-supported font configuration instead.

```css
@import url("https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&display=swap");
```

This URL-import approach is separate from the Dynamics font-library upload. Use it only when external font loading is permitted and the form editor preserves the import; otherwise use the uploaded font through Theme or an approved self-hosted implementation.

Loading a Google-hosted font sends a request to Google from the visitor's browser. Confirm that this is acceptable for the form's privacy, security, licensing, and availability requirements before publishing. If it is not, self-host the required Manrope font using an approved source; do not substitute a different primary font.

## Apply the font to the complete form

Place these rules after the Dynamics stylesheet and any generated form styles. The form root establishes the stack; descendants, pseudo-elements, and native controls inherit the font family.

```css
form.marketingForm {
  font-family: "Manrope", system-ui, sans-serif !important;
}

form.marketingForm *,
form.marketingForm *::before,
form.marketingForm *::after {
  font-family: inherit !important;
}
```

The fallback order is:

1. `Manrope`, when the embedded font loads.
2. `system-ui`, using the visitor's operating-system interface font.
3. `sans-serif`, as the generic browser fallback.

Do not replace the generated form layout selectors or use broad global selectors such as `*` outside `.marketingForm`.

## Reuse and testing rules

- Keep the `@import` at the top of the existing `<style>` block; do not create a competing stylesheet or duplicate the import.
- Keep Manrope as the primary font when self-hosting; only the system and generic fonts may act as fallbacks.
- Preserve the Dynamics stylesheet and generated inline layout values. Typography changes should not change section or container sizing unexpectedly.
- Test labels, inputs, select menus, buttons, validation messages, consent text, focus indicators, zoom, and narrow mobile widths.
- Confirm the form remains legible when Manrope is unavailable and that the system and generic fallbacks have sufficient contrast and readable metrics.
