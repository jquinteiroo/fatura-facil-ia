import csv
import os
from datetime import datetime

import pandas as pd
import PyPDF2
from flask import Flask, jsonify, render_template, request

from core.categories import categorize
from core.parser import parse_transactions
from core.query_engine import answer_question

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

ALLOWED_EXTENSIONS = {"pdf", "csv"}


def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _normalize_csv(file):
    last_error = None
    for kwargs in (
        {},
        {"sep": ";", "encoding": "utf-8"},
        {"sep": ";", "encoding": "latin-1"},
    ):
        try:
            file.seek(0)
            frame = pd.read_csv(file, **kwargs)
            if "Valor" in frame.columns:
                return frame
        except Exception as exc:
            last_error = exc
    raise ValueError(f'A coluna "Valor" não foi encontrada no CSV. {last_error or ""}'.strip())


def _parse_csv(file):
    frame = _normalize_csv(file)
    frame["Valor"] = (
        frame["Valor"]
        .astype(str)
        .str.replace("R$", "", regex=False)
        .str.replace(" ", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    frame["Valor"] = pd.to_numeric(frame["Valor"], errors="coerce")
    frame = frame.dropna(subset=["Valor"])

    if "Lançamento" not in frame.columns:
        for candidate in ("Descricao", "Descrição", "Estabelecimento", "description"):
            if candidate in frame.columns:
                frame["Lançamento"] = frame[candidate]
                break
    if "Lançamento" not in frame.columns:
        frame["Lançamento"] = "Lançamento"

    if "Categoria" in frame.columns:
        frame["Categoria"] = frame["Categoria"].fillna("")
        frame["Categoria"] = frame.apply(
            lambda row: row["Categoria"] if str(row["Categoria"]).strip() else categorize(str(row["Lançamento"])),
            axis=1,
        )
    else:
        frame["Categoria"] = frame["Lançamento"].astype(str).map(categorize)

    records = frame.to_dict(orient="records")
    total = round(sum(float(item.get("Valor", 0) or 0) for item in records if float(item.get("Valor", 0) or 0) > 0), 2)
    return records, total


@app.errorhandler(413)
def arquivo_muito_grande(_):
    return jsonify({"erro": "Arquivo muito grande. O limite é 10 MB."}), 413


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health")
def health():
    return jsonify({"status": "ok", "engine": "local"})


@app.route("/processar", methods=["POST"])
def processar():
    if "file" not in request.files:
        return jsonify({"erro": "Nenhum arquivo enviado."}), 400

    file = request.files["file"]
    filename = (file.filename or "").lower()

    if not filename or not _allowed_file(filename):
        return jsonify({"erro": "Formato não suportado. Envie uma fatura PDF ou CSV."}), 400

    try:
        if filename.endswith(".csv"):
            records, total = _parse_csv(file)
            return jsonify({
                "sucesso": True,
                "tipo": "csv",
                "dados": records,
                "total": total,
                "motor": "local",
            })

        reader = PyPDF2.PdfReader(file)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        if not text.strip():
            return jsonify({
                "erro": "Não consegui extrair texto desse PDF. Ele pode ser uma fatura escaneada como imagem."
            }), 422

        result = parse_transactions(text)
        if not result["transactions"]:
            return jsonify({
                "erro": (
                    "Consegui ler o PDF, mas não reconheci as transações com segurança. "
                    "Esse formato de fatura ainda precisa de um parser específico."
                ),
                "banco_detectado": result["bank"],
            }), 422

        return jsonify({
            "sucesso": True,
            "tipo": "pdf_estruturado",
            "dados": result["transactions"],
            "total": result["total"],
            "banco": result["bank"],
            "motor": "local",
        })
    except Exception as exc:
        app.logger.exception("Falha ao processar fatura")
        return jsonify({"erro": f"Não foi possível processar a fatura: {exc}"}), 500


@app.route("/chat", methods=["POST"])
def chat():
    payload = request.get_json(silent=True) or {}
    question = str(payload.get("pergunta", "")).strip()
    transactions = payload.get("transacoes")

    if not question:
        return jsonify({"resposta": "Digite uma pergunta sobre a sua fatura."}), 400
    if not isinstance(transactions, list):
        return jsonify({"resposta": "Não recebi os dados estruturados da fatura."}), 400

    return jsonify({
        "resposta": answer_question(question, transactions),
        "motor": "local",
    })


@app.route("/sugerir_banco", methods=["POST"])
def sugerir_banco():
    data = request.get_json(silent=True) or {}
    name = str(data.get("nome", "Anônimo"))[:120]
    bank = str(data.get("banco", "Não informado"))[:120]
    contact = str(data.get("contato", "Nenhum"))[:200]
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    filename = "sugestoes_bancos.csv"
    header_exists = os.path.isfile(filename)

    try:
        with open(filename, mode="a", newline="", encoding="utf-8") as output:
            writer = csv.writer(output, delimiter=";")
            if not header_exists:
                writer.writerow(["Data/Hora", "Banco Sugerido", "Nome", "Contato"])
            writer.writerow([timestamp, bank, name, contact])
        return jsonify({"sucesso": True})
    except Exception:
        app.logger.exception("Falha ao salvar sugestão")
        return jsonify({"erro": "Falha ao salvar sugestão."}), 500


if __name__ == "__main__":
    app.run(
        debug=os.environ.get("FLASK_DEBUG") == "1",
        port=int(os.environ.get("PORT", 5000)),
        host="0.0.0.0",
    )
