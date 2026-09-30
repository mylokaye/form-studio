# Styling and submission feedback

## Prefer supported settings

Start with the Designer and supported form settings. Set standard post-submission behavior in **Form settings**: choose a thank-you notification or a redirect. The thank-you notification is shown briefly even when a redirect is selected.

Use custom CSS only when the result cannot be achieved through the Designer or form settings, and keep selectors scoped to the target form.

## Submission feedback

To replace the default post-submission experience, configure the form placeholder with `data-preventsubmissionui="true"`, then render a custom message in a verified `d365mkt-afterformsubmit` handler.

The generic green confirmation icon cannot be changed through standard settings. To hide it, use:

```css
div[data-cached-form-url] .onFormSubmittedFeedbackIcon {
  display: none;
}
```

This is a CSS workaround rather than a stable public API. Test it against the published form after platform updates.

To replace the icon, the source uses a background image on the feedback container and adds top padding to the feedback message. Substitute the image URL and tune the layout for the published form:

```css
div[data-cached-form-url] .onFormSubmittedFeedback .onFormSubmittedFeedbackMessage {
  padding: 10em 1em 0;
  color: #000;
  font-size: 14px;
}

div[data-cached-form-url] .onFormSubmittedFeedback .onFormSubmittedFeedbackInternalContainer {
  padding: 30px 0 30px 1px;
  background: url("YOUR-IMAGE-URL-HERE") center no-repeat;
  margin: auto;
}
```

Add custom CSS in the form's HTML editor, inside its existing `<style>` element, then save and publish. Prefer a transparent PNG, approximately 64–128px, and keep the image under 200KB.

## Custom redirect after successful submission

Use the built-in post-submission redirect whenever it meets the requirement. Use a JavaScript redirect only when custom client-side behavior is required. Confirm a successful submission in the event payload and keep any delay intentional so users can read the confirmation message.

```js
document.addEventListener("d365mkt-afterformsubmit", (event) => {
  const successful = event.detail?.successful ?? event.detail?.Success;
  if (successful !== true) return;
  window.setTimeout(() => {
    window.location.assign("/thank-you");
  }, 5000);
});
```

Microsoft Learn currently uses `Success` in its event-detail table and `event.detail.successful` in its sample. The fallback above is a compatibility workaround, not a documented third API. Verify the actual target-environment payload before use.

For published-form checks, allow up to 10 minutes for CDN refresh, or add the `#d365mkt-nocache` cache-bypass parameter to test immediately. Do not share cache-bypass links with customers because they bypass CDN caching and slow page loading. Then test success, validation failure, and mobile layout.

The 64–128px / under-200KB image suggestion is a practical guideline, not a Microsoft Learn platform limit.
