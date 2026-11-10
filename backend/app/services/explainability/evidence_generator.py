"""JobShield AI — Deterministic Evidence Generation Service.

Extracts verifiable textual evidence, warning indicators, reassuring organizational signals,
and missing attribute flags from incoming job postings with contextual awareness.
"""

from __future__ import annotations

import re
from typing import List, Tuple
from backend.app.schemas.explanation import WarningIndicator, ReassuringIndicator


def extract_evidence_findings(
    title: str,
    description: str,
    company_name: str = "",
    company_profile: str = "",
    requirements: str = "",
    benefits: str = "",
) -> Tuple[List[WarningIndicator], List[ReassuringIndicator], List[str]]:
    """Scan posting content for grounded warning indicators, positive indicators, and missing attributes."""
    warnings: List[WarningIndicator] = []
    reassuring: List[ReassuringIndicator] = []
    unverified: List[str] = []

    combined_text = f"{title}\n{company_name}\n{company_profile}\n{description}\n{requirements}\n{benefits}"
    lower_text = combined_text.lower()

    # =========================================================================
    # 1. CRITICAL WARNING: Upfront Fees, Onboarding Deposits & Financial Solicitations
    # =========================================================================
    fee_patterns = [
        # Explicit currency amount with fee/deposit
        (r"((?:[\$₹€£]|rs\.?|inr)\s*[0-9]+(?:,[0-9]{3})*(?:\.[0-9]{2})?\s*(?:fee|registration|deposit|training fee|onboarding fee|security deposit|activation fee|verification fee))", "Upfront Registration or Training Fee Demand"),
        # Fee keywords associated with candidate joining/process
        (r"\b(registration\s+fee|application\s+fee|training\s+(?:materials\s+)?fee|onboarding\s+fee|account\s+activation\s+fee|security\s+deposit|caution\s+deposit|document\s+verification\s+fee|laptop\s+deposit|equipment\s+deposit)\b", "Mandatory Upfront Candidate Fee or Deposit"),
        # Refundable fee promises
        (r"\b(refundable\s+(?:onboarding|registration|security|training)?\s*(?:fee|deposit)|refundable\s+after\s+first\s+(?:paycheck|month|salary))\b", "Deferred Fee Refund Promise"),
        # Demands to pay before joining
        (r"\b(pay\s+(?:before|prior to)\s+(?:joining|onboarding|starting|confirmation)|payment\s+required\s+before\s+joining)\b", "Advance Payment Required Prior to Employment"),
    ]

    for pattern, name in fee_patterns:
        match = re.search(pattern, lower_text)
        if match:
            # Contextual check: make sure this isn't describing company legal registration (e.g. "registered under Companies Act")
            matched_str = match.group(0)
            surrounding = lower_text[max(0, match.start() - 40):min(len(lower_text), match.end() + 40)]
            if "registered under" in surrounding or "company registration number" in surrounding or "cin no" in surrounding:
                continue

            start = max(0, match.start() - 30)
            end = min(len(combined_text), match.end() + 50)
            excerpt = combined_text[start:end].strip()
            warnings.append(
                WarningIndicator(
                    indicator_name=name,
                    category="financial",
                    severity="critical",
                    evidence=f"...{excerpt}...",
                    reason_for_flagging="Legitimate employers never demand job applicants pay registration, onboarding, software setup, or refundable training deposits.",
                    source_type="textual_evidence",
                )
            )
            break

    # =========================================================================
    # 2. CRITICAL WARNING: Sensitive Identity Document Demands via Informal Channels
    # =========================================================================
    doc_patterns = [
        (r"\b(?:aadhaar|pan(?:\s*card)?|passport|voter\s*id|bank\s*details|bank\s*passbook|bank\s*statement|cancelled\s*cheque)\b.*?\b(?:whatsapp|telegram|personal\s*email)\b", "Sensitive Identity Documents Requested via Informal Messaging"),
        (r"\b(?:whatsapp|telegram)\b.*?\b(?:aadhaar|pan(?:\s*card)?|passport|voter\s*id|bank\s*details|bank\s*passbook|bank\s*statement)\b", "Sensitive Identity Documents Requested via Informal Messaging"),
        (r"\b(?:share|send|submit|upload)\s+(?:your\s+)?(?:aadhaar|pan(?:\s*card)?|passport|bank\s*details|bank\s*account)\b.*?\b(?:on|via|through|to)\s+(?:whatsapp|telegram)\b", "Identity Document Submission Enforced on WhatsApp/Telegram"),
        (r"\b(?:send|submit)\s+(?:aadhaar|pan|identity\s*documents?)\s+(?:before|prior to|without)\s+(?:any\s+)?(?:interview|selection)\b", "Identity Documents Demanded Prior to Interview"),
    ]

    for pattern, name in doc_patterns:
        match = re.search(pattern, lower_text)
        if match:
            start = max(0, match.start() - 25)
            end = min(len(combined_text), match.end() + 45)
            excerpt = combined_text[start:end].strip()
            warnings.append(
                WarningIndicator(
                    indicator_name=name,
                    category="identity",
                    severity="critical",
                    evidence=f"...{excerpt}...",
                    reason_for_flagging="Demanding government identity documents (Aadhaar, PAN, Passport, Bank Details) through WhatsApp or before formal interviews creates severe identity theft and financial fraud risks.",
                    source_type="textual_evidence",
                )
            )
            break

    # =========================================================================
    # 3. CRITICAL WARNING: Untraceable / Irreversible Payment Channels
    # =========================================================================
    wire_patterns = [
        (r"\b(wire\s+transfer|moneygram|western\s+union|cryptocurrency|bitcoin|usdt|cash\s+app|send\s+money\s+via\s+upi|gpay\s+to\s+personal|phonepe\s+to\s+personal)\b", "Untraceable / Irreversible Payment Channel"),
    ]
    for pattern, name in wire_patterns:
        match = re.search(pattern, lower_text)
        if match:
            start = max(0, match.start() - 25)
            end = min(len(combined_text), match.end() + 45)
            warnings.append(
                WarningIndicator(
                    indicator_name=name,
                    category="financial",
                    severity="critical",
                    evidence=f"...{combined_text[start:end].strip()}...",
                    reason_for_flagging="Demands for wire transfers, cryptocurrency, or peer-to-peer UPI payments indicate irreversible advance-fee or money-mule operations.",
                    source_type="textual_evidence",
                )
            )
            break

    # =========================================================================
    # 4. HIGH WARNING: Bypassed Hiring, Guaranteed Placement & No Assessment
    # =========================================================================
    guarantee_patterns = [
        (r"\b(guaranteed\s+(?:job\s+confirmation|job|placement|selection|hire|employment|approval)|immediate\s+job\s+confirmation|confirmed\s+job\s+offer\s+within\s+[0-9]+\s+hours?)\b", "Guaranteed Employment or Confirmation Claim"),
        (r"\b(no\s+(?:technical\s+)?interview\s+(?:required|needed|conducted)|no\s+coding\s+assessment|direct\s+(?:hiring|selection|joining)\s+without\s+(?:an?\s+)?interview|selection\s+without\s+interview)\b", "Bypassed Hiring Assessment / No Interview Required"),
        (r"\b(earn\s+(?:[\$₹€£]|rs\.?|inr)?\s*[0-9]{3,6}\s*(?:\/|\s*per\s*)(?:week|day)\s+guaranteed|guaranteed\s+income|easy\s+money)\b", "Guaranteed Income Promise"),
    ]
    for pattern, name in guarantee_patterns:
        match = re.search(pattern, lower_text)
        if match:
            start = max(0, match.start() - 25)
            end = min(len(combined_text), match.end() + 45)
            warnings.append(
                WarningIndicator(
                    indicator_name=name,
                    category="guarantee",
                    severity="high",
                    evidence=f"...{combined_text[start:end].strip()}...",
                    reason_for_flagging="Legitimate organizations evaluate applicants through professional screening; guaranteed immediate selection without technical evaluation is a recognized scam tactic.",
                    source_type="textual_evidence",
                )
            )
            break

    # =========================================================================
    # 5. HIGH WARNING: External Encrypted Chat Redirects
    # =========================================================================
    # Avoid duplicate if already covered by document request
    has_chat_doc_warning = any(w.category == "identity" and "whatsapp" in w.indicator_name.lower() for w in warnings)
    if not has_chat_doc_warning:
        chat_patterns = [
            (r"(telegram(?::|\s+on|\s+at|\s+handle|\s+channel|\s*@)?\s*@[a-zA-Z0-9_]+|t\.me\/[a-zA-Z0-9_]+|\btelegram\b)", "Recruitment Redirected to Telegram"),
            (r"(whatsapp(?::|\s+on|\s+at|\s+number|\s*@)?\s*\+?[0-9\s\-]+|wa\.me\/[0-9]+|\bwhatsapp\b)", "Recruitment Redirected to WhatsApp"),
            (r"\b(do not email|whatsapp only|telegram only)\b", "Exclusive Off-Platform Messaging Enforced"),
        ]
        for pattern, name in chat_patterns:
            match = re.search(pattern, lower_text)
            if match:
                start = max(0, match.start() - 20)
                end = min(len(combined_text), match.end() + 40)
                warnings.append(
                    WarningIndicator(
                        indicator_name=name,
                        category="communication",
                        severity="high",
                        evidence=f"...{combined_text[start:end].strip()}...",
                        reason_for_flagging="Routing official recruitment away from corporate channels to personal messaging apps avoids corporate verification and oversight.",
                        source_type="textual_evidence",
                    )
                )
                break

    # =========================================================================
    # 6. HIGH / MEDIUM WARNING: Unrealistic Compensation for Minimal Experience
    # =========================================================================
    # Contextual check: 0-1 years / freshers paired with disproportionately high compensation
    has_fresher_exp = bool(re.search(r"\b(?:0[-–\s]+1\s+years?|0\s+years?|no\s+experience|freshers?\s+(?:can\s+apply|welcome)?)\b", lower_text))
    high_pay_match = re.search(r"(?:₹|rs\.?|inr)\s*([6-9][0-9]|1[0-9]{2})(?:,[0-9]{3})?\s*(?:-|to)\s*(?:₹|rs\.?|inr)?\s*([7-9][0-9]|1[0-9]{2}|2[0-9]{2})(?:,[0-9]{3})?\s*(?:per\s+month|\/month|\/mo|pm\b)", lower_text)
    if has_fresher_exp and high_pay_match:
        warnings.append(
            WarningIndicator(
                indicator_name="Disproportionate Compensation for Minimal Experience",
                category="compensation",
                severity="medium",
                evidence=high_pay_match.group(0),
                reason_for_flagging="Promising senior-level compensation (₹65,000–₹95,000+/month) for zero-to-one year experience without rigorous evaluation is a common bait tactic.",
                source_type="textual_evidence",
            )
        )

    # =========================================================================
    # 7. MEDIUM WARNING: Free Webmail Used for Corporate Hiring
    # =========================================================================
    webmail_match = re.search(r"([a-zA-Z0-9_.+-]+@(gmail\.com|yahoo\.com|hotmail\.com|outlook\.com|aol\.com))", lower_text)
    if webmail_match:
        warnings.append(
            WarningIndicator(
                indicator_name="Free Webmail Domain Used for Official Hiring",
                category="identity",
                severity="medium",
                evidence=webmail_match.group(1),
                reason_for_flagging="Authentic corporate recruiters communicate via registered corporate domain emails rather than disposable public webmail.",
                source_type="textual_evidence",
            )
        )

    # =========================================================================
    # 8. MEDIUM WARNING: High-Pressure Urgency & Scarcity
    # =========================================================================
    urgency_patterns = [
        (r"\b(only\s+[0-9]+\s+spots\s+left|apply\s+in\s+the\s+next\s+24\s+hours|positions\s+filling\s+fast|apply\s+within\s+24\s+hours|limited\s+(?:spots|vacancies|openings)\s+left|urgent\s+hiring|immediate\s+hiring|limited\s+vacancies)\b", "Artificial Urgency & Scarcity Pressure"),
    ]
    for pattern, name in urgency_patterns:
        match = re.search(pattern, lower_text)
        if match:
            start = max(0, match.start() - 20)
            end = min(len(combined_text), match.end() + 40)
            warnings.append(
                WarningIndicator(
                    indicator_name=name,
                    category="procedural",
                    severity="medium",
                    evidence=f"...{combined_text[start:end].strip()}...",
                    reason_for_flagging="Artificial countdowns and immediate deadlines rush job-seekers into skipping verification.",
                    source_type="textual_evidence",
                )
            )
            break

    # =========================================================================
    # 9. REASSURING / POSITIVE INDICATORS
    # =========================================================================
    # A. Corporate career portal URL
    portal_match = re.search(r"(careers\.[a-z0-9\-]+\.[a-z]{2,}|[a-z0-9\-]+\.com\/careers|[a-z0-9\-]+\.workable\.com|[a-z0-9\-]+\.greenhouse\.io|[a-z0-9\-]+\.lever\.co)", lower_text)
    if portal_match:
        reassuring.append(
            ReassuringIndicator(
                indicator_name="Recognized Corporate Career Portal",
                evidence=portal_match.group(1),
                significance="Application directs to an established applicant tracking system or verified domain.",
            )
        )

    # B. Corporate domain email
    corp_email_match = re.search(r"([a-zA-Z0-9_.+-]+@([a-zA-Z0-9-]+\.[a-zA-Z]{2,}))", lower_text)
    if corp_email_match and not any(corp_email_match.group(2).endswith(d) for d in ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com"]):
        reassuring.append(
            ReassuringIndicator(
                indicator_name="Corporate Domain Email",
                evidence=corp_email_match.group(1),
                significance="Inquiries routed through an organization-controlled enterprise email domain.",
            )
        )

    # C. Comprehensive compensation & benefits
    if re.search(r"\b(health\s+insurance|401\s*\(?k\)?|parental\s+leave|medical|dental|vision|paid\s+time\s+off|pto|stipend)\b", lower_text):
        reassuring.append(
            ReassuringIndicator(
                indicator_name="Comprehensive Compensation & Benefits",
                evidence="Posting outlines institutional benefits (insurance, retirement matching, leave, or stipend).",
                significance="Indicates established employer payroll, compliance, and human resources infrastructure.",
            )
        )

    # D. Structured professional requirements & interview process
    if re.search(r"\b(technical\s+interview|background\s+check|portfolio|code\s+review|scrum|sprint|qualifications|requirements)\b", lower_text):
        reassuring.append(
            ReassuringIndicator(
                indicator_name="Structured Professional Requirements",
                evidence="Mentions technical evaluation, background verification, or defined candidate qualifications.",
                significance="Consistent with legitimate merit-based screening processes.",
            )
        )

    # E. Explicit no-fee policy
    if re.search(r"\b(we\s+do\s+not\s+request\s+payment|no\s+fees|never\s+ask\s+for\s+money|does\s+not\s+charge\s+any\s+fee)\b", lower_text):
        reassuring.append(
            ReassuringIndicator(
                indicator_name="Explicit No-Fee Recruiting Statement",
                evidence="Employer explicitly disclaims charging any application or hiring fees.",
                significance="Affirms compliance with standard fair recruitment practices.",
            )
        )

    # F. Realistic market compensation
    hourly_match = re.search(r"\$\s*([1-9][0-9])\s*(?:\/|\s*per\s*)(?:hr|hour)", lower_text)
    if hourly_match and 15 <= int(hourly_match.group(1)) <= 75:
        reassuring.append(
            ReassuringIndicator(
                indicator_name="Realistic Market Compensation",
                evidence=hourly_match.group(0),
                significance="Stated wage falls within customary competitive intern and junior market salary bands.",
            )
        )

    # =========================================================================
    # 10. UNVERIFIED INFORMATION & MISSING DETAILS
    # =========================================================================
    if not company_name or len(company_name.strip()) < 3:
        unverified.append("Company identity is unverified or not specified in posting header.")
    if not re.search(r"\b(founded|series|headquartered|employees|locations?|offices?)\b", lower_text):
        unverified.append("No verifiable company background, founding history, or physical headquarters mentioned.")
    if not re.search(r"\b(bachelor|degree|experience|proficient|skills|requirements)\b", lower_text):
        unverified.append("Minimal candidate qualifications required; prerequisites are unusually vague.")
    if not re.search(r"\b(benefits|health|insurance|pto|401k|stipend|credit)\b", lower_text):
        unverified.append("No standard corporate benefits, insurance, or academic credits specified.")

    return warnings, reassuring, unverified
