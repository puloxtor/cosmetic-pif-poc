"""
Валидиране на маркетингови претенции.
Регламент (ЕС) № 655/2013 (общи критерии) + Член 20 от 1223/2009.
"""
from __future__ import annotations
from dataclasses import dataclass
import re
from .models import Product, Claim


@dataclass
class ClaimResult:
    claim: str
    status: str          # "approved" | "blocked" | "needs_evidence"
    reason: str


# Денигриращи "free-from" претенции за законово разрешени съставки.
# Регламент 655/2013, Технически документ за претенциите — забранени,
# защото внушават, че разрешена съставка е опасна.
DENIGRATING_PATTERNS = [
    (r"\bбез\s+парабени\b", "парабени"),
    (r"\bparaben[\s-]?free\b", "parabens"),
    (r"\bбез\s+силикони\b", "силикони"),
    (r"\bsilicone[\s-]?free\b", "silicones"),
    (r"\bбез\s+алуминий\b", "алуминий"),
    (r"\bбез\s+сулфати\b", "сулфати"),
    (r"\bбез\s+SLS\b", "SLS"),
    (r"\bбез\s+SLES\b", "SLES"),
    (r"\bбез\s+феноксиетанол\b", "феноксиетанол"),
    (r"\bбез\s+консерванти\b", "консерванти"),
    (r"\bsulfate[\s-]?free\b", "sulfates"),
    (r"\bбез\s+минерални\s+масла\b", "минерални масла"),
]

# Претенции, които внушават въздействие върху растеж/възстановяване на косата —
# на ръба на медицинска претенция; изискват солидно доказателствено досие.
GROWTH_CLAIMS = [
    r"\bстимулира\s+растеж", r"\bускорява\s+растеж",
    r"\bпредотвратява\s+косопад", r"\bспира\s+косопад",
    r"\bвъзстановява\s+космен", r"\bregrow", r"\bhair\s+growth",
]

# Претенции изискващи доказателствено досие
EVIDENCE_REQUIRED = [
    r"\bхипоалергенен\b", r"\bhypoallergenic\b",
    r"\bдерматологично тестван\b", r"\bклинично доказан\b",
    r"\b\d+\s*%\b",   # всяка числова претенция
]

# Забранени медицински претенции (козметика не лекува)
MEDICAL_CLAIMS = [
    r"\bлекува\b", r"\bизлекува\b", r"\bпротивовъзпалител",
    r"\bантибактериал" , r"\bheals?\b",
]


def validate_claim(claim: Claim) -> ClaimResult:
    text = claim.text.lower()

    for pattern, substance in DENIGRATING_PATTERNS:
        if re.search(pattern, text):
            return ClaimResult(
                claim.text, "blocked",
                f"Денигрираща претенция за разрешена съставка ({substance}) — "
                f"нарушава Рег. 655/2013 (критерий 'Честност' и 'Обоснованост')."
            )

    for pattern in MEDICAL_CLAIMS:
        if re.search(pattern, text):
            return ClaimResult(
                claim.text, "blocked",
                "Медицинска претенция — извън обхвата на козметичен продукт (Чл. 20)."
            )

    for pattern in GROWTH_CLAIMS:
        if re.search(pattern, text):
            return ClaimResult(
                claim.text, "needs_evidence",
                "Претенция за растеж/възстановяване на косата — изисква солидно "
                "доказателствено досие; при внушение за лечебен ефект става "
                "медицинска (граница с Чл. 20)."
            )

    for pattern in EVIDENCE_REQUIRED:
        if re.search(pattern, text):
            return ClaimResult(
                claim.text, "needs_evidence",
                "Изисква доказателствено досие (тест/проучване) преди одобрение."
            )

    return ClaimResult(claim.text, "approved", "Съответства на общите критерии.")


def validate_all_claims(product: Product) -> list[ClaimResult]:
    return [validate_claim(c) for c in product.claims]
