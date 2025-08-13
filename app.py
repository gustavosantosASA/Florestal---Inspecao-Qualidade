# app.py
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from PIL import Image
import io

# Importações da biblioteca base do Google para o Drive
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# --- CONFIGURAÇÃO DA PÁGINA ---
try:
    favicon = Image.open("Marca Águia Florestal-02.png")
except FileNotFoundError:
    favicon = "📋" 
st.set_page_config(
    page_title="Inspeção de Qualidade",
    page_icon=favicon,
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- NOVA FUNÇÃO DE CSS PROFISSIONAL ---
def load_custom_css():
    primary_color = "#20643F"    # Verde Principal
    secondary_color = "#1B4E33"  # Verde Escuro para hover
    background_color = "#F4F7F5" # Fundo Cinza-esverdeado bem claro
    text_color = "#31333F"       # Texto principal (preto suave)
    light_gray = "#DCE1DE"       # Cinza claro para bordas

    st.markdown(f"""
        <style>
            /* Reset e Fundo Geral */
            #MainMenu, footer {{visibility: hidden;}}
            body {{ background-color: {background_color} !important; }}

            /* Container principal em formato de card */
            section[data-testid="stAppViewContainer"] > div:first-child > div:first-child {{
                background-color: #FFFFFF;
                padding: 1.5rem 2.5rem 2.5rem 2.5rem;
                border-radius: 20px;
                box-shadow: 0 8px 25px rgba(0,0,0,0.07);
                border: 1px solid #E0E0E0;
            }}

            /* Tipografia e Títulos */
            h1, h2, h3, h4, h5, h6 {{
                color: {text_color};
                font-weight: 600;
            }}
            h2 {{ /* Título de cada etapa */
                color: {primary_color};
                font-size: 1.6rem;
                font-weight: 700;
                margin-top: 1rem;
                margin-bottom: 2rem;
                text-align: center;
                border-bottom: 2px solid {background_color};
                padding-bottom: 0.5rem;
            }}
            h3 {{ /* Subtítulos internos */
                color: {secondary_color};
                font-weight: 600;
                font-size: 1.1rem;
                margin-top: 1.5rem;
            }}

            /* Estilo dos Inputs (minimalista, com borda inferior) */
            .stTextInput, .stNumberInput {{
                margin-bottom: 0.5rem;
            }}
            .stTextInput input, .stNumberInput input {{
                background-color: transparent !important;
                border: none !important;
                border-bottom: 2px solid {light_gray} !important;
                border-radius: 0 !important;
                padding-left: 0 !important;
                transition: border-bottom-color 0.3s ease;
            }}
            .stTextInput input:focus, .stNumberInput input:focus {{
                border-bottom-color: {primary_color} !important;
                box-shadow: none !important;
            }}

            /* Botões Principais */
            .stButton > button {{
                width: 100%; height: 3.2rem; font-size: 1.1rem; font-weight: bold;
                border-radius: 10px; border: none; background-color: {primary_color};
                color: white; transition: all 0.2s ease-in-out;
            }}
            .stButton > button:hover {{
                background-color: {secondary_color};
                transform: scale(1.02);
            }}

            /* --- NOVO ESTILO PARA RADIO BUTTONS --- */
            /* Esconde o círculo do radio button padrão */
            div[data-baseweb="radio"] input[type="radio"] {{
                display: none;
            }}
            /* Estiliza o contêiner de cada opção */
            div[data-baseweb="radio"] label {{
                display: block;
                background-color: #F0F0F0;
                color: {text_color};
                border-radius: 10px;
                padding: 0.75rem 1rem;
                margin: 0.25rem 0;
                cursor: pointer;
                border: 2px solid transparent;
                transition: all 0.2s ease-in-out;
                font-weight: 500;
                text-align: center;
            }}
            /* Estilo da opção ao passar o mouse */
            div[data-baseweb="radio"] label:hover {{
                background-color: #E0E0E0;
                border-color: {light_gray};
            }}
            /* Estilo da opção QUANDO SELECIONADA */
            div[data-baseweb="radio"] input[type="radio"]:checked + div {{
                background-color: {primary_color};
                color: white;
                border-color: {secondary_color};
                font-weight: 700;
            }}

            /* Barra de progresso */
            .stProgress > div > div > div > div {{
                background-color: {primary_color};
            }}

        </style>
    """, unsafe_allow_html=True)

# --- INICIALIZAÇÃO DO SESSION STATE (sem mudanças) ---
if 'current_step' not in st.session_state: st.session_state.current_step = 1
if 'form_data' not in st.session_state: st.session_state.form_data = {}

# --- FUNÇÕES DE BACKEND (sem mudanças) ---
def authenticate_google_services():
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    gspread_client = gspread.authorize(creds)
    drive_service = build('drive', 'v3', credentials=creds)
    return gspread_client, drive_service

def upload_file_to_drive(drive_service, file_object):
    try:
        DRIVE_FOLDER_ID = "0AFP5U55axe3sUk9PVA"
        file_metadata = {'name': file_object.name, 'parents': [DRIVE_FOLDER_ID]}
        media = MediaIoBaseUpload(io.BytesIO(file_object.getvalue()), mimetype=file_object.type, resumable=True)
        file = drive_service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink', supportsAllDrives=True).execute()
        file_id = file.get('id')
        drive_service.permissions().create(fileId=file_id, body={'type': 'anyone', 'role': 'reader'}, supportsAllDrives=True).execute()
        return file.get('webViewLink')
    except Exception as e:
        st.error(f"Erro no upload para o Drive: {e}")
        return None

def submit_data(data_row, fotos_carregadas, gspread_client, drive_service):
    try:
        links_das_fotos = []
        if fotos_carregadas:
            with st.spinner("Fazendo upload das imagens para o Google Drive..."):
                for foto in fotos_carregadas:
                    link = upload_file_to_drive(drive_service, foto)
                    if link: links_das_fotos.append(link)
        data_row[-1] = ", ".join(links_das_fotos) if links_das_fotos else "Nenhuma foto enviada"
        with st.spinner("Enviando dados para a planilha..."):
            sh = gspread_client.open_by_key("1cG1KTzTUTf6A_DhWC6NIwRdAdLjaCTUYr9VgS4X03fU").worksheet("Base")
            sh.append_row(data_row)
        return True, None
    except Exception as e: return False, str(e)

# --- FUNÇÕES PARA RENDERIZAR AS ETAPAS ---

def render_step_1():
    st.header("Etapa 1: Identificação da Inspeção")
    with st.form("step1_form"):
        st.subheader("Dados do Responsável")
        col1, col2 = st.columns(2)
        with col1:
            email = st.text_input("Seu Endereço de e-mail*", value=st.session_state.form_data.get('email', ''))
        with col2:
            responsavel = st.text_input("Responsável pela inspeção*", value=st.session_state.form_data.get('responsavel', ''))
        
        st.subheader("Dados do Lote")
        col3, col4 = st.columns(2)
        with col3:
            lote = st.text_input("LOTE (ano/semana)*", value=st.session_state.form_data.get('lote', ''))
        with col4:
            plaina = st.text_input("Plaina", value=st.session_state.form_data.get('plaina', ''))
        
        st.markdown("<br>", unsafe_allow_html=True) # Espaçamento
        if st.form_submit_button("Próximo ➡️"):
            if not email or not responsavel or not lote: st.warning("Os campos com * são obrigatórios.")
            else:
                st.session_state.form_data.update({'email': email, 'responsavel': responsavel, 'lote': lote, 'plaina': plaina})
                st.session_state.current_step = 2; st.rerun()

def render_step_2():
    st.header("Etapa 2: Dimensões e Enfardamento")
    with st.form("step2_form"):
        st.subheader("Enfardamento")
        enfardamento_pecas = st.text_input("Número de peças/camada (ex: A (20), AF (17))", value=st.session_state.form_data.get('enfardamento_pecas', ''))
        enfardamento_dimensoes = st.text_input("Dimensões das peças (ex: 20x100)", value=st.session_state.form_data.get('enfardamento_dimensoes', ''))
        
        st.subheader("Medidas")
        col1, col2, col3 = st.columns(3)
        with col1:
            e1 = st.number_input("E1 (mm) Entrada", value=st.session_state.form_data.get('e1', 0.0), format="%.2f", step=0.01)
            e2 = st.number_input("E2 (mm) Meio", value=st.session_state.form_data.get('e2', 0.0), format="%.2f", step=0.01)
            e3 = st.number_input("E3 (mm) Saída", value=st.session_state.form_data.get('e3', 0.0), format="%.2f", step=0.01)
        with col2:
            l1 = st.number_input("L1 (mm) Entrada", value=st.session_state.form_data.get('l1', 0.0), format="%.2f", step=0.01)
            l2 = st.number_input("L2 (mm) Meio", value=st.session_state.form_data.get('l2', 0.0), format="%.2f", step=0.01)
            l3 = st.number_input("L3 (mm) Saída", value=st.session_state.form_data.get('l3', 0.0), format="%.2f", step=0.01)
        with col3:
            comprimento = st.number_input("Comprimento (mm)", value=st.session_state.form_data.get('comprimento', 0.0), format="%.2f", step=0.01)
            umidade = st.number_input("Umidade (%)", value=st.session_state.form_data.get('umidade', 0.0), min_value=0.0, max_value=100.0, format="%.1f", step=0.1)
        
        st.markdown("<br>", unsafe_allow_html=True)
        nav_cols = st.columns([1, 1, 4])
        if nav_cols[0].form_submit_button("⬅️ Voltar"): st.session_state.current_step = 1; st.rerun()
        if nav_cols[1].form_submit_button("Próximo ➡️"):
            st.session_state.form_data.update({'enfardamento_pecas': enfardamento_pecas, 'enfardamento_dimensoes': enfardamento_dimensoes, 'e1': e1, 'e2': e2, 'e3': e3, 'l1': l1, 'l2': l2, 'l3': l3, 'comprimento': comprimento, 'umidade': umidade})
            st.session_state.current_step = 3; st.rerun()

def render_step_3():
    st.header("Etapa 3: Inspeção Visual e Envio")
    with st.form("step3_form"):
        st.subheader("Checklist de Inspeção")
        options = ["Conforme", "Não Conforme", "Não Aplicável"]
        col1, col2 = st.columns(2)
        with col1:
            azulamento = st.radio("Azulamento", options)
            tortuosidade = st.radio("Tortuosidade", options)
            no_morto = st.radio("Nó morto", options)
            esmoado = st.radio("Esmoado", options)
        with col2:
            no_gravata = st.radio("Nó gravata", options)
            marcas = st.radio("Marcas de ferramenta", options)
            pontuacao = st.number_input("Pontuação Final", min_value=0, max_value=100, step=1)
        
        st.subheader("Evidências Fotográficas")
        foto_camera = st.camera_input("Tirar uma foto com a câmera")
        fotos_galeria = st.file_uploader("Ou selecionar fotos da galeria", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])
        
        st.markdown("<br>", unsafe_allow_html=True)
        nav_cols = st.columns([1, 6, 2])
        if nav_cols[0].form_submit_button("⬅️ Voltar"): st.session_state.current_step = 2; st.rerun()
        if nav_cols[2].form_submit_button("✔️ SUBMETER INSPEÇÃO"):
            fotos_carregadas = []
            if foto_camera:
                foto_camera.name = f"foto_camera_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"; fotos_carregadas.append(foto_camera)
            if fotos_galeria: fotos_carregadas.extend(fotos_galeria)
            now = datetime.now()
            final_data_row = [now.isoformat(), now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"), st.session_state.form_data.get('email'), st.session_state.form_data.get('responsavel'), st.session_state.form_data.get('lote'), st.session_state.form_data.get('plaina'), st.session_state.form_data.get('enfardamento_pecas'), st.session_state.form_data.get('enfardamento_dimensoes'), st.session_state.form_data.get('e1'), st.session_state.form_data.get('e2'), st.session_state.form_data.get('e3'), st.session_state.form_data.get('l1'), st.session_state.form_data.get('l2'), st.session_state.form_data.get('l3'), st.session_state.form_data.get('comprimento'), st.session_state.form_data.get('umidade'), azulamento, tortuosidade, no_morto, esmoado, no_gravata, marcas, pontuacao, "placeholder_para_fotos"]
            
            gspread_client, drive_service = authenticate_google_services()
            success, error_message = submit_data(final_data_row, fotos_carregadas, gspread_client, drive_service)
            
            if success:
                st.session_state.current_step = 4; del st.session_state.form_data; st.rerun()
            else: st.error(f"Falha ao enviar os dados: {error_message}")

def render_success_step():
    st.success("🎉 Inspeção registrada com sucesso!"); st.balloons()
    st.markdown("Obrigado por preencher o formulário.")
    if st.button("Iniciar Nova Inspeção"):
        st.session_state.current_step = 1; st.session_state.form_data = {}; st.rerun()

# --- LÓGICA PRINCIPAL DE RENDERIZAÇÃO ---
load_custom_css()

col_logo1, col_logo2, col_logo3 = st.columns([1.5, 3, 1.5])
with col_logo2:
    try: st.image(Image.open("logo_horizontal.png"), use_container_width=True)
    except FileNotFoundError: st.title("Formulário de Inspeção de Qualidade")

st.progress((st.session_state.current_step - 1) / 3, text="")

if st.session_state.current_step == 1: render_step_1()
elif st.session_state.current_step == 2: render_step_2()
elif st.session_state.current_step == 3: render_step_3()
elif st.session_state.current_step == 4: render_success_step()