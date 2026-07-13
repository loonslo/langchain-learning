#!/usr/bin/env python3
"""Convert one Python source file into a minimal, Word-compatible DOCX."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import zipfile
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


SENSITIVE_PATTERNS = [
    re.compile(r"""(?i)\b(api[_-]?key|secret|password|passwd|token)\b\s*[:=]\s*["']([^"']{8,})["']"""),
    re.compile(r"""(?i)\b(openai_api_key|anthropic_api_key|access_token|refresh_token)\b\s*[:=]\s*["']([^"']{8,})["']"""),
    re.compile(r"""\bsk-[A-Za-z0-9_-]{20,}\b"""),
    re.compile(r"""\b[A-Za-z0-9_]*TOKEN[A-Za-z0-9_]*\s*=\s*["']([^"']{8,})["']"""),
]



CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>
"""


ROOT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
"""


DOCUMENT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>
"""


STYLES = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="{W_NS}">
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal">
    <w:name w:val="Normal"/>
    <w:rPr><w:rFonts w:ascii="Microsoft YaHei" w:hAnsi="Microsoft YaHei" w:eastAsia="Microsoft YaHei"/><w:sz w:val="21"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Title">
    <w:name w:val="Title"/>
    <w:basedOn w:val="Normal"/>
    <w:pPr><w:spacing w:after="240"/></w:pPr>
    <w:rPr><w:b/><w:rFonts w:ascii="Microsoft YaHei" w:hAnsi="Microsoft YaHei" w:eastAsia="Microsoft YaHei"/><w:sz w:val="36"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Code">
    <w:name w:val="Code"/>
    <w:basedOn w:val="Normal"/>
    <w:pPr><w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/><w:ind w:left="180"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas" w:eastAsia="Microsoft YaHei"/><w:sz w:val="18"/><w:color w:val="202830"/></w:rPr>
  </w:style>
</w:styles>
"""


def scan_for_literal_credentials(source_text: str) -> None:
    for lineno, line in enumerate(source_text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        for pattern in SENSITIVE_PATTERNS:
            if pattern.search(line):
                raise ValueError(
                    "Possible literal credential in source "
                    f"at line {lineno}. Create a redacted attachment only after user approval."
                )


def paragraph(text: str, style: str) -> str:
    text_node = f'<w:t xml:space="preserve">{escape(text)}</w:t>' if text else ""
    return f'<w:p><w:pPr><w:pStyle w:val="{style}"/></w:pPr><w:r>{text_node}</w:r></w:p>'


def build_document(title: str, source_name: str, lines: list[str]) -> str:
    body = [paragraph(title, "Title"), paragraph(f"源文件：{source_name}", "Normal"), paragraph("", "Normal")]
    body.extend(paragraph(line, "Code") for line in lines)
    body.append(
        '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
        '<w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134" '
        'w:header="708" w:footer="708" w:gutter="0"/></w:sectPr>'
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{W_NS}"><w:body>{"".join(body)}</w:body></w:document>'
    )


def verify_docx(path: Path, expected_lines: list[str]) -> None:
    with zipfile.ZipFile(path) as archive:
        required = {"[Content_Types].xml", "_rels/.rels", "word/document.xml", "word/styles.xml"}
        missing = required.difference(archive.namelist())
        if missing:
            raise ValueError(f"DOCX missing package parts: {sorted(missing)}")
        root = ET.fromstring(archive.read("word/document.xml"))

    ns = {"w": W_NS}
    actual_lines = []
    for node in root.findall(".//w:body/w:p", ns):
        style = node.find("./w:pPr/w:pStyle", ns)
        if style is None or style.attrib.get(f"{{{W_NS}}}val") != "Code":
            continue
        actual_lines.append("".join(part.text or "" for part in node.findall(".//w:t", ns)))
    if actual_lines != expected_lines:
        raise ValueError(f"DOCX code verification failed: expected {len(expected_lines)} lines, got {len(actual_lines)}")


def convert(source: Path, output: Path, title: str) -> None:
    source_text = source.read_text(encoding="utf-8")
    scan_for_literal_credentials(source_text)
    lines = source_text.splitlines()
    output.parent.mkdir(parents=True, exist_ok=True)
    document_xml = build_document(title, source.name, lines)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", CONTENT_TYPES)
        archive.writestr("_rels/.rels", ROOT_RELS)
        archive.writestr("word/document.xml", document_xml)
        archive.writestr("word/styles.xml", STYLES)
        archive.writestr("word/_rels/document.xml.rels", DOCUMENT_RELS)
    verify_docx(output, lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="UTF-8 Python source file")
    parser.add_argument("--output", required=True, type=Path, help="Destination .docx path")
    parser.add_argument("--title", required=True, help="Word document title")
    args = parser.parse_args()
    if args.input.suffix.lower() != ".py":
        raise ValueError("Input must be a .py file")
    if args.output.suffix.lower() != ".docx":
        raise ValueError("Output must be a .docx file")
    convert(args.input.resolve(), args.output.resolve(), args.title)
    print(f"Created and verified: {args.output.resolve()}")


if __name__ == "__main__":
    main()
