import importlib.util
import io
import json
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


REPOSITORY = Path(__file__).parents[1]
MODULE_PATH = REPOSITORY / "scripts" / "validate_form.py"
SPEC = importlib.util.spec_from_file_location("validate_form", MODULE_PATH)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = VALIDATOR
SPEC.loader.exec_module(VALIDATOR)


VALID_NATIVE = """<!doctype html>
<html>
  <head>
    <meta type="xrm/designer/setting" name="type"
          value="marketing-designer-content-editor-document">
  </head>
  <body>
    <form class="marketingForm" aria-label="Contact request">
      <div data-layout="true">
        <div data-section="true">
          <div data-container="true" data-container-width="100">
            <div data-editorblocktype="TextFormField"
                 data-targetproperty="emailaddress1"
                 data-required="required">
              <label for="email">Email</label>
              <input id="email" name="emailaddress1" type="email" required>
            </div>
          </div>
        </div>
        <div data-section="true">
          <div data-container="true" data-container-width="50">
            <div data-editorblocktype="Captcha"></div>
          </div>
          <div data-container="true" data-container-width="50">
            <div data-editorblocktype="SubmitButton">
              <button type="submit">Send</button>
            </div>
          </div>
        </div>
      </div>
    </form>
  </body>
</html>
"""


INVALID_NATIVE = """<html><body>
<form class="marketingForm" onclick="submitNow()">
  <div data-editorblocktype="Consent" data-purposeid="undefined"
       data-channels="Email">
    <input id="same" name="undefined">
  </div>
  <input id="same" name="emailaddress1">
</form>
</body></html>
"""


DESIGNER_GROUPS = """
<div data-editorblocktype="MultiOptionSetFormField" data-prefill="false">
  <label class="block-label" for="industries">Industry</label>
  <fieldset id="industries" name="Industry">
    <div><input id="industry-tech" type="checkbox" name="Industry" value="1"><label for="industry-tech">Technology</label></div>
    <div><input id="industry-manufacturing" type="checkbox" name="Industry" value="2"><label for="industry-manufacturing">Manufacturing</label></div>
  </fieldset>
</div>
<div data-editorblocktype="TwoOptionFormField" data-prefill="false">
  <label class="block-label" for="contact-method">Preferred contact method</label>
  <div class="radiobuttons" id="contact-method">
    <div><input id="method-email" type="radio" name="Contact method" value="1" checked><label for="method-email">Email</label></div>
    <div><input id="method-phone" type="radio" name="Contact method" value="0"><label for="method-phone">Phone</label></div>
  </div>
</div>
"""


VALID_CAPTURE = """<!doctype html>
<html><body>
<form id="existing-form">
  <label for="first">First name</label>
  <input id="first" name="firstName">
  <button type="submit">Send</button>
</form>
<script src="https://assets.example.microsoft/FormCapture.bundle.js"></script>
<script>
d365mktformcapture.waitForElement("#existing-form").then((form) => {
  const mappings = [
    { FormFieldName: "firstName", DataverseFieldName: "firstname" }
  ];
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const serialized = d365mktformcapture.serializeForm(form, mappings);
    const payload = serialized.SerializedForm.build();
    const captureConfig = {
      FormId: "8bb6ecb1-42f3-4aac-8af4-111111111111",
      FormApiUrl: "https://example.dynamics.com/api/v1.0/forms"
    };
    d365mktformcapture.submitForm(captureConfig, payload).then(() => {});
  });
});
</script>
</body></html>
"""


INVALID_CAPTURE = """<html><body>
<form id="existing"><input name="email"><button type="submit">Send</button></form>
<script src="FormCapture.bundle.js"></script>
<script>
d365mktformcapture.waitForElement("#existing").then((form) => {
  const mappings = [{ FormFieldName: "missing", DataverseFieldName: "emailaddress1" }];
  const payload = d365mktformcapture.serializeForm(form, mappings).SerializedForm.build();
  d365mktformcapture.submitForm({FormId: "...", FormApiUrl: "***Please fill***"}, payload);
});
</script>
</body></html>
"""


class ValidateFormTests(unittest.TestCase):
    def codes(self, source: str, mode: str) -> tuple[list[str], list[str]]:
        resolved, findings = VALIDATOR.validate_text(source, mode)
        self.assertEqual(resolved, mode)
        errors = [item.code for item in findings if item.severity == "error"]
        warnings = [item.code for item in findings if item.severity == "warning"]
        return errors, warnings

    def test_valid_native_has_no_errors(self) -> None:
        errors, _ = self.codes(VALID_NATIVE, "native")
        self.assertEqual(errors, [])

    def test_invalid_native_reports_structural_and_placeholder_errors(self) -> None:
        errors, warnings = self.codes(INVALID_NATIVE, "native")
        self.assertIn("duplicate-id", errors)
        self.assertIn("placeholder-value", errors)
        self.assertIn("submit", errors)
        self.assertIn("inline-event", warnings)

    def test_valid_capture_has_no_errors(self) -> None:
        errors, _ = self.codes(VALID_CAPTURE, "capture")
        self.assertEqual(errors, [])

    def test_invalid_capture_reports_environment_and_mapping_errors(self) -> None:
        errors, warnings = self.codes(INVALID_CAPTURE, "capture")
        self.assertIn("capture-form-id", errors)
        self.assertIn("capture-api-url", errors)
        self.assertIn("capture-control", errors)
        self.assertIn("capture-promise", warnings)

    def test_auto_detects_capture(self) -> None:
        mode, _ = VALIDATOR.validate_text(VALID_CAPTURE, "auto")
        self.assertEqual(mode, "capture")

    def test_json_option_metadata_is_not_a_placeholder(self) -> None:
        self.assertFalse(
            VALIDATOR.is_placeholder('[{"value":"1","label":"Option 1"}]')
        )

    def test_button_without_type_is_a_submit_control(self) -> None:
        button = VALIDATOR.Node("button", {}, None, 1)
        self.assertTrue(VALIDATOR.is_submit_control(button))

    def test_repository_styled_form_has_no_structural_errors(self) -> None:
        source = (REPOSITORY / "examples/restyle/styled.html").read_text(encoding="utf-8")
        errors, _ = self.codes(source, "native")
        self.assertEqual(errors, [])

    def test_archival_lead_export_is_rejected_as_deployable(self) -> None:
        source = (REPOSITORY / "docs/archive/examples/lead/default.html").read_text(
            encoding="utf-8"
        )
        errors, _ = self.codes(source, "native")
        self.assertIn("consent-config", errors)
        self.assertIn("placeholder-value", errors)

    def test_table_layout_is_rejected(self) -> None:
        source = VALID_NATIVE.replace('<div data-layout="true">', '<table data-layout="true"><tbody><tr><td>').replace(
            '      </div>\n    </form>', '      </td></tr></tbody></table>\n    </form>')
        errors, _ = self.codes(source, "native")
        self.assertIn("div-layout", errors)
        self.assertIn("table-layout", errors)

    def test_plain_input_inside_text_block_is_rejected(self) -> None:
        source = VALID_NATIVE.replace('</form>', '<div data-editorblocktype="Text"><input name="question"></div></form>')
        errors, _ = self.codes(source, "native")
        self.assertIn("unmanaged-control", errors)

    def test_table_wrapper_outside_form_is_rejected(self) -> None:
        source = VALID_NATIVE.replace('<form ', '<table><tr><td><form ', 1).replace('</form>', '</form></td></tr></table>', 1)
        errors, _ = self.codes(source, 'native')
        self.assertIn('table-layout', errors)

    def test_duplicate_mapping_with_new_control_id_is_rejected(self) -> None:
        block = re.search(r'<div data-editorblocktype="TextFormField".*?</div>', VALID_NATIVE, re.DOTALL).group(0)
        duplicate = block.replace('id="email"', 'id="email-copy"').replace('for="email"', 'for="email-copy"')
        errors, _ = self.codes(VALID_NATIVE.replace(block, block + duplicate), "native")
        self.assertIn("duplicate-field", errors)

    def test_duplicate_unmapped_blocks_are_rejected_but_grouped_choices_are_allowed(self) -> None:
        source = (REPOSITORY / "examples/restyle/original.html").read_text()
        errors, _ = self.codes(source, "native")
        self.assertEqual(errors, [])
        duplicate = '<div data-editorblocktype="TextFormField"><input name="Contact method"></div>'
        errors, _ = self.codes(source.replace('</form>', duplicate + '</form>'), "native")
        self.assertIn("duplicate-field", errors)

    def test_empty_captcha_is_a_warning(self) -> None:
        _, warnings = self.codes(VALID_NATIVE, "native")
        self.assertIn("empty-captcha", warnings)

    def wrapped_native(self, wrapper: str = '<div class="innerSection wrap-section">') -> str:
        return VALID_NATIVE.replace('<div data-section="true">', '<div data-section="true">' + wrapper).replace(
            '        </div>\n      </div>\n    </form>', '        </div></div>\n      </div>\n    </form>').replace(
            '        </div>\n        <div data-section="true">', '        </div></div>\n        <div data-section="true">')

    def test_saved_inner_sections_are_recognized(self) -> None:
        errors, warnings = self.codes(self.wrapped_native(), "native")
        self.assertEqual(errors, [])
        self.assertNotIn("empty-section", warnings)
        self.assertNotIn("container-width-total", warnings)

    def test_inner_section_widths_are_still_validated(self) -> None:
        source = self.wrapped_native().replace('data-container-width="100"', 'data-container-width="75"', 1)
        _, warnings = self.codes(source, "native")
        self.assertIn("container-width-total", warnings)
        errors, _ = self.codes(source.replace('data-container-width="75"', 'data-container-width="invalid"'), "native")
        self.assertIn("container-width", errors)

    def test_arbitrary_or_functional_wrappers_remain_errors(self) -> None:
        for wrapper in ('<div class="ordinary-wrapper">', '<div class="innerSection" data-editorblocktype="Text">'):
            with self.subTest(wrapper=wrapper):
                errors, _ = self.codes(self.wrapped_native(wrapper), "native")
                self.assertIn("container-parent", errors)

    def test_multiple_inner_rows_have_separate_width_totals(self) -> None:
        row = '<div class="innerSection"><div data-container="true" data-container-width="100"></div></div>'
        source = VALID_NATIVE.replace('<div data-layout="true">', '<div data-layout="true"><div data-section="true">' + row + row + '</div>', 1)
        errors, warnings = self.codes(source, "native")
        self.assertEqual(errors, [])
        self.assertNotIn("container-width-total", warnings)
        changed = source.replace(row + row, row + row.replace('width="100"', 'width="50"'), 1)
        _, warnings = self.codes(changed, "native")
        self.assertEqual(warnings.count("container-width-total"), 1)

    def native_groups(self, groups: str = DESIGNER_GROUPS) -> str:
        return VALID_NATIVE.replace('<div data-container="true" data-container-width="100">',
            '<div data-container="true" data-container-width="100">' + groups, 1)

    def test_native_designer_group_labels_are_accessibility_warnings(self) -> None:
        errors, warnings = self.codes(self.native_groups(), "native")
        self.assertEqual(errors, [])
        self.assertEqual(warnings.count("designer-group-label"), 2)

    def test_missing_group_and_cross_block_targets_are_errors(self) -> None:
        for target in ("missing-group", "contact-method"):
            with self.subTest(target=target):
                groups = DESIGNER_GROUPS.replace('for="industries"', f'for="{target}"', 1)
                errors, _ = self.codes(self.native_groups(groups), "native")
                self.assertIn("label-target", errors)

    def test_group_exception_requires_labeled_native_choices(self) -> None:
        cases = [
            DESIGNER_GROUPS.replace('data-editorblocktype="MultiOptionSetFormField"', 'data-editorblocktype="Text"', 1),
            DESIGNER_GROUPS.replace('type="checkbox"', 'type="text"', 1),
            DESIGNER_GROUPS.replace('<label for="industry-tech">Technology</label>', ''),
            DESIGNER_GROUPS.replace('class="block-label"', 'class="ordinary-label"', 1),
        ]
        for groups in cases:
            with self.subTest(groups=groups):
                errors, _ = self.codes(self.native_groups(groups), "native")
                self.assertIn("label-target", errors)

    def test_capture_group_labels_do_not_get_native_exception(self) -> None:
        source = VALID_CAPTURE.replace('</form>', DESIGNER_GROUPS + '</form>', 1)
        errors, warnings = self.codes(source, "capture")
        self.assertEqual(errors.count("label-target"), 2)
        self.assertNotIn("designer-group-label", warnings)


class PreservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.original = (REPOSITORY / "examples/restyle/original.html").read_text()
        cls.styled = (REPOSITORY / "examples/restyle/styled.html").read_text()

    def compare_codes(self, original: str, styled: str) -> set[str]:
        return {item.code for item in VALIDATOR.compare_native(original, styled)}

    def test_styled_example_preserves_the_original_contract(self) -> None:
        self.assertEqual(VALIDATOR.compare_native(self.original, self.styled), [])

    def test_functional_changes_are_rejected(self) -> None:
        cases = {
            "mapping": ('data-targetproperty="firstname"', 'data-targetproperty="lastname"'),
            "audience": ('data-targetaudience="contact"', 'data-targetaudience="lead"'),
            "control ID": ('id="firstname-fixture"', 'id="new-firstname"'),
            "validation": ('maxlength="50"', 'maxlength="100"'),
            "required": ('value="" required', 'value=""'),
            "hidden value": ('value="website"', 'value="different-source"'),
            "readonly": ('type="email"', 'type="email" readonly'),
            "consent": ('data-channels="Email"', 'data-channels="Text"'),
            "default choice": ('value="1" selected', 'value="1"'),
            "radio default": ('value="0" checked', 'value="0"'),
            "label association": ('for="email-fixture"', 'for="phone-fixture"'),
        }
        for name, (before, after) in cases.items():
            with self.subTest(change=name):
                changed = self.styled.replace(before, after, 1)
                self.assertNotEqual(changed, self.styled)
                self.assertIn("contract-removed", self.compare_codes(self.original, changed))

    def test_removed_and_added_fields_are_rejected(self) -> None:
        removed = self.styled.replace('<input id="phone-fixture" name="mobilephone" type="tel" maxlength="50" autocomplete="tel" value="">', '')
        self.assertIn("contract-removed", self.compare_codes(self.original, removed))
        added = self.styled.replace('</form>', '<div data-editorblocktype="TextFormField"><input name="Extra"></div></form>')
        self.assertIn("contract-added", self.compare_codes(self.original, added))

    def test_unknown_future_metadata_is_preserved(self) -> None:
        original = self.original.replace('data-targetproperty="firstname"', 'data-targetproperty="firstname" data-future-validation="enabled"')
        self.assertIn("contract-removed", self.compare_codes(original, self.styled))

    def test_control_cannot_move_to_a_different_field_block(self) -> None:
        first = re.search(r'<input id="firstname-fixture"[^>]*>', self.styled).group(0)
        last = re.search(r'<input id="lastname-fixture"[^>]*>', self.styled).group(0)
        moved = self.styled.replace(first, 'SWAP_CONTROL', 1).replace(last, first, 1).replace('SWAP_CONTROL', last, 1)
        self.assertIn("contract-removed", self.compare_codes(self.original, moved))

    def test_reordered_options_are_rejected(self) -> None:
        before = '<option value="1" selected>Email</option><option value="2">Phone</option>'
        after = '<option value="2">Phone</option><option value="1" selected>Email</option>'
        self.assertIn("options-changed", self.compare_codes(self.original, self.styled.replace(before, after)))

    def test_decorative_label_wrapper_and_added_classes_are_allowed(self) -> None:
        changed = self.styled.replace('>First name</label>', '><span class="label-copy">First name</span></label>')
        self.assertEqual(VALIDATOR.compare_native(self.original, changed), [])

    def test_text_blocks_document_title_and_submit_wording_are_preserved(self) -> None:
        cases = [
            ('Let’s talk', 'Changed heading'),
            ('Tell us a little about yourself and how we can help.', 'Changed descriptive text.'),
            ('Send request', 'Changed submit wording'),
            ('Contact form — regression fixture', 'Changed document title'),
        ]
        for before, after in cases:
            with self.subTest(copy=before):
                changed = self.styled.replace(before, after, 1)
                self.assertNotEqual(changed, self.styled)
                self.assertIn('source-text-changed', self.compare_codes(self.original, changed))

    def test_decorative_text_wrapper_preserves_copy(self) -> None:
        changed = self.styled.replace('<h1>Let’s talk</h1>', '<h1><span class="heading-copy">Let’s talk</span></h1>')
        self.assertEqual(VALIDATOR.compare_native(self.original, changed), [])

    def test_intact_containers_can_be_reordered(self) -> None:
        pattern = r'<div class="columnContainer" data-container="true" data-container-width="50" id="container-(?:firstname|lastname)".*?</div>\s*</div>'
        first, last = re.findall(pattern, self.styled, re.DOTALL)
        reordered = self.styled.replace(first, 'CONTAINER_SWAP', 1).replace(last, first, 1).replace('CONTAINER_SWAP', last, 1)
        self.assertEqual(VALIDATOR.compare_native(self.original, reordered), [])

    def test_generated_classes_cannot_be_removed(self) -> None:
        changed = self.styled.replace('class="textFormFieldBlock"', 'class="new-field-style"', 1)
        self.assertIn("class-removed", self.compare_codes(self.original, changed))

    def test_scripts_and_execution_order_are_protected(self) -> None:
        scripts = '<script src="/existing-script.js"></script><script>window.fixtureReady = true;</script>'
        original = self.original.replace('</body>', scripts + '</body>')
        styled = self.styled.replace('</body>', scripts + '</body>')
        self.assertEqual(VALIDATOR.compare_native(original, styled), [])
        cases = [styled.replace('fixtureReady = true', 'fixtureReady = false'),
                 styled.replace(scripts, '<script>window.fixtureReady = true;</script><script src="/existing-script.js"></script>'),
                 styled.replace(scripts, '').replace('<body>', '<body>' + scripts),
                 self.styled.replace('</body>', '<script>document.querySelector("form").onsubmit = () => false;</script></body>')]
        for changed in cases:
            self.assertIn("scripts-changed", self.compare_codes(original, changed))

    def test_original_styles_and_order_are_protected(self) -> None:
        edited = self.styled.replace('max-width: 600px; margin: 24px auto;', 'max-width: 400px; margin: 24px auto;', 1)
        self.assertIn("stylesheet-changed", self.compare_codes(self.original, edited))
        override = re.search(r'<style data-form-styling="true">.*?</style>', self.styled, re.DOTALL).group(0)
        reordered = self.styled.replace(override, '').replace('<style>', override + '<style>', 1)
        self.assertIn("stylesheet-order", self.compare_codes(self.original, reordered))

    def test_external_stylesheet_order_is_preserved(self) -> None:
        links = '<link rel="stylesheet" href="/first.css"><link rel="stylesheet" href="/second.css">'
        original = self.original.replace('<style>', links + '<style>', 1)
        styled = self.styled.replace('<style>', links + '<style>', 1)
        swapped = styled.replace(links, '<link rel="stylesheet" href="/second.css"><link rel="stylesheet" href="/first.css">')
        self.assertEqual(VALIDATOR.compare_native(original, styled), [])
        self.assertIn('stylesheet-order', self.compare_codes(original, swapped))

    def test_new_global_css_is_reported(self) -> None:
        for selector in ["body", ":root", "input", "form.marketingForm, body", "form.marketingFormOther", "form.marketingForm-other"]:
            with self.subTest(selector=selector):
                changed = self.styled.replace('</head>', f'<style>{selector} {{ color: red; }}</style></head>')
                self.assertIn("css-scope", self.compare_codes(self.original, changed))

    def test_single_global_rule_inside_media_query_is_reported(self) -> None:
        changed = self.styled.replace('</head>', '<style>@media (max-width: 600px) { body { color: red; } }</style></head>')
        self.assertIn('css-scope', self.compare_codes(self.original, changed))

    def test_cli_separates_source_warnings_from_introduced_errors(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            original = Path(directory) / "original.html"
            styled = Path(directory) / "styled.html"
            original.write_text(self.original)
            styled.write_text(self.styled)
            output = io.StringIO()
            with redirect_stdout(output):
                status = VALIDATOR.main([str(styled), '--original', str(original), '--json'])
            payload = json.loads(output.getvalue())
            self.assertEqual(status, 0)
            self.assertEqual(payload['summary'], {'errors': 0, 'warnings': 0})
            self.assertEqual(payload['source_summary'], {'errors': 0, 'warnings': 1})
            self.assertEqual(payload['source_findings'][0]['code'], 'recaptcha')
            styled.write_text(self.styled.replace('data-channels="Email"', 'data-channels="Text"'))
            with redirect_stdout(io.StringIO()):
                self.assertEqual(VALIDATOR.main([str(styled), '--original', str(original), '--json']), 1)

    def test_existing_source_errors_remain_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            original = Path(directory) / 'original.html'
            styled = Path(directory) / 'styled.html'
            original.write_text(self.original.replace('data-purposeid="22222222-2222-4222-8222-222222222222"', 'data-purposeid="undefined"'))
            styled.write_text(original.read_text())
            output = io.StringIO()
            with redirect_stdout(output):
                status = VALIDATOR.main([str(styled), '--original', str(original), '--json'])
            payload = json.loads(output.getvalue())
            self.assertEqual(status, 1)
            self.assertEqual(payload['summary']['errors'], 0)
            self.assertGreater(payload['source_summary']['errors'], 0)


class SkillDocumentationTests(unittest.TestCase):
    def test_local_markdown_links_exist(self) -> None:
        link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
        documents = [
            REPOSITORY / "SKILL.md",
            REPOSITORY / "README.md",
            *sorted((REPOSITORY / "references").glob("*.md")),
            *sorted((REPOSITORY / "docs").rglob("*.md")),
        ]
        for document in documents:
            source = document.read_text(encoding="utf-8")
            for raw_target in link_pattern.findall(source):
                if raw_target.startswith(("http://", "https://", "#")):
                    continue
                target = raw_target.split("#", 1)[0]
                with self.subTest(document=document.name, target=target):
                    self.assertTrue((document.parent / target).is_file())


if __name__ == "__main__":
    unittest.main()
