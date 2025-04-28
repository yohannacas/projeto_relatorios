import streamlit as st
import sqlite3
import os
from datetime import datetime
from utils import salvar_processo
from PIL import Image
import base64

# Criar pastas
os.makedirs("uploads", exist_ok=True)
os.makedirs("relatorios", exist_ok=True)

# ========= Cabeçalho com logo e título =========
def exibir_logo_e_titulo_lado_a_lado():
    logo_path = "logo.png"
    with open(logo_path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode()

    st.markdown(
        f"""
        <div style="display: flex; align-items: center; margin-top: 30px;">
            <img src="data:image/png;base64,{encoded}" style="width: 65px; margin-right: 30px;" />
            <h1 style="margin: 0; font-size: 40px;">JUSREPORT</h1>
        </div>
        <div style="margin-top: 20px;">
            <h3>📄 Envio de Processo para Relatório</h3>
        </div>
        """,
        unsafe_allow_html=True
    )

exibir_logo_e_titulo_lado_a_lado()

# ========== Formulário com novos campos ==========
with st.form("formulario_processo"):
    nome_cliente = st.text_input("Nome do Advogado ou Empresa")
    email = st.text_input("E-mail para receber o relatório")
    numero = st.text_input("Número do processo")
    tipo = st.selectbox("Tipo do processo", ["Cível", "Trabalhista", "Penal", "Outro"])
    conferencia = st.radio("Tipo de relatório desejado:", ["Com Verificação", "Sem Verificação"])
    arquivo = st.file_uploader("Anexar arquivo do processo (PDF, DOCX)", type=["pdf", "docx"])

    enviado = st.form_submit_button("📤 Enviar processo")

    if enviado:
        if not (nome_cliente and email and numero and arquivo):
            st.warning("Por favor, preencha todos os campos obrigatórios.")
        else:
            salvar_processo(nome_cliente, email, numero, tipo, arquivo, conferencia)
            st.success("✅ Processo enviado com sucesso, em 48h o relatório será enviado para o seu e-mail!")
