"""Keyword and regex lists for all skills. Keep them short and high-precision:
false positives on real jobs hurt more than misses. Matching is case-insensitive."""

# ponytail: hand-tuned lists and penalties, not learned. Upgrade path: a labelled
# dataset plus an evaluation harness before quoting any accuracy.

FREE_EMAIL_DOMAINS = {
    "gmail.com", "googlemail.com", "yahoo.com", "yahoo.in", "yahoo.co.in", "outlook.com",
    "hotmail.com", "live.com", "proton.me", "protonmail.com", "icloud.com", "rediffmail.com",
}

KNOWN_BRANDS = {
    "google", "amazon", "microsoft", "apple", "meta", "netflix", "stripe", "paypal", "oracle",
    "adobe", "ibm", "tcs", "infosys", "wipro", "accenture", "deloitte", "flipkart", "linkedin",
}

# Words scammers bolt onto a brand to build a lookalike domain (careers-stripe.com, amazonjobs.net).
JOB_AFFIXES = {"careers", "career", "jobs", "job", "hr", "hiring", "recruit", "recruitment", "talent", "work", "official"}

COMPANY_NAME_NOISE = (
    r"\b(inc|llc|ltd|limited|pvt|private|corp|corporation|co|company|technologies|technology|"
    r"solutions|services|group|careers|career|jobs|hr|hiring|recruitment)\b"
)

RISKY_SOURCES = {"whatsapp", "telegram", "email"}
MODERATED_SOURCES = {"linkedin", "indeed", "naukri", "company website"}

OFF_PLATFORM_CONTACT = [
    r"whats\s?app",
    r"telegram",
    r"(contact|message|text|reach|chat|connect)\b.{0,25}\bsignal\b",
    r"\bwa\.me/",
    r"\bt\.me/",
]

PAYMENT = [
    r"registration (fee|charge)",
    r"training (fee|charge)",
    r"processing fee",
    r"security deposit",
    r"refundable deposit",
    r"(pay|send|transfer|make)\b.{0,30}\bdeposit\b",
    r"\bdeposit (of|amount)\b.{0,10}(rs\.?|₹|inr|\$)",
    r"pay (for|towards) (your |the )?(equipment|kit|laptop|training|uniform)",
    r"(equipment|kit|starter) (fee|charge|cost)",
    r"wire transfer",
    r"western union",
    r"gift cards?",
    r"\b(crypto|bitcoin|usdt)\b",
    r"\bpay (a |the )?(small )?(fee|amount|rs\.?|₹|inr|\$)",
]

SENSITIVE_DOCS = r"(aadh?aa?r|\bpan\b( card)?|\bssn\b|social security|passport|bank (account|details)|\botp\b)"
SENSITIVE_REQUEST = [
    rf"(send|share|submit|upload|provide|forward|scan)\b.{{0,40}}{SENSITIVE_DOCS}",
    rf"{SENSITIVE_DOCS}.{{0,40}}\b(to confirm|for verification|to proceed|immediately|before (the )?interview)",
]

OVERPAYMENT = [
    r"overpa(y|id|yment)",
    r"reimburse you",
    r"refund the (difference|excess|extra|balance)",
    r"(cheque|check)\b.{0,40}\b(deposit|cash|send (back|the rest))",
]

URGENCY = [
    r"\burgent(ly)?\b",
    r"\bimmediately\b",
    r"limited (slots|seats|positions|vacancies|openings)",
    r"apply today( only)?",
    r"today only",
]

TOO_GOOD = [
    r"earn\b.{0,30}(per|/|a|every)\s*(day|week)",
    r"(rs\.?|₹|inr|\$)\s?[\d,]+\s*(/|per|a)\s*(day|week)",
    r"work from home.{0,40}\bearn",
    r"no experience.{0,80}(earn|rs\.?|₹|inr|\$)",
    r"(earn|rs\.?|₹|inr|\$).{0,80}no experience",
]

STRUCTURE_GREENS = {
    "Responsibilities are described": r"responsibilit",
    "Requirements or qualifications are listed": r"requirement|qualification",
    "Benefits are described": r"benefits|health insurance|provident fund|paid leave|\b401k\b",
}

INTERVIEW_STEP = r"\binterview"

MIN_DESCRIPTION_CHARS = 200
