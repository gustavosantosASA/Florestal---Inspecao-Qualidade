# app.py
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from PIL import Image # Biblioteca para manipulação de imagens

# --- CONFIGURAÇÃO DA PÁGINA ---
# Usando a outra logo como favicon da página
try:
    favicon = Image.open("Marca Águia Florestal-02.png")
except FileNotFoundError:
    favicon = "📋" # Fallback para emoji se a logo não for encontrada

st.set_page_config(
    page_title="Inspeção de Qualidade",
    page_icon=favicon,
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- FUNÇÃO PARA CARREGAR CSS CUSTOMIZADO ---
def load_custom_css():
    # Cores baseadas na nova identidade visual
    primary_color = "#20643F" # Verde Principal
    secondary_color = "#2E8B57" # Verde Secundário (um pouco mais claro)
    background_color = "#F5F5F5" # Branco Gelo
    card_background = "#FFFFFF" # Branco Puro para os cartões
    text_color = "#1a1a1a"
    
    st.markdown(f"""
        <style>
            /* Esconde o menu hamburger e o rodapé do Streamlit */
            #MainMenu, footer {{
                visibility: hidden;
            }}

            /* Estilo do corpo da página com a cor de fundo */
            body {{
                background-color: {background_color};
            }}

            /* Estilo dos blocos/cartões principais */
            section[data-testid="stAppViewContainer"] > div:first-child > div:first-child {{
                background-color: {card_background};
                padding: 1.5rem 2rem 2rem 2rem;
                border-radius: 15px;
                box-shadow: 0 6px 15px rgba(0,0,0,0.06);
                border: 1px solid #e6e6e6;
            }}
            
            /* Botões principais (Próximo, Submeter, etc.) */
            .stButton > button {{
                width: 100%;
                height: 3.2rem;
                font-size: 1.1rem;
                font-weight: bold;
                border-radius: 8px;
                border: none;
                color: white;
                background-color: {primary_color};
                transition: background-color 0.2s ease;
            }}
            .stButton > button:hover {{
                background-color: {secondary_color};
                color: white;
            }}
            .stButton > button:focus {{
                outline: none !important;
                box-shadow: 0 0 0 0.2rem rgba(32, 100, 63, 0.4);
            }}

            /* Estilo para campos de input de texto e número */
            .stTextInput input, .stNumberInput input {{
                border-radius: 8px;
                height: 3rem;
                border: 1px solid #ced4da;
                transition: all 0.2s ease;
            }}
            .stTextInput input:focus, .stNumberInput input:focus {{
                border-color: {primary_color};
                box-shadow: 0 0 0 0.2rem rgba(32, 100, 63, 0.25);
            }}

            /* Ajuste no título principal */
            h1 {{
                color: {primary_color};
                font-weight: bold;
                text-align: center;
            }}

            /* Barra de progresso com a cor primária */
            .stProgress > div > div > div > div {{
                background-color: {primary_color};
            }}
        </style>
    """, unsafe_allow_html=True)

# --- INICIALIZAÇÃO E FUNÇÕES DO BACKEND (sem mudanças) ---
if 'current_step' not in st.session_state:
    st.session_state.current_step = 1
if 'form_data' not in st.session_state:
    st.session_state.form_data = {}

# Versão atualizada da função para usar os "Secrets"
def submit_data_to_sheets(data):
    try:
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        
        # Converte o "Secret" do Streamlit para um dicionário Python padrão
        creds_dict = dict(st.secrets["gcp_service_account"])
        
        # Passa o dicionário para a função de credenciais
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        
        gc = gspread.authorize(creds)
        sh = gc.open_by_key("1cG1KTzTUTf6A_DhWC6NIwRdAdLjaCTUYr9VgS4X03fU").worksheet("Base")
        sh.append_row(data)
        return True, None
    except Exception as e:
        return False, str(e)

# --- FUNÇÕES PARA RENDERIZAR CADA ETAPA (sem mudanças na lógica) ---
def render_step_1():
    st.subheader("Etapa 1: Identificação da Inspeção")
    st.markdown("Preencha as informações do responsável e do lote.")
    with st.form("step1_form"):
        col1, col2 = st.columns(2)
        with col1:
            email = st.text_input("Seu Endereço de e-mail*", value=st.session_state.form_data.get('email', ''), placeholder="nome.sobrenome@email.com")
            responsavel = st.text_input("Responsável pela inspeção*", value=st.session_state.form_data.get('responsavel', ''), placeholder="Digite seu nome completo")
        with col2:
            lote = st.text_input("LOTE (ano/semana)*", value=st.session_state.form_data.get('lote', ''), placeholder="Ex: 2025/33")
            plaina = st.text_input("Plaina", value=st.session_state.form_data.get('plaina', ''), placeholder="Informação da plaina")
        submitted = st.form_submit_button("Próximo ➡️")
        if submitted:
            if not email or not responsavel or not lote:
                st.warning("Os campos com * são obrigatórios.")
            else:
                st.session_state.form_data.update({'email': email, 'responsavel': responsavel, 'lote': lote, 'plaina': plaina})
                st.session_state.current_step = 2
                st.rerun()

def render_step_2():
    st.subheader("Etapa 2: Dimensões e Enfardamento")
    with st.form("step2_form"):
        enfardamento_pecas = st.text_input("Número de peças/camada (A, AF, AG, Lamar)", value=st.session_state.form_data.get('enfardamento_pecas', ''), placeholder="Ex: A (20)")
        enfardamento_dimensoes = st.text_input("Dimensões das peças", value=st.session_state.form_data.get('enfardamento_dimensoes', ''), placeholder="Ex: 20x100")
        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**Espessura (E)**")
            e1 = st.number_input("E1 (mm) Entrada da plaina", value=st.session_state.form_data.get('e1', 0.0), format="%.2f", step=0.01)
            e2 = st.number_input("E2 (mm) Meio da tábua", value=st.session_state.form_data.get('e2', 0.0), format="%.2f", step=0.01)
            e3 = st.number_input("E3 (mm) Saída da plaina", value=st.session_state.form_data.get('e3', 0.0), format="%.2f", step=0.01)
        with col2:
            st.markdown("**Largura (L)**")
            l1 = st.number_input("L1 (mm) Entrada da plaina", value=st.session_state.form_data.get('l1', 0.0), format="%.2f", step=0.01)
            l2 = st.number_input("L2 (mm) Meio da tabua", value=st.session_state.form_data.get('l2', 0.0), format="%.2f", step=0.01)
            l3 = st.number_input("L3 (mm) Saída da plaina", value=st.session_state.form_data.get('l3', 0.0), format="%.2f", step=0.01)
        with col3:
            st.markdown("**Comprimento e Umidade**")
            comprimento = st.number_input("Comprimento (mm)", value=st.session_state.form_data.get('comprimento', 0.0), format="%.2f", step=0.01)
            umidade = st.number_input("Umidade (8% a 16%)", value=st.session_state.form_data.get('umidade', 0.0), min_value=0.0, max_value=100.0, format="%.1f", step=0.1)
        nav_cols = st.columns([1, 1, 6])
        with nav_cols[0]:
            back_clicked = st.form_submit_button("⬅️ Voltar")
        with nav_cols[1]:
            next_clicked = st.form_submit_button("Próximo ➡️")
        if back_clicked:
            st.session_state.current_step = 1
            st.rerun()
        if next_clicked:
            st.session_state.form_data.update({'enfardamento_pecas': enfardamento_pecas, 'enfardamento_dimensoes': enfardamento_dimensoes, 'e1': e1, 'e2': e2, 'e3': e3, 'l1': l1, 'l2': l2, 'l3': l3, 'comprimento': comprimento, 'umidade': umidade})
            st.session_state.current_step = 3
            st.rerun()

def render_step_3():
    st.subheader("Etapa 3: Inspeção Visual e Envio Final")
    with st.form("step3_form"):
        options = ["Conforme", "Não Conforme", "Não Aplicável"]
        col1, col2 = st.columns(2)
        with col1:
            azulamento = st.radio("Azulamento", options, horizontal=True, key="azulamento")
            tortuosidade = st.radio("Tortuosidade", options, horizontal=True, key="tortuosidade")
            no_morto = st.radio("Nó morto", options, horizontal=True, key="no_morto")
            pontuacao = st.number_input("Pontuação Final", min_value=0, max_value=100, step=1, key="pontuacao")
        with col2:
            esmoado = st.radio("Esmoado", options, horizontal=True, key="esmoado")
            no_gravata = st.radio("Nó gravata", options, horizontal=True, key="no_gravata")
            marcas = st.radio("Marcas de ferramenta", options, horizontal=True, key="marcas")
        st.divider()
        st.subheader("Fotos da Inspeção")
        foto_camera = st.camera_input("Tirar uma foto agora com a câmera")
        fotos_galeria = st.file_uploader("Ou selecionar uma ou mais fotos da galeria", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])
        nav_cols = st.columns([1, 6, 2])
        with nav_cols[0]:
            back_clicked = st.form_submit_button("⬅️ Voltar")
        with nav_cols[2]:
            submit_clicked = st.form_submit_button("✔️ SUBMETER INSPEÇÃO")
        if back_clicked:
            st.session_state.current_step = 2
            st.rerun()
        if submit_clicked:
            with st.spinner("Enviando dados..."):
                fotos_carregadas = []
                if foto_camera is not None:
                    foto_camera.name = f"foto_camera_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                    fotos_carregadas.append(foto_camera)
                if fotos_galeria:
                    fotos_carregadas.extend(fotos_galeria)
                nomes_fotos = ", ".join([f.name for f in fotos_carregadas]) if fotos_carregadas else "Nenhuma foto enviada"
                now = datetime.now()
                final_data_row = [
                    now.isoformat(), now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"),
                    st.session_state.form_data.get('email'), st.session_state.form_data.get('responsavel'),
                    st.session_state.form_data.get('lote'), st.session_state.form_data.get('plaina'),
                    st.session_state.form_data.get('enfardamento_pecas'), st.session_state.form_data.get('enfardamento_dimensoes'),
                    st.session_state.form_data.get('e1'), st.session_state.form_data.get('e2'), st.session_state.form_data.get('e3'),
                    st.session_state.form_data.get('l1'), st.session_state.form_data.get('l2'), st.session_state.form_data.get('l3'),
                    st.session_state.form_data.get('comprimento'), st.session_state.form_data.get('umidade'),
                    azulamento, tortuosidade, no_morto, esmoado, no_gravata, marcas, pontuacao, nomes_fotos
                ]
                success, error_message = submit_data_to_sheets(final_data_row)
                if success:
                    st.session_state.current_step = 4
                    del st.session_state.form_data
                    st.rerun()
                else:
                    st.error(f"Falha ao enviar os dados: {error_message}")

def render_success_step():
    st.success("🎉 Inspeção registrada com sucesso na planilha!")
    st.balloons()
    st.markdown("Obrigado por preencher o formulário. Você pode iniciar uma nova inspeção clicando no botão abaixo.")
    if st.button("Iniciar Nova Inspeção"):
        st.session_state.current_step = 1
        st.session_state.form_data = {}
        st.rerun()

# --- LÓGICA PRINCIPAL DE RENDERIZAÇÃO ---
load_custom_css()

# Adiciona a logo no topo da página
try:
    logo = Image.open("logo_horizontal.png")
    # Usamos colunas para centralizar e controlar a largura da logo.
    # A coluna do meio (col2) é onde a imagem ficará.
    # As colunas laterais (col1, col3) servem como espaçamento.
    col1, col2, col3 = st.columns([1, 1, 1]) # Proporção: 25% | 50% | 25%
    
    with col2:
        st.image(logo, use_container_width=True)
except FileNotFoundError:
    st.title("📋 Formulário de Inspeção de Qualidade")

# Adiciona um espaço após a logo
st.markdown("<br>", unsafe_allow_html=True)

# Barra de progresso visual
progress_value = (st.session_state.current_step - 1) / 3
st.progress(progress_value)

# Renderiza a etapa atual baseada no st.session_state
if st.session_state.current_step == 1:
    render_step_1()
elif st.session_state.current_step == 2:
    render_step_2()
elif st.session_state.current_step == 3:
    render_step_3()
elif st.session_state.current_step == 4:
    render_success_step()