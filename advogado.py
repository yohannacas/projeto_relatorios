import streamlit as st
import sqlite3
import os
import pandas as pd
import smtplib
import ssl
from email.message import EmailMessage
from dotenv import load_dotenv

# ========= CONFIGURAÇÕES =========
SENHA_CORRETA = "jus123"
DB_PATH = "banco_dados.db"

load_dotenv()
EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE")
SENHA_APP = os.getenv("SENHA_APP")

# ========= LOGIN =========
st.title("Área Interna - Advogados JUSREPORT")

senha = st.text_input("Digite a senha de acesso:", type="password")

if senha != SENHA_CORRETA:
    st.warning("Acesso restrito. Insira a senha correta para continuar.")
    st.stop()

# ========= FUNÇÕES =========
def carregar_processos_pendentes():
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT id, nome_cliente, email, numero_processo, tipo, conferencia, data_envio, caminho_arquivo 
        FROM processos 
        WHERE status = 'pendente' 
        ORDER BY data_envio DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def excluir_processo(processo_id, caminho_arquivo):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM processos WHERE id = ?", (processo_id,))
    conn.commit()
    conn.close()

    if os.path.exists(caminho_arquivo):
        os.remove(caminho_arquivo)

def finalizar_processo(processo_id, relatorio_path, email_cliente):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE processos SET status = 'finalizado' WHERE id = ?", (processo_id,))
    conn.commit()
    conn.close()

    enviar_email_cliente(email_cliente, relatorio_path)

def enviar_email_cliente(destinatario, relatorio_path):
    assunto = "Seu Relatório JUSREPORT está pronto!"
    corpo = """
    Prezado cliente,

    Segue em anexo o relatório solicitado.

    Atenciosamente,
    Equipe JUSREPORT
    """

    msg = EmailMessage()
    msg["Subject"] = assunto
    msg["From"] = EMAIL_REMETENTE
    msg["To"] = destinatario
    msg.set_content(corpo)

    # Anexar o relatório
    with open(relatorio_path, "rb") as f:
        file_data = f.read()
        file_name = os.path.basename(relatorio_path)

    msg.add_attachment(file_data, maintype="application", subtype="octet-stream", filename=file_name)

    contexto = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=contexto) as smtp:
        smtp.login(EMAIL_REMETENTE, SENHA_APP)
        smtp.send_message(msg)

# ========= INTERFACE =========
st.subheader("📋 Processos Pendentes")

df = carregar_processos_pendentes()

if df.empty:
    st.info("Nenhum processo pendente no momento.")
else:
    for i, row in df.iterrows():
        st.markdown("---")
        st.markdown(f"**Cliente:** {row['nome_cliente']}")
        st.markdown(f"**E-mail:** {row['email']}")
        st.markdown(f"**Número do processo:** {row['numero_processo']}")
        st.markdown(f"**Tipo:** {row['tipo']}")
        st.markdown(f"**Relatório:** {row['conferencia']}")
        st.markdown(f"**Data de envio:** {row['data_envio'][:19].replace('T', ' ')}")

        col1, col2 = st.columns([2, 1])

        with col1:
            with open(row["caminho_arquivo"], "rb") as file:
                st.download_button(
                    label="📥 Baixar arquivo do cliente",
                    data=file,
                    file_name=os.path.basename(row["caminho_arquivo"]),
                    mime="application/octet-stream",
                    key=f"download_{row['id']}"
                )

        with col2:
            if st.button("🗑️ Excluir processo", key=f"excluir_{row['id']}"):
                excluir_processo(row['id'], row["caminho_arquivo"])
                st.success(f"Processo de {row['nome_cliente']} excluído.")
                st.rerun()

        st.markdown("**Upload do relatório final:**")
        uploaded_relatorio = st.file_uploader(f"📤 Enviar relatório final para {row['nome_cliente']}", type=["pdf", "docx"], key=f"upload_{row['id']}")

        if uploaded_relatorio:
            caminho_relatorio = f"relatorios/{row['id']}_{uploaded_relatorio.name}"
            with open(caminho_relatorio, "wb") as f:
                f.write(uploaded_relatorio.read())

            finalizar_processo(row['id'], caminho_relatorio, row['email'])
            st.success(f"Relatório enviado para {row['nome_cliente']} com sucesso!")
            st.rerun()
