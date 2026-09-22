from collections import defaultdict


def _positive(transactions: list[dict]) -> list[dict]:
    return [
        item for item in transactions
        if float(item.get("Valor", 0) or 0) > 0
    ]


def _summary(transactions: list[dict]) -> dict:
    txs = _positive(transactions)
    total = round(sum(float(item.get("Valor", 0) or 0) for item in txs), 2)
    categories = defaultdict(float)

    for item in txs:
        category = str(item.get("Categoria") or "Outros")
        categories[category] += float(item.get("Valor", 0) or 0)

    return {
        "total": total,
        "count": len(txs),
        "categories": {key: round(value, 2) for key, value in categories.items()},
    }


def compare_transactions(current: list[dict], previous: list[dict]) -> dict:
    current_summary = _summary(current)
    previous_summary = _summary(previous)

    current_total = current_summary["total"]
    previous_total = previous_summary["total"]
    difference = round(current_total - previous_total, 2)
    percentage = None
    if previous_total:
        percentage = round((difference / previous_total) * 100, 1)

    category_names = sorted(
        set(current_summary["categories"]) | set(previous_summary["categories"])
    )
    categories = []

    for category in category_names:
        current_value = current_summary["categories"].get(category, 0.0)
        previous_value = previous_summary["categories"].get(category, 0.0)
        delta = round(current_value - previous_value, 2)
        pct = None
        if previous_value:
            pct = round((delta / previous_value) * 100, 1)

        categories.append({
            "categoria": category,
            "atual": round(current_value, 2),
            "anterior": round(previous_value, 2),
            "diferenca": delta,
            "percentual": pct,
        })

    categories.sort(key=lambda item: abs(item["diferenca"]), reverse=True)

    largest_increase = next((item for item in categories if item["diferenca"] > 0), None)
    largest_drop = next((item for item in categories if item["diferenca"] < 0), None)

    return {
        "atual": current_summary,
        "anterior": previous_summary,
        "diferenca_total": difference,
        "percentual_total": percentage,
        "categorias": categories,
        "maior_aumento": largest_increase,
        "maior_reducao": largest_drop,
    }
