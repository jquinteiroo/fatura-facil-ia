import re
from typing import Iterable

from core.categories import categorize

MONTHS = {
    "JAN": 1, "FEV": 2, "MAR": 3, "ABR": 4, "MAI": 5, "JUN": 6,
    "JUL": 7, "AGO": 8, "SET": 9, "OUT": 10, "NOV": 11, "DEZ": 12,
}

DEFAULT_IGNORED_TERMS = (
    "PAGAMENTO DE FATURA", "PAGAMENTO RECEBIDO", "SALDO ANTERIOR",
    "TOTAL DA FATURA", "TOTAL A PAGAR", "PAGAMENTO MINIMO", "PAGAMENTO MÍNIMO",
    "LIMITE DISPONIVEL", "LIMITE DISPONÍVEL", "LIMITE TOTAL",
    "MELHOR DIA DE COMPRA", "ENCARGOS", "JUROS", "MULTA", "IOF",
)

DATE_PATTERNS = (
    re.compile(r"^(?P<day>\d{1,2})[/-](?P<month>\d{1,2})(?:[/-](?P<year>\d{2,4}))?\s*"),
    re.compile(
        r"^(?P<day>\d{1,2})\s+(?P<month_name>JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ)"
        r"(?:\s+(?P<year>\d{2,4}))?\s*",
        re.I,
    ),
)

AMOUNT_AT_END = re.compile(
    r"(?P<sign>-)?\s*(?:R\$\s*)?"
    r"(?P<amount>\d{1,3}(?:\.\d{3})*,\d{2}|\d+,\d{2}|\d+\.\d{2})"
    r"(?:\s*(?P<credit>[CD]))?\s*$",
    re.I,
)

INSTALLMENT_PATTERN = re.compile(
    r"(?:PARC(?:ELA)?\s*)?(?P<current>\d{1,2})\s*/\s*(?P<total>\d{1,2})",
    re.I,
)


def parse_amount(raw: str) -> float:
    value = (raw or "").replace("R$", "").replace(" ", "").strip()
    if not value:
        raise ValueError("valor vazio")

    negative = value.startswith("-") or (value.startswith("(") and value.endswith(")"))
    value = value.strip("()-")

    if "," in value:
        value = value.replace(".", "").replace(",", ".")
    elif value.count(".") > 1:
        value = value.replace(".", "")

    parsed = float(value)
    return -parsed if negative else parsed


def extract_date(line: str):
    for pattern in DATE_PATTERNS:
        match = pattern.match(line)
        if not match:
            continue

        groups = match.groupdict()
        month = int(groups["month"]) if groups.get("month") else MONTHS[groups["month_name"].upper()]
        year = groups.get("year")
        year_value = int(year) if year else None
        if year_value is not None and year_value < 100:
            year_value += 2000

        return {
            "day": int(groups["day"]),
            "month": month,
            "year": year_value,
            "end": match.end(),
        }
    return None


def _should_ignore(line: str, extra_ignored_terms: tuple[str, ...]) -> bool:
    upper = line.upper()
    return any(term in upper for term in DEFAULT_IGNORED_TERMS + extra_ignored_terms)


def _clean_description(text: str) -> str:
    text = INSTALLMENT_PATTERN.sub("", text)
    text = re.sub(r"\bCOMPRA\s+(?:NO|NA|EM)\s+", "", text, flags=re.I)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip(" -–—|")


def candidate_lines(lines: Iterable[str]) -> list[str]:
    cleaned = [re.sub(r"\s+", " ", line).strip() for line in lines if line and line.strip()]
    candidates: list[str] = []

    for index, line in enumerate(cleaned):
        candidates.append(line)
        if not extract_date(line) or AMOUNT_AT_END.search(line):
            continue

        combined = line
        for offset in (1, 2):
            next_index = index + offset
            if next_index >= len(cleaned):
                break
            next_line = cleaned[next_index]
            if offset > 1 and extract_date(next_line):
                break
            combined = f"{combined} {next_line}"
            candidates.append(combined)
            if AMOUNT_AT_END.search(combined):
                break

    return candidates


def parse_standard(
    text: str,
    bank: str,
    *,
    extra_ignored_terms: tuple[str, ...] = (),
    replacements: tuple[tuple[str, str], ...] = (),
) -> list[dict]:
    transactions: list[dict] = []
    seen = set()

    for candidate in candidate_lines((text or "").splitlines()):
        line = candidate
        for old, new in replacements:
            line = line.replace(old, new)

        if _should_ignore(line, extra_ignored_terms):
            continue

        date_info = extract_date(line)
        if not date_info:
            continue

        amount_match = AMOUNT_AT_END.search(line)
        if not amount_match:
            continue

        try:
            amount = parse_amount(amount_match.group("amount"))
        except ValueError:
            continue

        if amount_match.group("sign") or (amount_match.group("credit") or "").upper() == "C":
            amount = -abs(amount)

        prefix = line[:amount_match.start()].strip()
        description_source = prefix[date_info["end"]:].strip()
        if len(description_source) < 2:
            continue

        installment_match = INSTALLMENT_PATTERN.search(description_source)
        installment_current = int(installment_match.group("current")) if installment_match else None
        installment_total = int(installment_match.group("total")) if installment_match else None
        description = _clean_description(description_source)
        if not description or description.upper() in {"TOTAL", "SUBTOTAL"}:
            continue

        transaction = {
            "Lançamento": description,
            "Categoria": categorize(description),
            "Valor": round(amount, 2),
            "Banco": bank,
            "ParcelaAtual": installment_current,
            "ParcelasTotal": installment_total,
            "Dia": date_info["day"],
            "Mes": date_info["month"],
            "Ano": date_info["year"],
        }

        signature = (
            transaction["Dia"], transaction["Mes"], transaction["Ano"],
            transaction["Lançamento"].upper(), transaction["Valor"],
        )
        if signature in seen:
            continue
        seen.add(signature)
        transactions.append(transaction)

    return transactions
