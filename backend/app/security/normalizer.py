import base64
import binascii
import codecs
import re
import unicodedata
from dataclasses import dataclass
from urllib.parse import unquote

SPACED = re.compile(r"\b(?:[a-zA-Z] ){3,}[a-zA-Z]\b")
ENCODED = re.compile(
    r'\b(base64|hex|url|rot13):\s*(?:"([^"\n]{1,3000})"|([^\s]{1,3000}))', re.I
)
FUSED = re.compile(
    r"\b(ignore|disable|bypass)(verification|authorization|security)\b", re.I
)
CONFUSABLES = str.maketrans("аесорхуіΑΒΕΙΚΜΝΟΡΤΧΥ", "aecopxyiABEIKMNOPTXY")


@dataclass(frozen=True)
class Normalized:
    original: str
    views: tuple[tuple[str, str], ...]


def normalize(raw: str) -> Normalized:
    nfkc = unicodedata.normalize("NFKC", raw)
    stripped = "".join(c for c in nfkc if unicodedata.category(c) != "Cf")
    folded = stripped.translate(CONFUSABLES)
    collapsed = SPACED.sub(lambda m: m.group().replace(" ", ""), folded)
    views = [
        ("nfkc", nfkc),
        ("stripped", stripped),
        ("confusable", folded),
        ("spacing", collapsed),
    ]
    for match in ENCODED.finditer(collapsed):
        kind, value = match.group(1).lower(), match.group(2) or match.group(3)
        try:
            if kind == "base64":
                decoded = base64.b64decode(value, validate=True).decode("utf-8")
            elif kind == "hex":
                decoded = bytes.fromhex(value).decode("utf-8")
            elif kind == "url":
                decoded = unquote(value, errors="strict")
            else:
                decoded = codecs.decode(value, "rot_13")
            if len(decoded) <= 2000:
                views.append((f"decoded_{kind}", decoded))
                expanded = FUSED.sub(r"\1 \2", decoded)
                if expanded != decoded:
                    views.append((f"decoded_{kind}_spacing", expanded))
        except (ValueError, UnicodeError, binascii.Error):
            continue
    return Normalized(raw, tuple(views))
