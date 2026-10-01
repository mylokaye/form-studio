#!/usr/bin/env python3
"""Local preflight checks for Customer Insights form source and Form Capture pages.

This checker deliberately does not claim platform compatibility. Customer Insights
must still save, validate, publish, and process a unique test submission.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable


VOID_TAGS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}
CONTROL_TAGS = {"input", "select", "textarea", "button"}
PLACEHOLDER_MARKERS = (
    "***please fill***",
    "your-image-url-here",
    "your-form-id",
    "your-api-url",
    "generated_id",
)


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str
    line: int | None = None


@dataclass
class Node:
    tag: str
    attrs: dict[str, str]
    parent: int | None
    line: int
    text: str = ""


class Inspector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.nodes: list[Node] = []
        self.stack: list[int] = []
        self.has_doctype = False
        self.doctype = ""

    def handle_decl(self, decl: str) -> None:
        if decl.lower().startswith("doctype"):
            self.has_doctype = True
            self.doctype = decl

    def handle_data(self, data: str) -> None:
        for index in self.stack:
            self.nodes[index].text += data

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        self._add_node(tag, attrs, push=tag.lower() not in VOID_TAGS)

    def handle_startendtag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        self._add_node(tag, attrs, push=False)

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        for position in range(len(self.stack) - 1, -1, -1):
            if self.nodes[self.stack[position]].tag == lowered:
                del self.stack[position:]
                return

    def _add_node(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
        *,
        push: bool,
    ) -> None:
        normalized = {key.lower(): value or "" for key, value in attrs}
        parent = self.stack[-1] if self.stack else None
        node = Node(tag.lower(), normalized, parent, self.getpos()[0])
        self.nodes.append(node)
        if push:
            self.stack.append(len(self.nodes) - 1)


def ancestors(inspector: Inspector, index: int) -> Iterable[int]:
    parent = inspector.nodes[index].parent
    while parent is not None:
        yield parent
        parent = inspector.nodes[parent].parent


def is_descendant(inspector: Inspector, index: int, ancestor: int) -> bool:
    return ancestor in ancestors(inspector, index)


def descendants(inspector: Inspector, index: int) -> list[tuple[int, Node]]:
    return [
        (candidate, node)
        for candidate, node in enumerate(inspector.nodes)
        if is_descendant(inspector, candidate, index)
    ]


def class_names(node: Node) -> set[str]:
    return set(node.attrs.get("class", "").split())


def is_submit_control(node: Node) -> bool:
    control_type = node.attrs.get("type", "").lower()
    if node.tag == "button":
        return control_type in {"", "submit"}
    return node.tag == "input" and control_type in {"submit", "image"}


def is_placeholder(value: str) -> bool:
    lowered = value.strip().lower()
    return (
        lowered in {"undefined", "null", "...", "todo", "tbd"}
        or "please fill" in lowered
        or any(marker in lowered for marker in PLACEHOLDER_MARKERS)
        or bool(re.search(r"\{[A-Za-z][A-Za-z0-9_.-]*\}", value))
    )


def is_designer_group_label(inspector: Inspector, label_index: int) -> bool:
    """Recognize native group headings without accepting arbitrary label targets."""
    label = inspector.nodes[label_index]
    if "block-label" not in class_names(label):
        return False
    parents = list(ancestors(inspector, label_index))
    if not any(inspector.nodes[index].tag == "form"
               and "marketingForm" in class_names(inspector.nodes[index]) for index in parents):
        return False
    block_index = next((index for index in parents
                        if "data-editorblocktype" in inspector.nodes[index].attrs), None)
    if block_index is None:
        return False
    block_type = inspector.nodes[block_index].attrs["data-editorblocktype"].lower()
    if block_type not in {"multioptionsetformfield", "twooptionformfield", "optionsetformfield"}:
        return False
    target_index = next((index for index, node in enumerate(inspector.nodes)
                         if node.attrs.get("id") == label.attrs.get("for")), None)
    if target_index is None or not is_descendant(inspector, target_index, block_index):
        return False
    target = inspector.nodes[target_index]
    if target.tag != "fieldset" and not (target.tag == "div" and "radiobuttons" in class_names(target)):
        return False
    group_nodes = descendants(inspector, target_index)
    controls = [node for _, node in group_nodes if node.tag in CONTROL_TAGS]
    expected_type = "checkbox" if block_type == "multioptionsetformfield" else "radio"
    labels = {node.attrs.get("for") for _, node in group_nodes if node.tag == "label"}
    return bool(controls) and all(
        node.tag == "input" and node.attrs.get("type", "").lower() == expected_type
        and node.attrs.get("id") and node.attrs["id"] in labels for node in controls
    )


def common_findings(inspector: Inspector, source: str, *, allow_designer_groups: bool = False) -> list[Finding]:
    findings: list[Finding] = []
    ids: dict[str, list[int]] = {}
    control_ids: set[str] = set()

    for node in inspector.nodes:
        node_id = node.attrs.get("id")
        if node_id:
            ids.setdefault(node_id, []).append(node.line)
            if node.tag in CONTROL_TAGS:
                control_ids.add(node_id)

        for attribute in node.attrs:
            if attribute.startswith("on"):
                findings.append(
                    Finding(
                        "warning",
                        "inline-event",
                        f"Inline event attribute {attribute!r} can be sanitized; use addEventListener.",
                        node.line,
                    )
                )

        for attribute, value in node.attrs.items():
            critical = (
                attribute.startswith("data-")
                or attribute in {"name", "value", "action", "src"}
            )
            if critical and is_placeholder(value):
                findings.append(
                    Finding(
                        "error",
                        "placeholder-value",
                        f"Replace non-deployable {attribute}={value!r} with a target-environment value.",
                        node.line,
                    )
                )

    for node_id, lines in ids.items():
        if len(lines) > 1:
            findings.append(
                Finding(
                    "error",
                    "duplicate-id",
                    f"ID {node_id!r} occurs {len(lines)} times.",
                    lines[0],
                )
            )

    for index, node in enumerate(inspector.nodes):
        if node.tag == "label" and node.attrs.get("for"):
            target = node.attrs["for"]
            if target not in control_ids:
                if allow_designer_groups and is_designer_group_label(inspector, index):
                    findings.append(Finding("warning", "designer-group-label",
                        "Designer group heading references an existing choice container; individual option labels are intact. Check the group's accessible name in the published form.", node.line))
                else:
                    findings.append(Finding("error", "label-target",
                        f"Label target {target!r} does not match a control ID.", node.line))

    lowered_source = source.lower()
    for marker in PLACEHOLDER_MARKERS:
        if marker in lowered_source:
            findings.append(
                Finding(
                    "error",
                    "placeholder-marker",
                    f"Unresolved placeholder marker {marker!r} remains in the document.",
                )
            )

    return findings


def validate_native(inspector: Inspector, source: str) -> list[Finding]:
    findings = common_findings(inspector, source, allow_designer_groups=True)
    forms = [
        index
        for index, node in enumerate(inspector.nodes)
        if node.tag == "form" and "marketingForm" in class_names(node)
    ]
    if len(forms) != 1:
        findings.append(
            Finding(
                "error",
                "marketing-form-count",
                f"Expected exactly one form.marketingForm; found {len(forms)}.",
            )
        )
        return findings

    form_index = forms[0]
    form = inspector.nodes[form_index]
    form_nodes = descendants(inspector, form_index)
    controls = [(index, node) for index, node in form_nodes if node.tag in CONTROL_TAGS]
    submit_controls = [node for _, node in controls if is_submit_control(node)]
    if not submit_controls:
        findings.append(
            Finding("error", "submit", "The marketing form has no submit control.", form.line)
        )

    if not form.attrs.get("aria-label") and not form.attrs.get("aria-labelledby"):
        findings.append(
            Finding(
                "warning",
                "form-name",
                "Give the marketing form an accessible name.",
                form.line,
            )
        )

    layout_nodes = [
        index
        for index, node in form_nodes
        if node.attrs.get("data-layout", "").lower() == "true"
    ]
    if not layout_nodes:
        findings.append(
            Finding(
                "warning",
                "designer-layout",
                "No data-layout region found. Full-page HTML can render, but drag-and-drop layout support may be limited.",
                form.line,
            )
        )

    sections = [
        index
        for index, node in form_nodes
        if node.attrs.get("data-section", "").lower() == "true"
    ]
    containers = [
        index
        for index, node in form_nodes
        if node.attrs.get("data-container", "").lower() == "true"
    ]

    for index in [*layout_nodes, *sections, *containers]:
        node = inspector.nodes[index]
        if node.tag != "div":
            findings.append(Finding(
                "error", "div-layout",
                "Layout, section, and container regions must use div elements. Enable the table-less layout in Dynamics and export again.",
                node.line,
            ))
    for index, node in enumerate(inspector.nodes):
        if node.tag == "table" and (
            is_descendant(inspector, form_index, index)
            or any(child.attrs.get("data-editorblocktype") for _, child in descendants(inspector, index))
        ):
            findings.append(Finding(
                "error", "table-layout",
                "A table contains the form or Designer blocks. Export a div-based form instead of using a table for form layout.",
                node.line,
            ))

    section_rows: dict[int, dict[int, list[Node]]] = {}
    for index in containers:
        parent_index = inspector.nodes[index].parent
        section_index = parent_index if parent_index in sections else None
        if section_index is None and parent_index is not None:
            parent = inspector.nodes[parent_index]
            if (parent.tag == "div" and "innerSection" in class_names(parent)
                    and parent.parent in sections
                    and not any(key in parent.attrs for key in (
                        "data-layout", "data-section", "data-container",
                        "data-editorblocktype", "data-targetproperty"))):
                section_index = parent.parent
        if section_index is None:
            findings.append(Finding(
                "error", "container-parent",
                "A data-container region must belong directly to a data-section, or to its native div.innerSection row wrapper.",
                inspector.nodes[index].line,
            ))
        else:
            section_rows.setdefault(section_index, {}).setdefault(parent_index, []).append(inspector.nodes[index])

    for section_index in sections:
        section = inspector.nodes[section_index]
        if layout_nodes and not any(
            is_descendant(inspector, section_index, layout) for layout in layout_nodes
        ):
            findings.append(
                Finding(
                    "error",
                    "section-parent",
                    "A data-section region is not inside data-layout.",
                    section.line,
                )
            )
        rows = section_rows.get(section_index, {})
        if not rows:
            findings.append(
                Finding(
                    "warning",
                    "empty-section",
                    "A data-section region has no direct or native innerSection data-container row.",
                    section.line,
                )
            )
            continue
        for row_containers in rows.values():
            widths: list[float] = []
            for container in row_containers:
                raw_width = container.attrs.get("data-container-width")
                if raw_width:
                    try:
                        widths.append(float(raw_width))
                    except ValueError:
                        findings.append(
                            Finding(
                                "error",
                                "container-width",
                                f"Invalid data-container-width value {raw_width!r}.",
                                container.line,
                            )
                        )
            if widths and abs(sum(widths) - 100.0) > 0.1:
                findings.append(
                    Finding(
                        "warning",
                        "container-width-total",
                        f"Row container widths total {sum(widths):g}, not 100.",
                        section.line,
                    )
                )

    mapped_blocks = [
        (index, node)
        for index, node in form_nodes
        if node.attrs.get("data-targetproperty")
    ]
    mappings = Counter(
        (node.attrs.get("data-targetaudience", ""), node.attrs["data-targetproperty"])
        for _, node in mapped_blocks
    )
    for (_, target), count in mappings.items():
        if count > 1:
            findings.append(Finding(
                "error", "duplicate-field",
                f"Mapped field {target!r} occurs in {count} blocks for the same audience.",
            ))

    # Unmapped controls use the same generated field-block types as mapped fields.
    # This recognizes their shape; only the target environment proves their schema.
    field_blocks = [
        (index, node) for index, node in form_nodes
        if node.attrs.get("data-editorblocktype", "").lower().endswith("formfield")
        or node.attrs.get("data-targetproperty")
    ]
    unmapped_names: Counter[str] = Counter()
    for index, block in field_blocks:
        names = {
            node.attrs["name"] for _, node in descendants(inspector, index)
            if node.tag in {"input", "select", "textarea"} and node.attrs.get("name")
        }
        if not block.attrs.get("data-targetproperty"):
            unmapped_names.update(names)
        if not any(parent in containers for parent in ancestors(inspector, index)):
            findings.append(Finding("error", "field-container",
                "A field block must remain inside a div container.", block.line))
    for name, count in unmapped_names.items():
        if count > 1:
            findings.append(Finding("error", "duplicate-field",
                f"Unmapped field {name!r} occurs in {count} field blocks."))
    if not mapped_blocks:
        findings.append(
            Finding(
                "warning",
                "mapped-fields",
                "No mapped field blocks found. Confirm fields through the target form editor.",
                form.line,
            )
        )

    for block_index, block in mapped_blocks:
        target = block.attrs["data-targetproperty"]
        block_controls = [
            node
            for _, node in descendants(inspector, block_index)
            if node.tag in {"input", "select", "textarea"}
        ]
        if not block_controls:
            findings.append(
                Finding(
                    "error",
                    "mapped-control",
                    f"Mapped block {target!r} contains no native control.",
                    block.line,
                )
            )
            continue
        if not any(control.attrs.get("name") == target for control in block_controls):
            findings.append(
                Finding(
                        "error",
                        "mapped-name",
                    f"Mapped block {target!r} has no descendant control with the same name.",
                    block.line,
                )
            )

        block_required = block.attrs.get("data-required", "").lower() in {
            "required",
            "true",
        }
        native_required = any("required" in control.attrs for control in block_controls)
        if block_required != native_required:
            findings.append(
                Finding(
                    "warning",
                    "required-mismatch",
                    f"Mapped block {target!r} has inconsistent Designer and native required markers.",
                    block.line,
                )
            )

    for control_index, control in controls:
        if is_submit_control(control) or control.attrs.get("type", "").lower() in {
            "button",
            "reset",
        }:
            continue
        if any(
            inspector.nodes[parent].attrs.get("data-targetproperty")
            or inspector.nodes[parent].attrs.get("data-editorblocktype", "").lower().endswith("formfield")
            or inspector.nodes[parent].attrs.get("data-editorblocktype", "").lower() in {"consent", "topic", "captcha", "recaptcha"}
            for parent in ancestors(inspector, control_index)
            if is_descendant(inspector, parent, form_index) or parent == form_index
        ):
            continue
        findings.append(
            Finding(
                "error",
                "unmanaged-control",
                f"Control {control.attrs.get('name') or control.tag!r} is not inside a generated field, consent, or CAPTCHA block.",
                control.line,
            )
        )

    consent_blocks = [
        node
        for _, node in form_nodes
        if node.attrs.get("data-editorblocktype", "").lower() in {"consent", "topic"}
    ]
    for block in consent_blocks:
        block_type = block.attrs.get("data-editorblocktype", "").lower()
        required_attrs = ["data-purposeid", "data-channels"]
        if block_type == "topic":
            required_attrs.append("data-topicid")
        for attribute in required_attrs:
            value = block.attrs.get(attribute, "")
            if not value or is_placeholder(value):
                findings.append(
                    Finding(
                        "error",
                        "consent-config",
                        f"{block_type.title()} block needs a target-environment {attribute} value.",
                        block.line,
                    )
                )

    has_captcha = any(
        node.attrs.get("data-editorblocktype", "").lower() in {"captcha", "recaptcha"}
        for _, node in form_nodes
    )
    if not has_captcha:
        findings.append(
            Finding(
                "warning",
                "recaptcha",
                "No reCAPTCHA Designer block was found. Add one before publishing a public form.",
                form.line,
            )
        )
    for index, node in form_nodes:
        if node.attrs.get("data-editorblocktype", "").lower() in {"captcha", "recaptcha"}:
            if not descendants(inspector, index):
                findings.append(Finding("warning", "empty-captcha",
                    "The CAPTCHA block is empty; a marker alone does not prove bot protection. Verify the generated block in Dynamics.", node.line))

    has_designer_meta = any(
        node.tag == "meta"
        and node.attrs.get("type") == "xrm/designer/setting"
        and node.attrs.get("name") == "type"
        and node.attrs.get("value") == "marketing-designer-content-editor-document"
        for node in inspector.nodes
    )
    if not has_designer_meta:
        findings.append(
            Finding(
                "warning",
                "designer-meta",
                "Designer drag-and-drop meta tag not found; the simplified full-page editor may be used.",
            )
        )

    for index, node in enumerate(inspector.nodes):
        if node.tag == "script" and any(
            inspector.nodes[parent].tag == "head" for parent in ancestors(inspector, index)
        ):
            findings.append(
                Finding(
                    "warning",
                    "head-script",
                    "Current versions move head scripts to the body; verify the saved target-environment source.",
                    node.line,
                )
            )

    return findings


def validate_capture(inspector: Inspector, source: str) -> list[Finding]:
    findings = common_findings(inspector, source)
    lowered = source.lower()
    forms = [node for node in inspector.nodes if node.tag == "form"]
    if not forms:
        findings.append(Finding("error", "capture-form", "No existing form element found."))
    if not any(is_submit_control(node) for node in inspector.nodes):
        findings.append(Finding("error", "submit", "The captured page has no submit control."))

    required_tokens = {
        "FormCapture.bundle.js": "formcapture.bundle.js",
        "waitForElement": "d365mktformcapture.waitforelement",
        "serializeForm": "d365mktformcapture.serializeform",
        "submitForm": "d365mktformcapture.submitform",
    }
    for label, token in required_tokens.items():
        if token not in lowered:
            findings.append(
                Finding(
                    "error",
                    "capture-api",
                    f"Generated Form Capture integration is missing {label}.",
                )
            )

    form_ids = re.findall(r"\bFormId\s*:\s*['\"]([^'\"]+)['\"]", source)
    api_urls = re.findall(r"\bFormApiUrl\s*:\s*['\"]([^'\"]+)['\"]", source)
    if not form_ids or any(is_placeholder(value) for value in form_ids):
        findings.append(
            Finding(
                "error",
                "capture-form-id",
                "Use the FormId from the generated target-environment capture snippet.",
            )
        )
    if not api_urls or any(is_placeholder(value) for value in api_urls):
        findings.append(
            Finding(
                "error",
                "capture-api-url",
                "Use the FormApiUrl from the generated target-environment capture snippet.",
            )
        )

    mapping_names = re.findall(
        r"\bFormFieldName\s*:\s*['\"]([^'\"]+)['\"]", source
    )
    if not mapping_names:
        findings.append(
            Finding("error", "capture-mappings", "No FormFieldName mappings found.")
        )
    control_names = {
        node.attrs["name"]
        for node in inspector.nodes
        if node.tag in {"input", "select", "textarea"} and node.attrs.get("name")
    }
    for name in mapping_names:
        if name not in control_names:
            findings.append(
                Finding(
                    "error",
                    "capture-control",
                    f"FormFieldName {name!r} does not match an existing control name.",
                )
            )

    dataverse_names = re.findall(
        r"\bDataverseFieldName\s*:\s*['\"]([^'\"]+)['\"]", source
    )
    if mapping_names and len(dataverse_names) < len(mapping_names):
        findings.append(
            Finding(
                "warning",
                "capture-dataverse-mapping",
                "Some form-field mappings do not include a DataverseFieldName; verify generated value mappings and unmapped fields.",
            )
        )

    if "preventdefault(" not in lowered:
        findings.append(
            Finding(
                "warning",
                "submission-ownership",
                "No preventDefault call found. Confirm whether original or dual submission is intentional.",
            )
        )
    if "await d365mktformcapture.submitform" not in lowered and not re.search(
        r"d365mktformcapture\.submitForm\s*\([^;]+\)\s*\.(then|catch)",
        source,
        flags=re.IGNORECASE | re.DOTALL,
    ):
        findings.append(
            Finding(
                "warning",
                "capture-promise",
                "Handle the submitForm promise before redirecting or showing success.",
            )
        )
    if "window.location" in lowered or "location.href" in lowered:
        findings.append(
            Finding(
                "warning",
                "capture-redirect",
                "Verify that navigation occurs only after submitForm and any required original destination complete.",
            )
        )

    return findings


def validate_text(source: str, mode: str = "auto") -> tuple[str, list[Finding]]:
    inspector = Inspector()
    inspector.feed(source)
    inspector.close()
    resolved_mode = mode
    if mode == "auto":
        lowered = source.lower()
        resolved_mode = (
            "capture"
            if "d365mktformcapture" in lowered or "formcapture.bundle.js" in lowered
            else "native"
        )
    if resolved_mode == "capture":
        return resolved_mode, validate_capture(inspector, source)
    return resolved_mode, validate_native(inspector, source)


def inspect_text(source: str) -> Inspector:
    inspector = Inspector()
    inspector.feed(source)
    inspector.close()
    return inspector


def protected_node(node: Node) -> bool:
    if node.tag in {"script", "style"}:
        return False
    return (
        node.tag in {"html", "body", "form", "meta", "link", "label", "fieldset", "legend", "option", "optgroup"}
        or node.tag in CONTROL_TAGS
        or any(key.startswith("data-") for key in node.attrs)
        or any(key in node.attrs for key in {"id", "role", "property-reference"})
    )


def protected_attrs(node: Node) -> dict[str, str]:
    # Visual overrides belong in styles/classes; every other source attribute is
    # part of the preservation contract, including unknown future metadata.
    return {key: value for key, value in node.attrs.items() if key not in {"class", "style"}}


def node_key(inspector: Inspector, index: int) -> str:
    node = inspector.nodes[index]
    parents = [
        {"tag": inspector.nodes[parent].tag, "attrs": protected_attrs(inspector.nodes[parent])}
        for parent in reversed(list(ancestors(inspector, index)))
        if protected_node(inspector.nodes[parent])
    ]
    record: dict = {"tag": node.tag, "attrs": protected_attrs(node), "parents": parents}
    if node.tag in {"option", "textarea", "label", "legend"}:
        record["text"] = " ".join(node.text.split()) if node.tag != "textarea" else node.text
    return json.dumps(record, sort_keys=True)


def compare_native(original: str, styled: str) -> list[Finding]:
    """Compare source contracts without publishing field values in diagnostics.

    This is a DOM/attribute check, not a CSS, JavaScript, or Dataverse runtime proof.
    Reordering fields is allowed; changing their owning block or option order is not.
    """
    before, after = inspect_text(original), inspect_text(styled)
    findings: list[Finding] = []
    before_nodes = Counter(node_key(before, i) for i, n in enumerate(before.nodes) if protected_node(n))
    after_nodes = Counter(node_key(after, i) for i, n in enumerate(after.nodes) if protected_node(n))
    removed, added = before_nodes - after_nodes, after_nodes - before_nodes
    if removed:
        findings.append(Finding("error", "contract-removed",
            f"{sum(removed.values())} protected source nodes were removed or changed. Check fields, mappings, validation, consent, IDs, and parent relationships."))
    if added:
        findings.append(Finding("error", "contract-added",
            f"{sum(added.values())} protected nodes were added or changed. A styling pass must preserve the original form contract."))

    def classes(inspector: Inspector) -> Counter:
        result: Counter = Counter()
        for i, node in enumerate(inspector.nodes):
            if node.tag not in {"script", "style"}:
                result.update((node_key(inspector, i), name) for name in class_names(node))
        return result

    if classes(before) - classes(after):
        findings.append(Finding("error", "class-removed",
            "Existing classes were removed or moved from protected nodes. Keep generated CSS and JavaScript hooks; add styling classes instead."))

    def copy_text(inspector: Inspector) -> Counter:
        # Compare each source region independently so intact blocks can move and
        # decorative wrappers can be added without changing their wording.
        return Counter(
            (node_key(inspector, index), " ".join(node.text.split()))
            for index, node in enumerate(inspector.nodes)
            if node.tag in {"title", "button"}
            or node.attrs.get("data-editorblocktype", "").lower() == "text"
        )

    if copy_text(before) != copy_text(after):
        findings.append(Finding("error", "source-text-changed",
            "Generated text blocks, document title, or button wording changed. Preserve source copy during styling."))

    def options(inspector: Inspector) -> dict[str, list[dict]]:
        return {
            node_key(inspector, i): [
                {"attrs": protected_attrs(child), "text": " ".join(child.text.split())}
                for _, child in descendants(inspector, i) if child.tag == "option"
            ]
            for i, node in enumerate(inspector.nodes) if node.tag == "select"
        }

    if options(before) != options(after):
        findings.append(Finding("error", "options-changed",
            "Select options, their order, labels, values, or default selection changed."))

    def scripts(inspector: Inspector) -> list[tuple]:
        result = []
        preceding: Counter = Counter()
        for index, node in enumerate(inspector.nodes):
            if protected_node(node):
                preceding[node_key(inspector, index)] += 1
            if node.tag == "script":
                parents = [
                    (inspector.nodes[parent].tag, protected_attrs(inspector.nodes[parent]))
                    for parent in reversed(list(ancestors(inspector, index)))
                    if protected_node(inspector.nodes[parent])
                ]
                result.append((node.attrs, node.text.strip(), parents, sorted(preceding.items())))
        return result

    if scripts(before) != scripts(after):
        findings.append(Finding("error", "scripts-changed",
            "Scripts, script attributes, placement, or execution order changed. Preserve existing behavior during restyling."))

    def stylesheet_key(node: Node) -> tuple | None:
        if node.tag == "style":
            return (node.tag, json.dumps(node.attrs, sort_keys=True), node.text)
        if node.tag == "link" and "stylesheet" in node.attrs.get("rel", "").lower().split():
            return (node.tag, json.dumps(node.attrs, sort_keys=True), "")
        return None

    expected_style_order = [key for n in before.nodes if (key := stylesheet_key(n)) is not None]
    original_styles = Counter(expected_style_order)
    remaining_styles = original_styles.copy()
    new_styles: list[Node] = []
    retained_style_order: list[tuple] = []
    last_retained_style = -1
    first_new_style = len(after.nodes)
    for index, node in enumerate(after.nodes):
        key = stylesheet_key(node)
        if key is None:
            continue
        if remaining_styles[key]:
            remaining_styles[key] -= 1
            retained_style_order.append(key)
            last_retained_style = index
        else:
            if node.tag == "style":
                new_styles.append(node)
            first_new_style = min(first_new_style, index)
    if +remaining_styles:
        findings.append(Finding("error", "stylesheet-changed",
            "An original stylesheet was removed or edited. Keep generated CSS intact and append scoped overrides."))
    if retained_style_order != expected_style_order or first_new_style < last_retained_style:
        findings.append(Finding("error", "stylesheet-order",
            "Preserve the original stylesheet order and place new overrides after the original styles."))

    # A deliberately conservative check for common global-selector mistakes.
    # Browser checks still need to establish cascade, geometry, and accessibility.
    for node in new_styles:
        css = re.sub(r"/\*.*?\*/", "", node.text, flags=re.DOTALL)
        for match in re.finditer(r"([^{}]+)\{", css):
            selector = match.group(1).rsplit(";", 1)[-1].strip()
            if selector.startswith("@"):
                continue
            if any(not re.match(r"^(?:form)?\.marketingForm(?=$|[.#:\s>+~\[])", part.strip()) for part in selector.split(",")):
                findings.append(Finding("warning", "css-scope",
                    "A new CSS selector is not rooted at .marketingForm. Scope every selector arm to the form; inspect complex at-rules manually.", node.line))
                break

    normalize_doctype = lambda value: " ".join(value.lower().split())
    if normalize_doctype(before.doctype) != normalize_doctype(after.doctype):
        findings.append(Finding("error", "doctype-changed", "Preserve the source document doctype."))
    return findings


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run local preflight checks on a native Customer Insights form or Form Capture page."
    )
    parser.add_argument("path", type=Path, help="HTML file to inspect")
    parser.add_argument("--original", type=Path, help="Untouched native Dynamics export to compare against the styled HTML")
    parser.add_argument(
        "--mode", choices=("auto", "native", "capture"), default="auto"
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    parser.add_argument(
        "--strict", action="store_true", help="Return nonzero when warnings exist"
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if not args.path.is_file():
        print(f"ERROR file: {args.path} does not exist or is not a file.", file=sys.stderr)
        return 2

    source = args.path.read_text(encoding="utf-8")
    mode, findings = validate_text(source, args.mode)
    original_findings: list[Finding] = []
    source_findings: list[Finding] = []
    if args.original:
        if mode != "native" or not args.original.is_file():
            print("ERROR original: comparison requires an existing native-form export.", file=sys.stderr)
            return 2
        original = args.original.read_text(encoding="utf-8")
        original_mode, original_findings = validate_text(original, "auto")
        if original_mode != "native":
            print("ERROR original: Form Capture pages are not native-form styling inputs.", file=sys.stderr)
            return 2
        baseline = Counter((item.severity, item.code, item.message) for item in original_findings)
        introduced: list[Finding] = []
        for item in findings:
            key = (item.severity, item.code, item.message)
            if baseline[key]:
                source_findings.append(item)
                baseline[key] -= 1
            else:
                introduced.append(item)
        findings = introduced + compare_native(original, source)
    errors = sum(item.severity == "error" for item in findings)
    warnings = sum(item.severity == "warning" for item in findings)
    payload = {
        "file": str(args.path),
        "mode": mode,
        "original": str(args.original) if args.original else None,
        "findings": [asdict(item) for item in findings],
        "original_findings": [asdict(item) for item in original_findings],
        "source_findings": [asdict(item) for item in source_findings],
        "summary": {"errors": errors, "warnings": warnings},
        "source_summary": {
            "errors": sum(item.severity == "error" for item in source_findings),
            "warnings": sum(item.severity == "warning" for item in source_findings),
        },
        "scope": (
            "Local preflight only. Customer Insights must still save, pass Check content, "
            "publish, and process a verified test submission."
        ),
    }

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        for item in source_findings:
            print(f"SOURCE {item.severity.upper()} {item.code}: {item.message}")
        for item in findings:
            location = f" line {item.line}" if item.line else ""
            print(f"{item.severity.upper()} {item.code}{location}: {item.message}")
        print(
            f"SUMMARY mode={mode} errors={errors} warnings={warnings} file={args.path}"
        )
        print(f"NOTE {payload['scope']}")

    if errors or payload["source_summary"]["errors"] or (args.strict and (warnings or payload["source_summary"]["warnings"])):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
