"""Per-posting features beyond the skill list: work mode, pay, seniority, location, employer.

All rules are plain regular expressions over the cleaned posting text. They measure what a posting
*says*, not what is true: "remote" means the word appears in a non-negated way, "has_salary" means a
pay figure is printed. Shares of these flags are descriptive statistics, not validated forecasts.
"""

import re

FLAGS = re.IGNORECASE

# ----------------------------------------------------------------- work mode
_REMOTE = re.compile(r"\bremote(?:ly)?\b", FLAGS)
_NOT_REMOTE = re.compile(
    r"\b(?:no|not|non|without|never)[\s-]+(?:fully[\s-]+)?remote\b"
    r"|\bremote(?:\s+work)?\s*(?:is\s+)?(?:not|n't)\b|\bremote\s*[:=]\s*(?:no|none|not)\b", FLAGS)
_ONSITE = re.compile(r"\bon[\s-]?site\b|\bin[\s-]?office\b|\boffice[\s-]based\b", FLAGS)
_HYBRID = re.compile(r"\bhybrid\b", FLAGS)

# ----------------------------------------------------------------------- pay
_SEP = r"\s?(?:-|–|—|to)\s?"
_USD_K_RANGE = re.compile(r"(?<![A-Za-z])\$\s?(\d{2,3}(?:\.\d)?)\s?[kK]?" + _SEP + r"\$?\s?(\d{2,3}(?:\.\d)?)\s?[kK]\b")
_USD_K = re.compile(r"(?<![A-Za-z])\$\s?(\d{2,3}(?:\.\d)?)\s?[kK]\b")
_USD_COMMA_RANGE = re.compile(r"(?<![A-Za-z])\$\s?(\d{2,3}),(\d{3})(?!,\d)" + _SEP + r"\$?\s?(\d{2,3}),(\d{3})(?!,\d)")
_USD_COMMA = re.compile(r"(?<![A-Za-z])\$\s?(\d{2,3}),(\d{3})(?!,\d)")
_OTHER_PAY = re.compile(r"(?:£|€|CA?\$|A\$)\s?\d{2,3}(?:,\d{3}|\s?[kK]\b)|\b\d{2,3}\s?[kK]" + _SEP + r"\d{2,3}\s?[kK]\b"
                        r"|\b\d{2,3}\s?[kK]\s?(?:USD|EUR|GBP|CAD)\b", FLAGS)
SALARY_MIN_K, SALARY_MAX_K = 30.0, 700.0           # plausible annual USD range, in thousands

# ----------------------------------------------------------------- other flags
_EQUITY = re.compile(r"\b(?:equity|stock[\s-]options?|esop|rsus?)\b", FLAGS)
_VISA = re.compile(r"\bvisa\b|\bsponsor(?:ship|ing|s)?\b", FLAGS)
_SENIOR = re.compile(
    r"\b(?:senior|sr\b\.?|principal|architect|tech(?:nical)?\s+lead|team\s+lead|engineering\s+manager|head\s+of|director"
    r"|staff\s+(?:software|engineer|developer|scientist|ml|data|backend|frontend)"
    r"|lead\s+(?:software|engineer|developer|designer|data|backend|frontend|ml|product|full))", FLAGS)
_JUNIOR = re.compile(r"\b(?:junior|jr\b\.?|entry[\s-]level|new[\s-]grads?|recent\s+graduates?|early[\s-]career|apprentice)", FLAGS)
_INTERN = re.compile(r"\binterns?\b|\binternships?\b|\bco-?op\b", FLAGS)
_FULLTIME = re.compile(r"full[\s-]?time", FLAGS)
_PARTTIME = re.compile(r"part[\s-]?time", FLAGS)
_CONTRACT = re.compile(r"(?<!smart )\bcontract(?:or|ors|ing)?\b|\bfreelance\b", FLAGS)

# ------------------------------------------------------------------- location
# (city, region, aliases). Alias syntax as in taxonomy: plain = case-insensitive whole word, "cs:" = case-sensitive regex.
NA, EU, APAC = "NA", "EU", "APAC"
CITIES = [
    ("San Francisco", NA, ["san francisco", "bay area", "silicon valley", "palo alto", "mountain view", "sunnyvale", "menlo park",
                           "san mateo", "redwood city", "cs:SF", "south san francisco"]),
    ("New York", NA, ["new york", "nyc", "brooklyn", "manhattan", "cs:NY"]),
    ("Seattle", NA, ["seattle", "bellevue", "redmond"]),
    ("Boston", NA, ["boston", "cambridge, ma"]),
    ("Austin", NA, ["austin"]),
    ("Los Angeles", NA, ["los angeles", "santa monica", "cs:LA"]),
    ("Chicago", NA, ["chicago"]),
    ("Denver", NA, ["denver", "boulder"]),
    ("Portland", NA, ["portland"]),
    ("Washington DC", NA, ["washington, dc", "washington dc", "cs:DC"]),
    ("San Diego", NA, ["san diego"]),
    ("Atlanta", NA, ["atlanta"]),
    ("Toronto", NA, ["toronto"]),
    ("Vancouver", NA, ["vancouver"]),
    ("Montreal", NA, ["montreal", "montréal"]),
    ("London", EU, ["london"]),
    ("Berlin", EU, ["berlin"]),
    ("Amsterdam", EU, ["amsterdam"]),
    ("Paris", EU, ["paris"]),
    ("Dublin", EU, ["dublin"]),
    ("Zurich", EU, ["zurich", "zürich"]),
    ("Munich", EU, ["munich", "münchen"]),
    ("Barcelona", EU, ["barcelona"]),
    ("Stockholm", EU, ["stockholm"]),
    ("Copenhagen", EU, ["copenhagen"]),
    ("Lisbon", EU, ["lisbon"]),
    ("Madrid", EU, ["madrid"]),
    ("Vienna", EU, ["vienna"]),
    ("Singapore", APAC, ["singapore"]),
    ("Bangalore", APAC, ["bangalore", "bengaluru"]),
    ("Sydney", APAC, ["sydney"]),
    ("Melbourne", APAC, ["melbourne"]),
    ("Tokyo", APAC, ["tokyo"]),
    ("Hong Kong", APAC, ["hong kong"]),
    ("Việt Nam", APAC, ["vietnam", "ho chi minh", "hanoi", "saigon", "da nang"]),
]
# countries / regions give a region even when no city is named
COUNTRIES = [
    (NA, ["cs:USA", "cs:US", "united states", "canada"]),
    (EU, ["europe", "cs:UK", "united kingdom", "germany", "netherlands", "france", "spain", "poland", "switzerland", "sweden", "ireland"]),
    (APAC, ["india", "australia", "japan", "singapore", "china", "asia"]),
]
HEADER_CHARS = 250                                  # location is announced at the start of a posting


def _alias(alias):
    if alias.startswith("cs:"):
        return re.compile(r"(?<![\w.])" + alias[3:] + r"(?![\w])")
    return re.compile(r"(?<![\w])" + re.escape(alias) + r"(?![\w])", FLAGS)


_CITY_PATTERNS = [(city, region, [_alias(a) for a in aliases]) for city, region, aliases in CITIES]
_COUNTRY_PATTERNS = [(region, [_alias(a) for a in aliases]) for region, aliases in COUNTRIES]


def locate(text):
    """(city, region) from the first HEADER_CHARS characters; city is None when only a country/region is named."""
    head = text[:HEADER_CHARS]
    best = None
    for city, region, patterns in _CITY_PATTERNS:
        for p in patterns:
            m = p.search(head)
            if m and (best is None or m.start() < best[0]):
                best = (m.start(), city, region)
    if best:
        return best[1], best[2]
    for region, patterns in _COUNTRY_PATTERNS:
        if any(p.search(head) for p in patterns):
            return None, region
    return None, "UNKNOWN"


# ------------------------------------------------------------------- employer
_PAREN = re.compile(r"\([^)]*\)|\[[^\]]*\]")
_URL = re.compile(r"https?://\S+|www\.\S+")
_WS = re.compile(r"\s+")
# some postings start with the job title or work mode instead of the company name
_NOT_COMPANY = re.compile(r"engineer|developer|designer|manager|scientist|analyst|architect|devops|\bsre\b|intern\b|remote|on-?site|"
                          r"full[\s-]?time|part[\s-]?time|hiring|looking for|\bjobs?\b|\bwe\b|\bis\b|\bare\b", FLAGS)


def company_of(text):
    """First field of a 'Company | Location | ...' posting, or None when the posting is not in that format."""
    if text.count("|") < 2:
        return None
    first = _WS.sub(" ", _URL.sub(" ", _PAREN.sub(" ", text.split("|", 1)[0]))).strip(" -–—:·•*,")
    if not first or len(first) > 40 or len(first.split()) > 5 or _NOT_COMPANY.search(first):
        return None
    return first


# ----------------------------------------------------------------------- pay
def salary_usd_k(text):
    """Midpoint of the first annual USD figure in thousands (e.g. '$120k-$160k' -> 140.0), or None."""
    candidates = []
    for priority, (rx, kind) in enumerate(((_USD_K_RANGE, "range_k"), (_USD_K, "single_k"),
                                           (_USD_COMMA_RANGE, "range_c"), (_USD_COMMA, "single_c"))):
        m = rx.search(text)
        if not m:
            continue
        g = m.groups()
        if kind == "range_k":
            value = (float(g[0]) + float(g[1])) / 2
        elif kind == "single_k":
            value = float(g[0])
        elif kind == "range_c":
            value = (float(g[0]) * 1000 + float(g[1]) + float(g[2]) * 1000 + float(g[3])) / 2000
        else:
            value = (float(g[0]) * 1000 + float(g[1])) / 1000
        candidates.append((m.start(), priority, value))    # earliest figure wins; ranges beat single figures at the same spot
    if not candidates:
        return None
    value = min(candidates)[2]
    return value if SALARY_MIN_K <= value <= SALARY_MAX_K else None


def extract_features(text):
    """All per-posting features for one cleaned posting text."""
    remote = bool(_REMOTE.search(text)) and not _NOT_REMOTE.search(text)
    usd = salary_usd_k(text)
    city, region = locate(text)
    return {
        "is_remote": remote, "is_onsite": bool(_ONSITE.search(text)), "is_hybrid": bool(_HYBRID.search(text)),
        "has_salary": usd is not None or bool(_OTHER_PAY.search(text)), "salary_usd_k": usd,
        "has_equity": bool(_EQUITY.search(text)), "has_visa": bool(_VISA.search(text)),
        "is_senior": bool(_SENIOR.search(text)), "is_junior": bool(_JUNIOR.search(text)), "is_intern": bool(_INTERN.search(text)),
        "is_fulltime": bool(_FULLTIME.search(text)), "is_parttime": bool(_PARTTIME.search(text)), "is_contract": bool(_CONTRACT.search(text)),
        "city": city, "region": region, "company": company_of(text), "n_chars": len(text),
    }
