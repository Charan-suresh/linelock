"""One-page text PDFs. The local extractor reads the text back out of the content stream."""

from __future__ import annotations


def make_pdf(lines: list[str]) -> bytes:
    commands: list[str] = []
    y = 780
    for line in lines:
        escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        commands.append(f"BT /F1 11 Tf 48 {y} Td ({escaped}) Tj ET")
        y -= 16
        if y < 48:
            break
    stream = ("\n".join(commands) + "\n").encode("latin-1", errors="replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Count 1 /Kids [3 0 R] >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"endstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out.extend(f"{index} 0 obj\n".encode())
        out.extend(obj)
        out.extend(b"\nendobj\n")
    xref = len(out)
    out.extend(f"xref\n0 {len(objects)+1}\n".encode())
    out.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        out.extend(f"{offset:010d} 00000 n \n".encode())
    out.extend(
        f"trailer << /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    )
    return bytes(out)


def read_pdf_lines(data: bytes) -> list[str]:
    text = data.decode("latin-1", errors="replace")
    lines: list[str] = []
    index = 0
    while True:
        start = text.find("(", index)
        if start < 0:
            break
        chars: list[str] = []
        i = start + 1
        while i < len(text):
            char = text[i]
            if char == "\\" and i + 1 < len(text):
                chars.append(text[i + 1])
                i += 2
                continue
            if char == ")":
                break
            chars.append(char)
            i += 1
        lines.append("".join(chars))
        index = i + 1
    return [line for line in lines if line.strip()]
