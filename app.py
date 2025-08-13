# app.py
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from PIL import Image
# Novas importações para o Google Drive
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import io

# --- CONFIGURAÇÃO DA PÁGINA (sem mudanças) ---
try:
    favicon = Image.open("Marca Águia Florestal-02.png")
except FileNotFoundError:
    favicon = "📋"
st.set_page_config(page_title="Inspeção de Qualidade", page_icon=favicon, layout="wide", initial_sidebar_state="collapsed")

# --- CSS CUSTOMIZADO (sem mudanças) ---
def load_custom_css():
    primary_color = "#20643F"
    secondary_color = "#2E8B57"
    st.markdown(f"""
        <style>
            #MainMenu, footer {{ visibility: hidden; }}
            section[data-testid="stAppViewContainer"] > div:first-child > div:first-child {{
                background-color: #FFFFFF; padding: 1.5rem 2rem 2rem 2rem; border-radius: 15px;
                box-shadow: 0 6px 15px rgba(0,0,0,0.06); border: 1px solid #e6e6e6;
            }}
            .stButton > button {{
                width: 100%; height: 3.2rem; font-size: 1.1rem; font-weight: bold; border-radius: 8px;
                border: none; color: white; background-color: {primary_color}; transition: background-color 0.2s ease;
            }}
            .stButton > button:hover {{ background-color: {secondary_color}; color: white; }}
            h1 {{ color: {primary_color}; font-weight: bold; text-align: center; }}
            .stProgress > div > div > div > div {{ background-color: {primary_color}; }}
        </style>
    """, unsafe_allow_html=True)

# --- INICIALIZAÇÃO E FUNÇÕES DO BACKEND ---
if 'current_step' not in st.session_state: st.session_state.current_step = 1
if 'form_data' not in st.session_state: st.session_state.form_data = {}

# --- NOVA FUNÇÃO DE UPLOAD PARA O GOOGLE DRIVE ---
def upload_file_to_drive(file_object, creds):
    """Faz o upload de um objeto de arquivo para o Google Drive e retorna o link compartilhável."""
    try:
        # Autenticação com o PyDrive2
        gauth = GoogleAuth()
        gauth.credentials = creds
        drive = GoogleDrive(gauth)

        # ID da pasta do Google Drive para onde as fotos serão enviadas
        # SUBSTITUA PELO ID DA SUA PASTA!
        DRIVE_FOLDER_ID = "1a2b3c4d5e6f7g8h9i0j_kLmM" # <-- COLOQUE O ID DA SUA PASTA AQUI

        # Converte o objeto de arquivo do Streamlit para um que o PyDrive2 entenda
        file_object.seek(0)
        file_bytes = io.BytesIO(file_object.read())
        
        # Cria o arquivo no Google Drive
        drive_file = drive.CreateFile({
            'title': file_object.name,
            'parents': [{'id': DRIVE_FOLDER_ID}]
        })
        drive_file.content = file_bytes
        drive_file.Upload()
        
        # Define a permissão para que qualquer pessoa com o link possa ver
        drive_file.InsertPermission({'type': 'anyone', 'role': 'reader', 'value': 'anyone'})

        return drive_file['alternateLink'] # Retorna o link de visualização
    except Exception as e:
        st.error(f"Erro no upload para o Drive: {e}")
        return None

# --- FUNÇÃO DE ENVIO PARA O GOOGLE SHEETS (ATUALIZADA) ---
def submit_data_to_sheets_and_drive(data, fotos_carregadas):
    try:
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        
        # 1. Faz o upload das fotos e obtém os links
        links_das_fotos = []
        if fotos_carregadas:
            for foto in fotos_carregadas:
                link = upload_file_to_drive(foto, creds)
                if link:
                    links_das_fotos.append(link)
        
        # Substitui o nome do arquivo pelo link na linha de dados
        data[-1] = ", ".join(links_das_fotos) if links_das_fotos else "Nenhuma foto enviada"

        # 2. Envia os dados para a planilha
        gc = gspread.authorize(creds)
        sh = gc.open_by_key("1cG1KTzTUTf6A_DhWC6NIwRdAdLjaCTUYr9VgS4X03fU").worksheet("Base")
        sh.append_row(data)
        
        return True, None
    except Exception as e:
        return False, str(e)

# --- RENDERIZAÇÃO DAS ETAPAS ---
# render_step_1 e render_step_2 não mudam.
def render_step_1():
    st.subheader("Etapa 1: Identificação da Inspeção")
    with st.form("step1_form"):
        col1, col2 = st.columns(2)
        with col1:
            email = st.text_input("Seu Endereço de e-mail*", value=st.session_state.form_data.get('email', ''))
            responsavel = st.text_input("Responsável pela inspeção*", value=st.session_state.form_data.get('responsavel', ''))
        with col2:
            lote = st.text_input("LOTE (ano/semana)*", value=st.session_state.form_data.get('lote', ''))
            plaina = st.text_input("Plaina", value=st.session_state.form_data.get('plaina', ''))
        if st.form_submit_button("Próximo ➡️"):
            if not email or not responsavel or not lote:
                st.warning("Os campos com * são obrigatórios.")
            else:
                st.session_state.form_data.update({'email': email, 'responsavel': responsavel, 'lote': lote, 'plaina': plaina})
                st.session_state.current_step = 2
                st.rerun()

def render_step_2():
    st.subheader("Etapa 2: Dimensões e Enfardamento")
    with st.form("step2_form"):
        # ... (código dos campos da etapa 2, sem mudanças)
        enfardamento_pecas = st.text_input("Número de peças/camada", value=st.session_state.form_data.get('enfardamento_pecas', ''))
        enfardamento_dimensoes = st.text_input("Dimensões das peças", value=st.session_state.form_data.get('enfardamento_dimensoes', ''))
        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1: e1 = st.number_input("E1 (mm)", value=st.session_state.form_data.get('e1', 0.0), format="%.2f")
        with col2: l1 = st.number_input("L1 (mm)", value=st.session_state.form_data.get('l1', 0.0), format="%.2f")
        # ... (restante dos campos)
        nav_cols = st.columns([1, 1, 6])
        if nav_cols[0].form_submit_button("⬅️ Voltar"):
            st.session_state.current_step = 1
            st.rerun()
        if nav_cols[1].form_submit_button("Próximo ➡️"):
            st.session_state.form_data.update({'enfardamento_pecas': enfardamento_pecas, 'enfardamento_dimensoes': enfardamento_dimensoes, 'e1': e1, 'l1': l1})
            st.session_state.current_step = 3
            st.rerun()
            
# FUNÇÃO RENDER_STEP_3 ATUALIZADA
def render_step_3():
    st.subheader("Etapa 3: Inspeção Visual e Envio Final")
    with st.form("step3_form"):
        # ... (código dos campos de inspeção visual, sem mudanças)
        options = ["Conforme", "Não Conforme", "Não Aplicável"]
        col1, col2 = st.columns(2); azulamento = col1.radio("Azulamento", options, horizontal=True)
        
        st.divider()
        st.subheader("Fotos da Inspeção")
        foto_camera = st.camera_input("Tirar uma foto agora com a câmera")
        fotos_galeria = st.file_uploader("Ou selecionar uma ou mais fotos da galeria", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])

        nav_cols = st.columns([1, 6, 2])
        if nav_cols[0].form_submit_button("⬅️ Voltar"):
            st.session_state.current_step = 2; st.rerun()
        if nav_cols[2].form_submit_button("✔️ SUBMETER INSPEÇÃO"):
            with st.spinner("Enviando dados e fazendo upload das imagens..."):
                fotos_carregadas = []
                if foto_camera is not None:
                    foto_camera.name = f"foto_camera_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                    fotos_carregadas.append(foto_camera)
                if fotos_galeria:
                    fotos_carregadas.extend(fotos_galeria)
                
                # Prepara a linha de dados (o campo de fotos é um placeholder por enquanto)
                now = datetime.now()
                final_data_row = [now.isoformat(), now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"),
                                  st.session_state.form_data.get('email'), st.session_state.form_data.get('responsavel'),
                                  # ... (todos os outros campos)
                                  azulamento, "placeholder_para_fotos"]
                
                # Chama a nova função de envio unificada
                success, error_message = submit_data_to_sheets_and_drive(final_data_row, fotos_carregadas)
                
                if success:
                    st.session_state.current_step = 4; del st.session_state.form_data; st.rerun()
                else:
                    st.error(f"Falha ao enviar os dados: {error_message}")

def render_success_step():
    st.success("🎉 Inspeção registrada com sucesso!")
    st.balloons()
    if st.button("Iniciar Nova Inspeção"):
        st.session_state.current_step = 1; st.session_state.form_data = {}; st.rerun()

# --- LÓGICA PRINCIPAL DE RENDERIZAÇÃO (com a logo) ---
load_custom_css()
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    try: st.image(Image.open("logo_horizontal.png"))
    except: st.title("📋 Formulário de Inspeção")
st.markdown("<br>", unsafe_allow_html=True)
st.progress((st.session_state.current_step - 1) / 3)

if st.session_state.current_step == 1: render_step_1()
elif st.session_state.current_step == 2: render_step_2()
elif st.session_state.current_step == 3: render_step_3()
elif st.session_state.current_step == 4: render_success_step()