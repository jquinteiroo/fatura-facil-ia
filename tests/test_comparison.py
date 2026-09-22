from core.comparison import compare_transactions


CURRENT = [
    {"Lançamento": "IFOOD", "Categoria": "Alimentação", "Valor": 120.0},
    {"Lançamento": "UBER", "Categoria": "Transporte", "Valor": 80.0},
    {"Lançamento": "NETFLIX", "Categoria": "Assinaturas", "Valor": 30.0},
]

PREVIOUS = [
    {"Lançamento": "IFOOD", "Categoria": "Alimentação", "Valor": 100.0},
    {"Lançamento": "UBER", "Categoria": "Transporte", "Valor": 100.0},
    {"Lançamento": "NETFLIX", "Categoria": "Assinaturas", "Valor": 30.0},
]


def test_compare_totals():
    result = compare_transactions(CURRENT, PREVIOUS)
    assert result["atual"]["total"] == 230.0
    assert result["anterior"]["total"] == 230.0
    assert result["diferenca_total"] == 0.0
    assert result["percentual_total"] == 0.0


def test_compare_categories():
    result = compare_transactions(CURRENT, PREVIOUS)
    alimentacao = next(item for item in result["categorias"] if item["categoria"] == "Alimentação")
    transporte = next(item for item in result["categorias"] if item["categoria"] == "Transporte")
    assert alimentacao["diferenca"] == 20.0
    assert alimentacao["percentual"] == 20.0
    assert transporte["diferenca"] == -20.0
    assert transporte["percentual"] == -20.0


def test_compare_when_previous_is_zero():
    result = compare_transactions(
        [{"Lançamento": "Teste", "Categoria": "Outros", "Valor": 50.0}],
        [],
    )
    assert result["diferenca_total"] == 50.0
    assert result["percentual_total"] is None
