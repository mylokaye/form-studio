# Preserve the exported HTML contract

Read this before editing. The user already configured the form in Customer Insights - Journeys. The supplied native HTML is the baseline, including properties that are not visible in a screenshot.

## Inspect once, preserve throughout

Inventory the document envelope and Designer meta settings; the form root; layout/section/container regions; mapped and unmapped blocks; native controls and label associations; choices and default values; required and validation settings; consent and CAPTCHA; event-specific regions; scripts and external resources.

Preserve these source properties:

| Region | Protected properties |
| --- | --- |
| Document | Doctype, generated HTML attributes, Designer meta tags, resource URLs, original stylesheets |
| Form | Root class, ID, audience/behavior metadata, action/method when present, accessible naming |
| Layout | Div hierarchy, container IDs, `data-layout*`, `data-section`, `data-container*`, `property-reference` |
| Fields | Block type, `data-targetproperty`, `data-targetaudience`, `data-prefill`, required and field-specific metadata |
| Controls | Tag/type, name, ID, value, checked/selected state, hidden/read-only/disabled state, autocomplete, validation attributes |
| Labels and choices | Label association/text, option labels/values/order, group semantics and defaults |
| Consent | Compliance, purpose, topic, channel, opt-in metadata, controls and default states |
| Scripts | URLs, attributes, code, and execution order |

Preserve unknown nonvisual attributes too. Do not decide that an unfamiliar `data-*` setting is unnecessary. Add CSS classes without deleting existing ones. Preserve source words and answers unless the user explicitly requested copy changes; such changes must be reviewed separately from a styling-only comparison.

Mapped and unmapped fields can share type-specific block names such as `TextFormField` and `OptionSetFormField`. An unmapped field can have no `data-targetproperty`; this does not authorize treating a plain input inside a Text block as an unmapped field. Do not invent field definitions. Keep the actual generated shape and logical name.

## Div layout

The expected structural shape is:

```text
form.marketingForm
└── div[data-layout="true"]
    └── div[data-section="true"]
        └── div[data-container="true"]
            └── generated block[data-editorblocktype]
```

Require div elements for the layout, section, and container regions. Do not use tables to position Designer blocks. A genuine content table or third-party runtime table is not itself a form layout; inspect its purpose before flagging it.

When the source uses a legacy table layout, have the user enable **Enable table-less layouts in Form editor** in Dynamics, edit/save the form, and export again. Automatic HTML surgery on a legacy form is outside this styling workflow.

Generated exports may have additional wrappers. Preserve them. A screenshot is insufficient evidence for changing structural ownership or moving a control to another field block.

## Existing problems

Record source findings before editing. A missing CAPTCHA, placeholder consent value, duplicate field, malformed label, or failing script is an existing form issue. Preserve the source during the styling pass and report what needs correction in Dynamics. Never fill gaps using repository example IDs or fabricated configuration.

The checker recognizes common field shapes and compares unknown metadata. It cannot determine whether a logical name exists, whether a control is supported in the selected audience, whether consent belongs to the selected compliance profile, or whether a CAPTCHA is operational. Dynamics acceptance and a recorded submission provide that evidence.

Sources: [Microsoft form customization and validation](https://learn.microsoft.com/en-us/dynamics365/customer-insights/journeys/real-time-marketing-manage-forms), [div-based layouts](https://learn.microsoft.com/en-us/troubleshoot/dynamics-365/customer-insights/journeys/forms/troubleshooting-forms), [unmapped fields](https://learn.microsoft.com/en-us/dynamics365/customer-insights/journeys/real-time-marketing-forms-custom-fields).
