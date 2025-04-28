import streamlit as st
import sqlite3
import os
import pandas as pd
import smtplib
import ssl
from email.message import EmailMessage
from dotenv import load_dotenv
import base64
from datetime import datetime
import uuid
from io import BytesIO

# ========= CONFIGURAÇÕES =========
DB_PATH = "banco_dados.db"
UPLOADS_DIR = "uploads"
RELATORIOS_DIR = "relatorios"

# ========= AJUSTES INICIAIS =========
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(RELATORIOS_DIR, exist_ok=True)

# ========= CARREGAR VARIÁVEIS SECRETAS =========
load_dotenv()
EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE")
SENHA_APP = os.getenv("SENHA_APP")
SENHA_ADVOGADO = os.getenv("SENHA_ADVOGADO", "123cas#@!adv")

# ========= FUNÇÕES =========
# (funções continuam iguais)

# ========= APP =========

inicializar_banco()

st.sidebar.title("NAVEGAÇÃO")
pagina = st.sidebar.selectbox("ESCOLHA A PÁGINA", ["\u00c1REA DO CLIENTE", "\u00c1REA JUSREPORT"])

if pagina == "\u00c1REA DO CLIENTE":
    exibir_logo_e_titulo_lado_a_lado()

    with st.form("formulario_processo"):
        nome_cliente = st.text_input("Nome ou nome da empresa")
        email = st.text_input("E-mail para receber o relatório")
        numero = st.text_input("Número do processo")
        tipo = st.selectbox("Tipo do processo", ["Cível", "Trabalhista", "Penal", "Outro"])
        conferencia = st.radio("Tipo de relatório desejado:", ["Com conferência", "Sem conferência"])
        arquivo = st.file_uploader("Anexar arquivo do processo (PDF, DOCX)", type=["pdf", "docx"])

        enviado = st.form_submit_button("ENVIAR PROCESSO")

        if enviado:
            if not (nome_cliente and email and numero and arquivo):
                st.warning("Por favor, preencha todos os campos obrigatórios.")
            else:
                salvar_processo(nome_cliente, email, numero, tipo, arquivo, conferencia)
                st.success("Processo enviado com sucesso!")

elif pagina == "\u00c1REA JUSREPORT":
    st.title("\u00c1REA INTERNA - JUSREPORT")

    senha = st.text_input("DIGITE A SENHA DE ACESSO:", type="password")

    if senha != SENHA_ADVOGADO:
        st.warning("ACESSO RESTRITO. INSIRA A SENHA CORRETA PARA CONTINUAR.")
        st.stop()

    # Processos Pendentes
    st.markdown("<h2 style='text-transform: uppercase; font-size: 28px;'>Processos Pendentes</h2>", unsafe_allow_html=True)
    df = carregar_processos_pendentes()

    if df.empty:
        st.info("Nenhum processo pendente no momento.")
    else:
        for i, row in df.iterrows():
            st.markdown("---")
            st.markdown(f"**CLIENTE:** {row['nome_cliente']}")
            st.markdown(f"**E-MAIL:** {row['email']}")
            st.markdown(f"**NÚMERO DO PROCESSO:** {row['numero_processo']}")
            st.markdown(f"**TIPO:** {row['tipo']}")
            st.markdown(f"**RELATÓRIO:** {row['conferencia']}")
            st.markdown(f"**DATA DE ENVIO:** {row['data_envio'][:19].replace('T', ' ')}")

            col1, col2 = st.columns([2, 1])

            with col1:
                with open(row["caminho_arquivo"], "rb") as file:
                    st.download_button(
                        label="BAIXAR ARQUIVO DO CLIENTE",
                        data=file,
                        file_name=os.path.basename(row["caminho_arquivo"]),
                        mime="application/octet-stream",
                        key=f"download_{row['id']}"
                    )

            with col2:
                if st.button("EXCLUIR PROCESSO", key=f"excluir_{row['id']}"):
                    excluir_processo(row['id'], row["caminho_arquivo"])
                    st.success(f"Processo de {row['nome_cliente']} excluído.")
                    st.rerun()

            st.markdown("**UPLOAD DO RELATÓRIO FINAL:**")
            uploaded_relatorio = st.file_uploader(f"ENVIAR RELATÓRIO FINAL PARA {row['nome_cliente']}", type=["pdf", "docx"], key=f"upload_{row['id']}" )

            if uploaded_relatorio:
                caminho_relatorio = f"{RELATORIOS_DIR}/{row['id']}_{uploaded_relatorio.name}"
                with open(caminho_relatorio, "wb") as f:
                    f.write(uploaded_relatorio.read())

                finalizar_processo(row['id'], caminho_relatorio, row['email'], row['numero_processo'])
                st.success(f"Relatório enviado para {row['nome_cliente']} com sucesso!")
                st.rerun()

    # Relatórios Finalizados
    st.markdown("<h2 style='text-transform: uppercase; font-size: 28px;'>Relatórios Finalizados</h2>", unsafe_allow_html=True)
    df_finalizados = carregar_processos_finalizados()

    if df_finalizados.empty:
        st.info("Nenhum relatório finalizado encontrado ainda.")
    else:
        for i, row in df_finalizados.iterrows():
            st.markdown("---")
            st.markdown(f"**CLIENTE:** {row['nome_cliente']}")
            st.markdown(f"**E-MAIL:** {row['email']}")
            st.markdown(f"**NÚMERO DO PROCESSO:** {row['numero_processo']}")
            st.markdown(f"**DATA DE ENVIO:** {row['data_envio'][:19].replace('T', ' ')}")

            with open(row["caminho_arquivo"], "rb") as file:
                st.download_button(
                    label="BAIXAR RELATÓRIO FINALIZADO",
                    data=file,
                    file_name=os.path.basename(row["caminho_arquivo"]),
                    mime="application/octet-stream",
                    key=f"download_finalizado_{i}"
                )

    # Relatório Mensal
    st.markdown("<h2 style='text-transform: uppercase; font-size: 28px;'>Relatório Mensal de Processos por Cliente</h2>", unsafe_allow_html=True)
    df_contagem = carregar_contagem_processos_mensal()
    if not df_contagem.empty:
        st.dataframe(df_contagem)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_contagem.to_excel(writer, index=False, sheet_name='RelatorioMensal')
        st.download_button(
            label="BAIXAR RELATÓRIO EM EXCEL",
            data=output.getvalue(),
            file_name="relatorio_mensal_processos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("Nenhum processo enviado ainda para gerar o relatório.")
