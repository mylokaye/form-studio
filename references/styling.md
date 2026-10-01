# Recreate the requested appearance

Use the original export as the working document. Derive colors, typography, spacing, borders, radii, control styles, focus treatment, and responsive behavior from the user's reference. Choose sensible details when the reference does not specify them. Keep text, fields, and behavior intact.

## Scope and cascade

Keep the generated styles unchanged. Add one override `<style data-form-styling="true">` after the existing style elements, with every selector arm rooted at `form.marketingForm` or `.marketingForm`. Add a styling class to the form when a more specific target is useful.

Define custom properties on the form, not `:root`. Avoid new `body`, bare control, and global `*` rules. Scope resets, pseudo-elements, responsive rules, and focus states too. Verify the new styles against unrelated headings and controls on an embedded host page.

```css
form.marketingForm.d365-styled {
  --form-accent: #174ea6;
  --form-border: #c4cfdd;
  font-family: "Manrope", system-ui, sans-serif;
}

form.marketingForm.d365-styled input,
form.marketingForm.d365-styled select,
form.marketingForm.d365-styled textarea,
form.marketingForm.d365-styled button {
  font-family: inherit;
}
```

The colors are illustrative. Do not force them onto a different requested design. Use `!important` narrowly when an observed generated rule or inline visual value requires it; verify the computed result. Keep the original block and its controls instead of replacing them with custom controls.

## Shared spacing

Inline [assets/form-spacing.css](../assets/form-spacing.css) into the new override style, after its font import and other visual rules. Add the `d365-styled` form class. This is the skill's default spacing design, not a Dynamics platform requirement. Keep the asset's defaults for every output unless the user supplies a different spacing reference; override its form-scoped tokens after the preset when needed.

| Relationship | Default |
| --- | --- |
| Label to control | 8px |
| Field block to next field | 24px |
| Desktop columns | 24px |
| Radio/checkbox choices | 10px |
| Consent blocks | 12px |

Dynamics can wrap a saved row's columns in `.innerSection`, inside `[data-section="true"]`. A gap on the outer section alone then has no effect between the columns. The preset covers both row shapes and stacks both at its mobile breakpoint. Verify the **actual control edges** have the intended gap, rather than checking only that a CSS `column-gap` property exists.

Budget the gap within the available row width. Override generated fixed visual widths/flex bases when necessary without changing metadata. Preserve unequal column proportions: derive flex weights from `data-container-width` (or the inspected source) and set styling custom properties, rather than making every column equal. The preset deliberately does not choose desktop widths, proportions, colors or card dimensions. Adapt its breakpoint if the source's column count or geometry needs earlier stacking. Keep hidden blocks hidden; their margins must not create visible gaps.

## Responsive geometry

Generated container percentages can become fixed inline `width` and `flex-basis` values. Inspect the layout, section, container, and control widths before deciding how to style a card or columns. The repository's historical 600px layout is not a platform constant.

- Budget card borders/padding outside the actual layout width, or use narrowly scoped responsive overrides that keep content within the available width.
- Retain generated IDs and layout metadata. At a narrow breakpoint, a scoped rule can stack the existing div columns and override fixed inline visual widths/flex bases without changing field ownership. Derive the breakpoint from the reference and actual geometry.
- Test at a desktop width, 375px, and 320px. Check every visible control's edges and `document.documentElement.scrollWidth <= document.documentElement.clientWidth`.
- Check computed control font sizes at mobile widths. A more specific generated or base selector can defeat a later media rule; verify that the intended override actually applies.
- Verify after Dynamics saves and publishes, since it can materialize different inline values. A passing local export is only local evidence.

Do not hide overflow to mask an oversized form. Do not clip or hide required controls. Prefer readable labels above controls; use floating labels only when empty, populated, focused, autofilled, validation, zoom, and mobile states have been checked.

## Fonts and assets

Keep Manrope as the primary font when it is a project requirement; use the requested brand font for other styling work. Use system and generic fallbacks. For a font import, place `@import` first in the new override style element, before its other rules. Preserve the original style elements.

Google-hosted fonts send requests from the visitor's browser to Google. Use an approved hosted/uploaded font when external loading is unsuitable. Dynamics Theme font upload is an available user-side option; do not invent font URLs or embed private assets into shared examples. Verify font loading and readability when it fails. Apply fonts to labels, controls, consent, and existing validation/feedback regions as needed.

## Accessibility and submission states

Keep native controls and their labels, fieldsets/legends, required markers, and accessible naming. Preserve visible keyboard focus, adequate contrast, long-label wrapping, and usable targets. Test native validation and 200% zoom. Do not remove outlines without an equally visible replacement.

Restyle existing loading/error/success regions only when their ownership and published markup have been inspected. Preserve their messages, live regions, behavior, and redirects. Feedback inserted outside the form root may require a separately verified wrapper scope; do not add global selectors or suppress the default submission UI as part of ordinary styling.

Sources: [form Theme and CSS customization](https://learn.microsoft.com/en-us/dynamics365/customer-insights/journeys/real-time-marketing-manage-forms), [custom fonts](https://learn.microsoft.com/en-us/dynamics365/customer-insights/journeys/use-custom-fonts).
