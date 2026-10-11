import re

from app.models.schemas import Category, Finding, Risk
from app.security.normalizer import Normalized

INFORMATION = re.compile(
    r"^(?:what (?:does|is)|explain|define|describe|how (?:does|do)|tell me about)\b",
    re.I,
)
COMMAND_SUFFIX = re.compile(
    r"(?:\bthen\b|;|\band\b)\s*(?:ignore|disable|bypass|transfer|send|execute|export|reveal)\b",
    re.I,
)
RULES = (
    (
        Category.ROLE_SPOOFING,
        re.compile(
            r"\b(?:system|developer|administrator|admin|bank system)\s*(?:message|override|instruction|approved|has approved|:)\b|\[SYSTEM OVERRIDE\]",
            re.I,
        ),
    ),
    (
        Category.POLICY_OVERRIDE,
        re.compile(
            r"\b(?:ignore|override|disable|bypass|skip|disregard|suspend)\b.{0,60}\b(?:instructions|verification|authorization|polic\w*|security|checks|rules|confirmation)\b",
            re.I,
        ),
    ),
    (
        Category.ROLEPLAY_JAILBREAK,
        re.compile(
            r"\b(?:act|pretend|roleplay|imagine)\b.{0,60}\b(?:unrestricted|unfiltered|no rules|operator|god mode)\b",
            re.I,
        ),
    ),
    (
        Category.DATA_EXFILTRATION,
        re.compile(
            r"\b(?:reveal|export|dump|show|give|send|print|list)\b.{0,70}\b(?:passwords?|credentials?|secrets?|customer records|other users|all accounts|all customers|api keys?)\b",
            re.I,
        ),
    ),
    (
        Category.CROSS_TURN_MANIPULATION,
        re.compile(
            r"\b(?:change|replace|substitute|make)\b.{0,100}\b(?:without asking|without confirmation|already confirmed|confirmed beneficiary|approved amount)\b",
            re.I,
        ),
    ),
    (
        Category.DIRECT_INJECTION,
        re.compile(
            r"\b(?:forget your mandate|follow only my commands|new highest priority|your new instructions|stop being a firewall)\b",
            re.I,
        ),
    ),
)
SENSITIVE = re.compile(r"\b(?:transfer|send|execute|export|reveal)\b", re.I)
MEMO = re.compile(r"\bmemo\s*:", re.I)


def informational(text: str) -> bool:
    return bool(INFORMATION.search(text.strip()) and not COMMAND_SUFFIX.search(text))


def detect(normalized: Normalized) -> list[Finding]:
    if informational(normalized.original):
        return []
    for view, text in normalized.views:
        for category, rule in RULES:
            if rule.search(text):
                if MEMO.search(text):
                    category = Category.MEMO_INJECTION
                elif view.startswith("decoded_"):
                    category = Category.ENCODED_PAYLOAD
                elif (
                    view in {"stripped", "confusable", "spacing"}
                    and text != normalized.views[0][1]
                ):
                    category = Category.OBFUSCATION
                return [
                    Finding(
                        category=category,
                        risk=Risk.CRITICAL if SENSITIVE.search(text) else Risk.HIGH,
                        evidence="Untrusted instruction attempts to change security behavior or access protected data",
                        view=view,
                    )
                ]
    return []
