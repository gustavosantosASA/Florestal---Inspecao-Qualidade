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

# --- CONFIGURAÇÃO DA PÁGINA (sem mudanças) ---
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

# --- FUNÇÃO CSS ATUALIZADA ---
def load_custom_css():
    primary_color = "#20643F"
    secondary_color = "#1B4E33"
    background_color = "#F9FAF9"

    st.markdown(f"""
        <style>
            /* Esconde menu e rodapé padrão do Streamlit */
            #MainMenu, footer {{visibility: hidden;}}

            /* Fundo geral */
            section[data-testid="stAppViewContainer"] {{
                background-color: {background_color};
                padding-top: 1rem;
                padding-bottom: 2rem;
            }}

            /* Container central em formato de card */
            section[data-testid="stAppViewContainer"] > div:first-child > div:first-child {{
                background-color: #FFFFFF;
                padding: 1.5rem 2rem 2rem 2rem;
                border-radius: 15px;
                box-shadow: 0 6px 15px rgba(0,0,0,0.06);
                border: 1px solid #e6e6e6;
            }}

            /* Títulos */
            h1, h2, h3, h4 {{
                color: {primary_color};
                font-weight: 700;
            }}
            h1 {{text-align: center; font-size: 1.8rem; margin-bottom: 1rem;}}
            h2 {{margin-top: 1rem; font-size: 1.3rem; border-left: 4px solid {primary_color}; padding-left: 0.5rem;}}

            /* Botões */
            .stButton > button {{
                width: 100%;
                height: 3rem;
                font-size: 1.05rem;
                font-weight: bold;
                border-radius: 8px;
                border: none;
                background-color: {primary_color};
                color: white;
                transition: all 0.25s ease;
            }}
            .stButton > button:hover {{
                background-color: {secondary_color};
                transform: translateY(-1px);
                box-shadow: 0px 3px 8px rgba(0,0,0,0.15);
            }}

            /* Inputs */
            input, textarea, select {{
                border: 1px solid #d9d9d9 !important;
                border-radius: 6px !important;
            }}

            /* Barra de progresso */
            .stProgress > div > div > div > div {{
                background-color: {primary_color};
            }}

            /* Radio buttons */
            div[data-baseweb="radio"] label span {{
                color: {primary_color} !important;
                font-weight: 500;
            }}

            /* Camera input */
            [data-testid="stCameraInput"] {{
                border-radius: 10px;
                border: 2px dashed {primary_color};
                padding: 8px;
            }}
        </style>
    """, unsafe_allow_html=True)


# --- INICIALIZAÇÃO DO SESSION STATE (sem mudanças) ---
if 'current_step' not in st.session_state: st.session_state.current_step = 1
if 'form_data' not in st.session_state: st.session_state.form_data = {}

# --- FUNÇÕES DE BACKEND (LÓGICA DE AUTENTICAÇÃO E UPLOAD CORRIGIDA) ---

def authenticate_google_services():
    """Cria e retorna clientes autorizados para o gspread e o Google Drive."""
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    
    gspread_client = gspread.authorize(creds)
    drive_service = build('drive', 'v3', credentials=creds)

    return gspread_client, drive_service

def upload_file_to_drive(drive_service, file_object):
    try:
        # !! IMPORTANTE !! Use o ID da pasta que está DENTRO do Drive Compartilhado
        DRIVE_FOLDER_ID = "0AFP5U55axe3sUk9PVA"

        file_metadata = {
            'name': file_object.name,
            'parents': [DRIVE_FOLDER_ID]
        }
        media = MediaIoBaseUpload(io.BytesIO(file_object.getvalue()), mimetype=file_object.type, resumable=True)
        
        # --- MUDANÇA PRINCIPAL AQUI ---
        # Adicionamos 'supportsAllDrives=True' para informar a API que estamos usando um Drive Compartilhado
        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink',
            supportsAllDrives=True  # <-- Parâmetro essencial para Drives Compartilhados
        ).execute()
        
        # A permissão 'anyone' já funciona em arquivos de Drives Compartilhados se as políticas permitirem
        file_id = file.get('id')
        drive_service.permissions().create(
            fileId=file_id, 
            body={'type': 'anyone', 'role': 'reader'},
            supportsAllDrives=True # <-- Adicionar aqui também por segurança
        ).execute()
        
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
            if not email or not responsavel or not lote: st.warning("Os campos com * são obrigatórios.")
            else:
                st.session_state.form_data.update({'email': email, 'responsavel': responsavel, 'lote': lote, 'plaina': plaina})
                st.session_state.current_step = 2; st.rerun()

def render_step_2():
    st.subheader("Etapa 2: Dimensões e Enfardamento")
    with st.form("step2_form"):
        enfardamento_pecas = st.text_input("Enfardamento - Número de peças/camada A (20) ; AF (17) ; AG (13) ; Lamar (29)", value=st.session_state.form_data.get('enfardamento_pecas', ''))
        enfardamento_dimensoes = st.text_input("Enfardamento Dimensões das peças", value=st.session_state.form_data.get('enfardamento_dimensoes', ''))
        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**Espessura (E)**"); e1 = st.number_input("E1 (mm) Entrada da plaina", value=st.session_state.form_data.get('e1', 0.0), format="%.2f", step=0.01)
            e2 = st.number_input("E2 (mm) Meio da tábua", value=st.session_state.form_data.get('e2', 0.0), format="%.2f", step=0.01)
            e3 = st.number_input("E3 (mm) Saída da plaina", value=st.session_state.form_data.get('e3', 0.0), format="%.2f", step=0.01)
        with col2:
            st.markdown("**Largura (L)**"); l1 = st.number_input("L1 (mm) Entrada da plaina", value=st.session_state.form_data.get('l1', 0.0), format="%.2f", step=0.01)
            l2 = st.number_input("L2 (mm) Meio da tabua", value=st.session_state.form_data.get('l2', 0.0), format="%.2f", step=0.01)
            l3 = st.number_input("L3 (mm) Saída da plaina", value=st.session_state.form_data.get('l3', 0.0), format="%.2f", step=0.01)
        with col3:
            st.markdown("**Comprimento e Umidade**"); comprimento = st.number_input("Comprimento (mm)", value=st.session_state.form_data.get('comprimento', 0.0), format="%.2f", step=0.01)
            umidade = st.number_input("Umidade (8% a 16%)", value=st.session_state.form_data.get('umidade', 0.0), min_value=0.0, max_value=100.0, format="%.1f", step=0.1)
        nav_cols = st.columns([1, 1, 6])
        if nav_cols[0].form_submit_button("⬅️ Voltar"): st.session_state.current_step = 1; st.rerun()
        if nav_cols[1].form_submit_button("Próximo ➡️"):
            st.session_state.form_data.update({'enfardamento_pecas': enfardamento_pecas, 'enfardamento_dimensoes': enfardamento_dimensoes, 'e1': e1, 'e2': e2, 'e3': e3, 'l1': l1, 'l2': l2, 'l3': l3, 'comprimento': comprimento, 'umidade': umidade})
            st.session_state.current_step = 3; st.rerun()

def render_step_3():
    st.subheader("Etapa 3: Inspeção Visual e Envio Final")
    with st.form("step3_form"):
        options = ["Conforme", "Não Conforme", "Não Aplicável"]; col1, col2 = st.columns(2)
        with col1:
            azulamento = st.radio("Inspeção visual [Azulamento]", options, horizontal=True); tortuosidade = st.radio("Inspeção visual [Tortuosidade]", options, horizontal=True)
            no_morto = st.radio("Inspeção visual [Nó morto]", options, horizontal=True); esmoado = st.radio("Inspeção visual [Esmoado]", options, horizontal=True)
        with col2:
            no_gravata = st.radio("Inspeção visual [Nó gravata]", options, horizontal=True); marcas = st.radio("Inspeção visual [Marcas de ferramenta]", options, horizontal=True)
            pontuacao = st.number_input("Pontuação", min_value=0, max_value=100, step=1)
        st.divider(); st.subheader("Fotos da Inspeção")
        foto_camera = st.camera_input("Tirar uma foto agora com a câmera"); fotos_galeria = st.file_uploader("Ou selecionar uma ou mais fotos da galeria", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])
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
    if st.button("Iniciar Nova Inspeção"):
        st.session_state.current_step = 1; st.session_state.form_data = {}; st.rerun()

# --- LÓGICA PRINCIPAL DE RENDERIZAÇÃO ---
load_custom_css()
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    try: st.image(Image.open("logo_horizontal.png"), use_container_width=True)
    except FileNotFoundError: st.title("📋 Formulário de Inspeção de Qualidade")
st.markdown("<br>", unsafe_allow_html=True); st.progress((st.session_state.current_step - 1) / 3)
if st.session_state.current_step == 1: render_step_1()
elif st.session_state.current_step == 2: render_step_2()
elif st.session_state.current_step == 3: render_step_3()
elif st.session_state.current_step == 4: render_success_step()