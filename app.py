# app.py
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from PIL import Image
# Bibliotecas para o Google Drive
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import io

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

# --- FUNÇÃO PARA CARREGAR CSS CUSTOMIZADO ---
def load_custom_css():
    primary_color = "#20643F" # Verde Principal
    secondary_color = "#2E8B57" # Verde Secundário
    
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

# --- INICIALIZAÇÃO DO SESSION STATE ---
if 'current_step' not in st.session_state: st.session_state.current_step = 1
if 'form_data' not in st.session_state: st.session_state.form_data = {}

# --- FUNÇÕES DE BACKEND ---

def upload_file_to_drive(file_object, creds):
    """Faz o upload de um objeto de arquivo para o Google Drive e retorna o link compartilhável."""
    try:
        gauth = GoogleAuth()
        gauth.credentials = creds
        drive = GoogleDrive(gauth)
        
        # !! IMPORTANTE !! SUBSTITUA PELO ID DA SUA PASTA DO GOOGLE DRIVE!
        DRIVE_FOLDER_ID = "SEU_ID_DA_PASTA_AQUI" 

        file_object.seek(0)
        file_bytes = io.BytesIO(file_object.read())
        
        drive_file = drive.CreateFile({
            'title': file_object.name,
            'parents': [{'id': DRIVE_FOLDER_ID}]
        })
        drive_file.content = file_bytes
        drive_file.Upload()
        drive_file.InsertPermission({'type': 'anyone', 'role': 'reader', 'value': 'anyone'})
        return drive_file['alternateLink']
    except Exception as e:
        st.error(f"Erro no upload para o Drive: {e}")
        return None

def submit_data_to_sheets_and_drive(data, fotos_carregadas):
    """Faz upload de fotos para o Drive e envia dados para o Sheets."""
    try:
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        
        links_das_fotos = []
        if fotos_carregadas:
            for foto in fotos_carregadas:
                link = upload_file_to_drive(foto, creds)
                if link:
                    links_das_fotos.append(link)
        
        # A última coluna da lista `data` é o placeholder para as fotos.
        data[-1] = ", ".join(links_das_fotos) if links_das_fotos else "Nenhuma foto enviada"

        gc = gspread.authorize(creds)
        sh = gc.open_by_key("1cG1KTzTUTf6A_DhWC6NIwRdAdLjaCTUYr9VgS4X03fU").worksheet("Base")
        sh.append_row(data)
        
        return True, None
    except Exception as e:
        return False, str(e)

# --- FUNÇÕES PARA RENDERIZAR CADA ETAPA ---

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
        enfardamento_pecas = st.text_input("Enfardamento - Número de peças/camada A (20) ; AF (17) ; AG (13) ; Lamar (29)", value=st.session_state.form_data.get('enfardamento_pecas', ''))
        enfardamento_dimensoes = st.text_input("Enfardamento Dimensões das peças", value=st.session_state.form_data.get('enfardamento_dimensoes', ''))
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
        if nav_cols[0].form_submit_button("⬅️ Voltar"):
            st.session_state.current_step = 1; st.rerun()
        if nav_cols[1].form_submit_button("Próximo ➡️"):
            st.session_state.form_data.update({
                'enfardamento_pecas': enfardamento_pecas, 'enfardamento_dimensoes': enfardamento_dimensoes, 
                'e1': e1, 'e2': e2, 'e3': e3, 'l1': l1, 'l2': l2, 'l3': l3, 
                'comprimento': comprimento, 'umidade': umidade
            })
            st.session_state.current_step = 3
            st.rerun()

def render_step_3():
    st.subheader("Etapa 3: Inspeção Visual e Envio Final")
    with st.form("step3_form"):
        options = ["Conforme", "Não Conforme", "Não Aplicável"]
        col1, col2 = st.columns(2)
        with col1:
            azulamento = st.radio("Inspeção visual [Azulamento]", options, horizontal=True)
            tortuosidade = st.radio("Inspeção visual [Tortuosidade]", options, horizontal=True)
            no_morto = st.radio("Inspeção visual [Nó morto]", options, horizontal=True)
            esmoado = st.radio("Inspeção visual [Esmoado]", options, horizontal=True)
        with col2:
            no_gravata = st.radio("Inspeção visual [Nó gravata]", options, horizontal=True)
            marcas = st.radio("Inspeção visual [Marcas de ferramenta]", options, horizontal=True)
            pontuacao = st.number_input("Pontuação", min_value=0, max_value=100, step=1)
        
        st.divider()
        st.subheader("Fotos da Inspeção")
        foto_camera = st.camera_input("Tirar uma foto agora com a câmera")
        fotos_galeria = st.file_uploader("Ou selecionar uma ou mais fotos da galeria", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])

        nav_cols = st.columns([1, 6, 2])
        if nav_cols[0].form_submit_button("⬅️ Voltar"):
            st.session_state.current_step = 2; st.rerun()
        if nav_cols[2].form_submit_button("✔️ SUBMETER INSPEÇÃO"):
            with st.spinner("Enviando dados e fazendo upload das imagens... Por favor, aguarde."):
                fotos_carregadas = []
                if foto_camera:
                    foto_camera.name = f"foto_camera_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                    fotos_carregadas.append(foto_camera)
                if fotos_galeria:
                    fotos_carregadas.extend(fotos_galeria)
                
                now = datetime.now()
                final_data_row = [
                    now.isoformat(), now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"),
                    st.session_state.form_data.get('email'), st.session_state.form_data.get('responsavel'),
                    st.session_state.form_data.get('lote'), st.session_state.form_data.get('plaina'),
                    st.session_state.form_data.get('enfardamento_pecas'), st.session_state.form_data.get('enfardamento_dimensoes'),
                    st.session_state.form_data.get('e1'), st.session_state.form_data.get('e2'), st.session_state.form_data.get('e3'),
                    st.session_state.form_data.get('l1'), st.session_state.form_data.get('l2'), st.session_state.form_data.get('l3'),
                    st.session_state.form_data.get('comprimento'), st.session_state.form_data.get('umidade'),
                    azulamento, tortuosidade, no_morto, esmoado, no_gravata, marcas, pontuacao,
                    "placeholder_para_fotos"
                ]
                
                success, error_message = submit_data_to_sheets_and_drive(final_data_row, fotos_carregadas)
                
                if success:
                    st.session_state.current_step = 4; del st.session_state.form_data; st.rerun()
                else:
                    st.error(f"Falha ao enviar os dados: {error_message}")

def render_success_step():
    st.success("🎉 Inspeção registrada com sucesso!")
    st.balloons()
    st.markdown("Obrigado por preencher o formulário. Você pode iniciar uma nova inspeção clicando no botão abaixo.")
    if st.button("Iniciar Nova Inspeção"):
        st.session_state.current_step = 1; st.session_state.form_data = {}; st.rerun()

# --- LÓGICA PRINCIPAL DE RENDERIZAÇÃO ---
load_custom_css()

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    try:
        st.image(Image.open("logo_horizontal.png"), use_container_width=True)
    except FileNotFoundError:
        st.title("📋 Formulário de Inspeção de Qualidade")

st.markdown("<br>", unsafe_allow_html=True)
st.progress((st.session_state.current_step - 1) / 3)

if st.session_state.current_step == 1: render_step_1()
elif st.session_state.current_step == 2: render_step_2()
elif st.session_state.current_step == 3: render_step_3()
elif st.session_state.current_step == 4: render_success_step()