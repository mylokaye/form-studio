# Designer elements

## Identify a Designer-managed element

Each time an element is added through the **Designer** tab, the editor creates opening and closing `div` tags for it and generates the HTML required by that element's **Properties** settings.

Designer elements have a `data-editorblocktype` attribute. Its value identifies the element type:

```html
<div data-editorblocktype="Text">
  <!-- Do not edit Designer-managed content here. -->
</div>
```

## Element inventory

The generic Microsoft Designer reference spans multiple content surfaces and generations. The table below is an identification aid for inspected source, not a current allow-list for Customer Insights forms. Add fields, consent, topics, reCAPTCHA, and buttons from the target form editor; do not create a block by copying a listed name.

| Design element | Element category | `data-editorblocktype` value | Additional detail |
| --- | --- | --- | --- |
| Text | Common design element | `Text` | |
| Image | Common design element | `Image` | |
| Divider | Common design element | `Divider` | |
| Button | Common design element | `Button` | |
| Content block | Common design element | `Content` | Also has `data-block-datatype="text"` or `data-block-datatype="image"`. |
| Field | Form content | `Field-<field-name>` in the generic Designer reference; published form exports may use type-specific values such as `TextFormField` or `PhoneFormField` | Confirm the value against the published form before selecting or modifying a field. |
| Subscription list | Form content | `SubscriptionListBlock` | |
| Forward to a friend | Form content | `ForwardToFriendBlock` | |
| Do-not-email or Remember-me | Form content | `Field-checkbox` | Both create checkboxes; distinguish them through their internal settings. |
| Consent | Form content | `Consent` in the included form exports | Confirm the compliance and purpose settings against the form. |
| Topic | Form content | `Topic` in the included form exports | Confirm the compliance profile and topic settings against the form. |
| Submit button | Form content | `SubmitButton` in the included form exports; some generic documentation lists `SubmitButtonBlock` | Confirm the value against the published form. |
| Reset button | Form content | `ResetButton` in form exports; some generic documentation lists `ResetButtonBlock` | Confirm the value against the published form. |
| CAPTCHA | Form content | `Captcha` in form exports; some generic documentation lists `CaptchaBlock` | Confirm the value against the published form. |

Older exports can contain HIP CAPTCHA markup and related styles. HIP CAPTCHA was removed in June 2026 and no longer protects those forms; add the current reCAPTCHA element in the form editor and republish.

## Editing rule

Avoid editing content between a Designer element's opening and closing `div` tags in the HTML tab. The result can be unpredictable and the Designer may overwrite the changes. Use the **Designer** tab to manage the element's content and properties.

## Lock an element

Add `data-protected="true"` to the opening Designer element to lock its content and properties in Designer view.

```html
<div data-editorblocktype="Divider" data-protected="true">
  ...
</div>
```
