import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
import os

# Puxa a chave do "cofre" do Render (Variáveis de Ambiente)
MINHA_CHAVE_GEMINI = os.environ.get("GEMINI_API_KEY", "")
st.set_page_config(page_title="Smart Fatura IA", page_icon="💳", layout="wide")

# ==========================================
# 2. SEU LAYOUT E DESIGN (O HTML que você gerou)
# ==========================================
st.markdown("""
<style>
    /* Importando Inter (similar à Proxima Nova para web) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* Reset de Fundo e Fonte idêntico ao seu HTML */
    .stApp, header[data-testid="stHeader"] { 
        background-color: #403A2E !important; 
        font-family: 'Inter', sans-serif !important;
        color: #BFBAB0;
    }

    /* O Card Gigante do "Total da Fatura" (Classe .glass do seu HTML) */
    div[data-testid="metric-container"] {
        background: rgba(74, 67, 53, 0.4) !important;
        backdrop-filter: blur(8px) !important;
        border: 1px solid rgba(217, 189, 156, 0.3) !important;
        border-radius: 32px !important;
        padding: 40px !important;
        text-align: left !important;
        box-shadow: none !important;
    }
    
    /* Textos do Card */
    div[data-testid="metric-container"] label {
        color: #D9BD9C !important;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-size: 0.9rem !important;
        font-weight: 600;
    }
    div[data-testid="metric-container"] div {
        color: #D94854 !important;
        font-size: 4rem !important;
        font-weight: 900 !important;
        letter-spacing: -2px;
    }

    /* Customização das Abas Estilo o seu HTML */
    .stTabs [data-baseweb="tab-list"] {
        gap: 30px;
        border-bottom: 1px solid rgba(217, 189, 156, 0.2);
        background-color: transparent !important;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        border: none !important;
        color: #BFBAB0 !important;
        padding-bottom: 15px !important;
    }
    .stTabs [aria-selected="true"] {
        color: #BF0413 !important;
        border-bottom: 3px solid #BF0413 !important;
        font-weight: 700 !important;
    }

    /* Ocultar menus do Streamlit */
    #MainMenu, footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. LÓGICA DE DADOS (O motor que já funcionava)
# ==========================================
def clean_currency(x):
    if pd.isna(x): return 0.0
    if isinstance(x, str):
        x = x.replace('R$', '').replace('.', '').replace(',', '.').strip()
        try: return float(x)
        except: return 0.0
    return float(x)

if "dados" not in st.session_state:
    st.session_state.dados = None

# ==========================================
# 4. TELA INICIAL (UPLOAD)
# ==========================================
if st.session_state.dados is None:
    st.markdown("""
        <div style='text-align: center; padding-top: 50px; padding-bottom: 30px;'>
            <h1 style='color: #D9BD9C; font-size: 3.5rem; font-weight: 800; margin-bottom: 0;'>Smart Fatura IA</h1>
            <p style='color: #BFBAB0; font-size: 1.2rem; opacity: 0.8;'>Analise seus gastos com inteligência e elegância.</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info("👆 Arraste seu arquivo CSV para a caixa abaixo:")
        arquivo = st.file_uploader("", type=['csv'])
        if arquivo:
            # Tenta ler o CSV (tratando possíveis erros de separador)
            try:
                df = pd.read_csv(arquivo)
                if 'Valor' not in df.columns:
                    arquivo.seek(0)
                    df = pd.read_csv(arquivo, sep=';', encoding='utf-8')
            except:
                arquivo.seek(0)
                df = pd.read_csv(arquivo, sep=';', encoding='utf-8')
                
            if 'Valor' in df.columns:
                df['Valor_Num'] = df['Valor'].apply(clean_currency)
                st.session_state.dados = df
                st.rerun()
            else:
                st.error("⚠️ Coluna 'Valor' não encontrada. Verifique seu CSV.")

# ==========================================
# 5. DASHBOARD PRINCIPAL
# ==========================================
else:
    df = st.session_state.dados
    
    # SIDEBAR
    with st.sidebar:
        st.markdown("<h2 style='color: #D9BD9C;'>⚙️ Ajustes</h2>", unsafe_allow_html=True)
        categorias = df['Categoria'].unique().tolist() if 'Categoria' in df.columns else []
        filtro = st.multiselect("Filtrar Setores", categorias, default=categorias)
        
        st.markdown("---")
        if st.button("📂 Substituir Fatura", use_container_width=True):
            st.session_state.dados = None
            st.rerun()

    df_filtered = df[df['Categoria'].isin(filtro)] if categorias else df
    total = df_filtered['Valor_Num'].sum()

    # HERO METRIC (Card Principal)
    st.metric(label="Total da Fatura", value=f"R$ {total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    st.markdown("<br>", unsafe_allow_html=True)

    # ABAS
    tab_dash, tab_ia = st.tabs(["📈 Dashboard Visuais", "🤖 Consultor IA"])

    with tab_dash:
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.markdown("<h4 style='color: #D9BD9C;'>Distribuição dos Gastos</h4>", unsafe_allow_html=True)
            if 'Categoria' in df_filtered.columns:
                fig_pie = px.pie(df_filtered, values='Valor_Num', names='Categoria', hole=0.6,
                                 color_discrete_sequence=['#BF0413', '#D94854', '#D9BD9C', '#BFBAB0'])
                fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                                      font_color='#BFBAB0', showlegend=True)
                st.plotly_chart(fig_pie, use_container_width=True)

        with col_right:
            st.markdown("<h4 style='color: #D9BD9C;'>Maiores Despesas</h4>", unsafe_allow_html=True)
            top_8 = df_filtered.sort_values('Valor_Num', ascending=False).head(8)
            fig_bar = px.bar(top_8, x='Valor_Num', y='Lançamento', orientation='h',
                             color='Valor_Num', color_continuous_scale=['#D9BD9C', '#BF0413'])
            fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                                  font_color='#BFBAB0', showlegend=False, yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_bar, use_container_width=True)

        with st.expander("📄 Ver tabela completa de transações"):
            st.dataframe(df_filtered[['Data', 'Lançamento', 'Categoria', 'Valor_Num']], use_container_width=True)

    with tab_ia:
        st.markdown("<h4 style='color: #D9BD9C;'>💬 Conversar com a Fatura</h4>", unsafe_allow_html=True)
        
        if MINHA_CHAVE_GEMINI == "COLE_SUA_API_KEY_AQUI":
            st.error("⚠️ Insira sua chave API na linha 8 do código para habilitar o chat.")
        else:
            genai.configure(api_key=MINHA_CHAVE_GEMINI)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            pergunta = st.chat_input("Digite sua pergunta financeira...")
            if pergunta:
                st.chat_message("user").write(pergunta)
                with st.spinner("Analisando seus dados..."):
                    contexto = df_filtered[['Data', 'Lançamento', 'Categoria', 'Valor_Num']].to_csv(index=False)
                    full_prompt = f"Você é um consultor financeiro. Dados da fatura:\n{contexto}\nResponda em Reais (R$). Pergunta: {pergunta}"
                    try:
                        resposta = model.generate_content(full_prompt)
                        st.chat_message("assistant").write(resposta.text)
                    except Exception as e:
                        st.error(f"Erro na IA: {e}")