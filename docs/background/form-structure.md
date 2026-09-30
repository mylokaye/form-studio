# Form structure

Use this reference when creating or reviewing the HTML structure of a native Customer Insights - Journeys form. It describes the common table-less hierarchy and Designer attributes; it is not a drop-in form template and does not prove a field mapping.

For deployable work, start with HTML stored by a form created in the target environment. Keep its generated IDs, field names, target properties, consent settings, validation attributes, inline layout values, and environment-specific metadata. The examples below are intentionally generic and omit settings that vary by form, audience, environment, and field type.

Preserve the current form's document envelope when editing source. Microsoft documents the `marketing-designer-content-editor-document` meta tag for enabling drag-and-drop features, but does not document this repository's XHTML doctype, template GUID, 600px setting, author link, or complete shell as a universal requirement. The repository examples use one observed envelope as a fixture; do not copy its template ID into another environment.

## Structural hierarchy

```text
document
└── form.marketingForm
    └── div[data-layout="true"]
        └── div[data-section="true"]
            └── div[data-container="true"]
                └── Designer block[data-editorblocktype]
```

- The `marketingForm` element is the form root and owns submission behavior.
- The layout wrapper contains one or more sections. It commonly carries `data-layout-version`, `data-layout-maxwidth`, and a `property-reference` to the Designer setting for the maximum width.
- A section represents a row or layout group. It contains one or more containers.
- A container represents a column. Its `data-container-width` values normally describe percentages across the section, such as two `50` containers or one `100` container. Keep the Designer-generated flex and width styles with the export.
- A block is a Designer-managed element inside a container. Its `data-editorblocktype` identifies the block type. A container may contain multiple blocks.

The published export may add wrappers, classes, notification regions, accessibility attributes, and other metadata. Those details are part of the form implementation and should not be removed merely because they are not shown in this conceptual model.

## Layout width ownership and overflow

In the repository's observed published form, `data-layout-maxwidth="600px"` is the inner width available to the Dynamics layout. The Designer materialized container percentages as fixed inline values such as `width: 300px; flex: 0 0 300px` for a `50` container and `width: 600px; flex: 0 0 600px` for a `100` container. Treat those numbers as a diagnostic example, not a platform constant. The `data-container-width` attribute is metadata and does not create corresponding CSS in an arbitrary standalone document.

This matters when a custom wrapper adds padding. In that observed case, a `600px` wrapper using `box-sizing: border-box`, `40px` horizontal padding, and `1px` borders left `518px` of content width. Generated `600px` sections and containers then extended beyond the wrapper even though their DOM nesting was correct. Fixed-width child containers can also make a section's grid item expand because its default `min-width` is `auto`.

For custom cards and responsive styles:

- Keep the generated layout as the width owner, or make the outer border-box wide enough for the layout width plus padding and borders.
- Do not infer structural nesting from a screenshot; inspect computed widths and right edges.
- Compare the layout wrapper, each section, each container, and each control in the published form. A child right edge must not exceed the intended parent right edge.
- Check `document.documentElement.scrollWidth` against `document.documentElement.clientWidth` for unintended horizontal overflow.
- Test the published form after Dynamics applies inline layout styles; a standalone preview without those styles is insufficient.

## Repository fixture spacing

The included examples use the following observed spacing. Preserve it when editing those fixtures or when the user requests the same design; do not present these values as Microsoft requirements for every form:

- `data-section="true"` sections use `display: flex`, `flex: 1 0 0%`, `margin: 0`, and `padding: 0`, with no visible border.
- Standard field/content containers use `padding: 10px`, `flex-direction: column`, `min-width: 5px`, `float: left`, `word-wrap: break-word`, and `word-break: break-word`. Full-width field containers retain the same `10px` padding.
- The outer form-fields layout uses a `16px` gap between sections; two-column rows use a `1rem` gap between columns.
- Field blocks use a `0.45rem` gap between labels and controls.
- Use `background: #fff` for the page/form background. Never emit an empty or invalid background declaration.

Derive container widths from the published layout width rather than copying sample values. A submit-button wrapper may retain its generated centered, no-padding container exception.

The repository's basic examples mark `lastname` and `emailaddress1` as required. For a real form, derive required fields from the selected matching rule, target table requirements, and the user's business requirements. Microsoft's standard Contact example uses email as the default matching field, but matching rules can change. When a field is required, keep the Designer block and native control markers consistent.

## Minimal structural shell

This is an annotated shape, not a complete form. Replace the illustrative container IDs and block settings with values from a target-environment form before using it. Ordinary inputs pasted into this structure do not become mapped fields.

```html
<form class="marketingForm" aria-label="Form name">
  <div
    data-layout="true"
    data-layout-version="v3"
    property-reference="data-layout-maxwidth:@layout-max-width"
    data-layout-maxwidth="600px"
  >
    <div class="wrap-section" data-section="true">
      <div
        class="columnContainer"
        data-container="true"
        data-container-width="100"
        id="containerGENERATED_ID"
      >
        <div data-editorblocktype="Text">
          <p>Introductory content</p>
        </div>
      </div>
    </div>

    <div class="wrap-section" data-section="true">
      <div
        class="columnContainer"
        data-container="true"
        data-container-width="50"
        id="containerGENERATED_ID_1"
      >
        <!-- A field block or other Designer block goes here. -->
      </div>
      <div
        class="columnContainer"
        data-container="true"
        data-container-width="50"
        id="containerGENERATED_ID_2"
      >
        <!-- The section's container widths add up to 100. -->
      </div>
    </div>
  </div>
</form>
```

Do not copy the placeholder IDs. The Designer generates container and control IDs, and other attributes may be required for a particular target audience, field, consent record, or validation rule.

## Common block shapes

### Text

Text blocks are Designer-managed content. Use the Designer to change their content where possible.

```html
<div data-editorblocktype="Text">
  <p>Text</p>
</div>
```

### Submit button

The submit button belongs inside a container and must remain a submit control. The exact wrapper classes and accessibility attributes should come from the published form.

```html
<div data-editorblocktype="SubmitButton" class="submitButtonWrapper">
  <button class="submitButton" type="submit" aria-label="Submit">
    <span>Submit</span>
  </button>
</div>
```

### Field

Field blocks contain the label and native control generated for the selected Dataverse field. The block type and its settings vary by field type (`TextFormField`, `PhoneFormField`, `OptionSetFormField`, `TextAreaFormField`, and others).

```html
<div
  class="textFormFieldBlock"
  data-editorblocktype="TextFormField"
  data-targetproperty="firstname"
  data-targetaudience="lead"
  data-prefill="false"
>
  <label for="firstname-GENERATED_ID" title="First Name">First name</label>
  <input
    id="firstname-GENERATED_ID"
    type="text"
    name="firstname"
    title="First Name"
  >
</div>
```

Preserve the generated `name`, `id`, `for`, `data-targetproperty`, `data-targetaudience`, `data-required`, `data-prefill`, validation attributes, and field-specific child markup. Do not replace a generated field with a hand-authored input unless the task explicitly requires a supported custom field approach.

## Optional regions

Some forms contain additional Designer-managed or runtime regions, for example:

- event registration notifications such as `eventNotStarted` or `eventAtCapacity`;
- consent, topic, subscription-list, CAPTCHA, reset-button, lookup, or hidden-field blocks;
- confirmation, error, and submission-feedback containers.

These are not required in every form. Preserve them when they exist, and do not add event-specific regions to an ordinary lead or contact form without confirming that the form supports them.

## Editing and reuse rules

1. Use the Designer for adding, removing, reordering, or configuring mapped fields, unmapped fields, consent, reCAPTCHA, and Submit. Treat content inside a `data-editorblocktype` element as Designer-managed.
2. Use the published form export as the source of truth for exact markup. Do not invent IDs, service metadata, field mappings, consent identifiers, or undocumented block types.
3. Keep custom CSS and JavaScript outside the structural responsibility of sections and containers. A visual override should not take ownership of their flex layout, widths, `flex-basis`, `min-width`, or generated metadata.
4. Scope custom selectors to the form and attach behavior with event listeners. Do not rely on a block's generated ID as a durable CSS or JavaScript hook.
5. After structural changes, test the Designer preview and the published form, including responsive layout, native validation, submission feedback, consent behavior, and any relevant event-specific states.

## Related references

- [Designer elements](designer-elements.md) for the block inventory and editing rules.
- [Custom attributes](custom-attributes.md) for Designer metadata, containers, block markers, and style settings.
- [Embed and client API](embed-and-client-api.md) for hosted-form lifecycle and rendering behavior.
- [Styling and submission feedback](styling-and-submission-feedback.md) for visual overrides and post-submit states.
