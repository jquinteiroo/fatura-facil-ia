from flask import Flask, render_template, request, jsonify
import pandas as pd
import google.generativeai as genai
import PyPDF2
import os
import json
import re

app = Flask(__name__)

MINHA_CHAVE_GEMINI = os.environ.get("GEMINI_API_KEY", "")
if MINHA_CHAVE_GEMINI:
    genai.configure(api_key=MINHA_CHAVE_GEMINI)
    model = genai.GenerativeModel('gemini-3-flash-preview')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/processar', methods=['POST'])
def processar():
    if 'file' not in request.files:
        return jsonify({'erro': 'Nenhum arquivo enviado'})
    
    file = request.files['file']
    filename = file.filename.lower()
    
    try:
        if filename.endswith('.csv'):
            try:
                df = pd.read_csv(file)
                if 'Valor' not in df.columns:
                    file.seek(0)
                    df = pd.read_csv(file, sep=';', encoding='utf-8')
            except:
                file.seek(0)
                df = pd.read_csv(file, sep=';', encoding='utf-8')
                
            if 'Valor' not in df.columns:
                return jsonify({'erro': 'A coluna "Valor" não foi encontrada no CSV.'})
                
            df['Valor'] = df['Valor'].astype(str).str.replace('R$', '').str.replace('.', '').str.replace(',', '.').astype(float)
            
            if 'Categoria' in df.columns:
                df['Categoria'] = df['Categoria'].fillna('OUTROS').str.upper()
            else:
                df['Categoria'] = 'OUTROS'
                
            df = df.dropna(subset=['Valor'])
            
            dados_json = df.to_dict(orient='records')
            total = df['Valor'].sum()
            
            return jsonify({'sucesso': True, 'tipo': 'csv', 'dados': dados_json, 'total': total})

        elif filename.endswith('.pdf'):
            leitor = PyPDF2.PdfReader(file)
            texto_pdf = ""
            for pagina in leitor.pages:
                texto_pdf += pagina.extract_text() + "\n"

            prompt_extracao = f"""
            Você é um assistente financeiro. Leia a fatura abaixo e extraia TODAS as transações (compras e despesas).
            Ignore pagamentos da própria fatura.
            Retorne APENAS um array JSON. Sem formatação markdown, apenas o colchete inicial e final.
            Categorias sugeridas: SUPERMERCADO, RESTAURANTE, TRANSPORTE, SERVICOS, SAUDE, EDUCACAO, ENTRETENIMENTO, COMPRAS, OUTROS.
            
            Formato OBRIGATÓRIO:
            [
              {{"Lançamento": "Nome do local", "Categoria": "NOME DA CATEGORIA", "Valor": 150.50}}
            ]
            
            Texto da fatura:
            {texto_pdf}
            """
            
            resposta_ia = model.generate_content(prompt_extracao)

            texto_limpo = resposta_ia.text.strip()
            match = re.search(r'\[.*\]', texto_limpo, re.DOTALL)
            if match:
                dados_pdf = json.loads(match.group(0))
            else:
                dados_pdf = json.loads(texto_limpo)

            total_pdf = sum(float(item.get('Valor', 0)) for item in dados_pdf)
                
            return jsonify({'sucesso': True, 'tipo': 'pdf_estruturado', 'dados': dados_pdf, 'total': total_pdf})
            
        else:
            return jsonify({'erro': 'Formato inválido. Use CSV ou PDF.'})
            
    except Exception as e:
        return jsonify({'erro': f"Erro interno ou IA falhou ao ler PDF: {str(e)}"})

@app.route('/chat', methods=['POST'])
def chat():
    dados = request.json
    pergunta = dados.get('pergunta', '')
    contexto = dados.get('contexto', '')
    resumo = dados.get('resumo', '') 
    
    if not MINHA_CHAVE_GEMINI:
         return jsonify({'resposta': 'Erro: API Key do Gemini não configurada no servidor.'})
    
    prompt = f"""
    Você é um consultor financeiro especialista. 
    REGRA DE OURO: NUNCA tente calcular totais por categoria somando os dados detalhados. Você deve usar EXCLUSIVAMENTE os totais fornecidos no 'RESUMO EXATO' abaixo.
    
    {resumo}
    
    DETALHAMENTO DE TRANSAÇÕES:
    {contexto}
    
    Pergunta do usuário: {pergunta}
    """
    
    try:
        resposta = model.generate_content(prompt)
        return jsonify({'resposta': resposta.text})
    except Exception as e:
        return jsonify({'resposta': f"Erro ao gerar resposta da IA: {str(e)}"})

if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)), host='0.0.0.0')