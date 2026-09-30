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
