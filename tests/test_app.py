import io

from app import app


def client():
    app.config.update(TESTING=True)
    return app.test_client()


def test_health_endpoint():
    response = client().get("/health")
    assert response.status_code == 200
    assert response.get_json()["engine"] == "local"


def test_index_renders():
    response = client().get("/")
    assert response.status_code == 200
    assert b"Fatura F" in response.data


def test_compare_endpoint():
    response = client().post(
        "/comparar",
        json={
            "atual": [{"Lançamento": "A", "Categoria": "Compras", "Valor": 120}],
            "anterior": [{"Lançamento": "A", "Categoria": "Compras", "Valor": 100}],
        },
    )
    data = response.get_json()
    assert response.status_code == 200
    assert data["sucesso"] is True
    assert data["comparacao"]["diferenca_total"] == 20.0


def test_csv_upload():
    content = "Lançamento;Valor;Categoria\nIFOOD;48,90;\nUBER;20,00;\n"
    response = client().post(
        "/processar",
        data={"file": (io.BytesIO(content.encode("utf-8")), "teste.csv")},
        content_type="multipart/form-data",
    )
    data = response.get_json()
    assert response.status_code == 200
    assert data["sucesso"] is True
    assert data["total"] == 68.90
    assert len(data["dados"]) == 2


def test_reject_fake_pdf():
    response = client().post(
        "/processar",
        data={"file": (io.BytesIO(b"not a real pdf"), "fatura.pdf")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    assert "conteúdo" in response.get_json()["erro"].lower()
