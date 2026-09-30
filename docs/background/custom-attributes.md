# Custom attributes

Use this reference when adding or reviewing HTML metadata that enables Customer Insights - Journeys Designer features. These attributes are Designer instructions, not field mappings or general-purpose application hooks. Start from a target-environment form and verify current behavior against the official documentation before relying on an attribute in production.

Official reference: [Microsoft Learn custom Designer attributes guidance](https://learn.microsoft.com/en-us/dynamics365/customer-insights/journeys/custom-template-attributes).

## Form-relevant attributes

| Attribute or tag | Purpose | Guidance |
| --- | --- | --- |
| `<meta type="xrm/designer/setting" name="type" value="marketing-designer-content-editor-document">` | Enables the drag-and-drop Designer experience. | Keep it in the document `<head>` when the form is intended to use the full Designer. |
| `data-container="true"` | Marks a region where Designer elements can be placed. | Keep the opening and closing tags paired. Do not use it as a general CSS hook. |
| `data-locked="hard"` | Locks a container and its contents in Designer view. | Use only when the form owner explicitly wants the region read-only. |
| `data-editorblocktype="..."` | Identifies a Designer-managed element. | Preserve the generated value and manage the element through Designer properties where possible. |
| `data-protected="true"` | Protects an individual element's content and properties in Designer view. | It protects Designer editing, not access to the raw HTML. |
| `property-reference="..."` | Connects an HTML attribute to a Designer style setting. | Reference a setting declared in the `<head>`; use the documented semicolon-separated syntax for multiple properties. |

Form exports also commonly use layout markers such as `data-layout="true"`, `data-section="true"`, `data-container-width`, and `data-layout-maxwidth`. See [Form structure](form-structure.md) for how those markers compose the form layout.

## Enable the Designer

Place the drag-and-drop marker in the document `<head>`:

```html
<meta
  type="xrm/designer/setting"
  name="type"
  value="marketing-designer-content-editor-document"
>
```

Without this marker, the Designer may use its simplified full-page editing experience instead of exposing containers, Toolbox elements, and element properties.

Microsoft supports pasting externally created HTML into the HTML editor. The imported page can render in the simplified full-page editor, and the meta tag plus supported containers can enable drag-and-drop features. This does not make ordinary `<input>` elements valid mapped Contact or Lead fields. Add mapped and unmapped fields through the form editor.

## Containers and elements

The basic relationship is a container holding one or more marked Designer elements:

```html
<div data-container="true">
  <div data-editorblocktype="Text">
    <p>Designer-managed text</p>
  </div>
</div>
```

Content inside a `data-editorblocktype` element is managed by the Designer. Prefer the Designer tab and element properties for changing it; direct edits may be overwritten or produce unpredictable results.

To lock a whole container:

```html
<div data-container="true" data-locked="hard">
  <!-- Designer cannot edit this region. -->
</div>
```

To protect one element:

```html
<div data-editorblocktype="Divider" data-protected="true">
  <!-- Protected Designer content. -->
</div>
```

Container locking takes precedence over the locked or unlocked state of elements inside it. These controls affect Designer editing; they do not replace application authorization or protect secrets.

## Style settings and property references

Declare a style setting in the `<head>`:

```html
<meta
  type="xrm/designer/setting"
  name="layout-max-width"
  value="600px"
  datatype="text"
  label="Layout max width"
>
```

Reference it from an element in the `<body>`:

```html
<div property-reference="data-layout-maxwidth:@layout-max-width">
  ...
</div>
```

Multiple references use semicolons in one attribute:

```html
<img property-reference="src:@hero-image;height:@hero-image-height;" alt="..."><!-- illustrative -->
```

For CSS values, the documented form surrounds the replaceable value with matching comments:

```css
.marketingForm {
  max-width: /* @layout-max-width */ 600px /* @layout-max-width */;
}
```

Keep style settings limited to visual properties. Do not use them to rewrite field mappings, control IDs, consent identifiers, or other behavior-critical form metadata.

## Safe editing rules

- Preserve generated attributes and paired container/block boundaries.
- Do not invent a `data-editorblocktype` value or assume a block is supported because it appears in another product surface.
- Do not hand-author `data-targetproperty`, consent identifiers, or target-audience metadata to simulate a field mapping.
- Do not use `data-*` attributes as durable JavaScript hooks when a stable, scoped class or supported lifecycle event is available.
- Treat custom attributes as implementation details that may be rewritten when the form is saved. Recheck the published form after editing.
