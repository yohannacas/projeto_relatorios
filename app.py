import streamlit as st
import sqlite3
import os
import pandas as pd
import smtplib
import ssl
from email.message import EmailMessage
from dotenv import load_dotenv
import base64

# ========= CONFIGURAÇÕES =========
DB_PATH = "banco_dados.db"
SENHA_ADVOGADO = "123cas#@!adv"

# ========= AJUSTES INICIAIS =========
# Criar pastas se não existirem
os.makedirs("uploads", exist_ok=True)
os.makedirs("relatorios", exist_ok=True)

# Criar banco e tabela se não existirem
def inicializar_banco():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS processos (
            id TEXT PRIMARY KEY,
            nome_cliente TEXT,
            email TEXT,
            numero_processo TEXT,
            tipo TEXT,
            caminho_arquivo TEXT,
            data_envio TEXT,
            status TEXT,
            conferencia TEXT
        )
    """)
    conn.commit()
    conn.close()

inicializar_banco()

# ========= CARREGAR VARIÁVEIS SECRETAS =========
load_dotenv()
EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE")
SENHA_APP = os.getenv("SENHA_APP")

# ========= FUNÇÕES =========
def salvar_processo(nome_cliente, email, numero, tipo, arquivo, conferencia):
    from datetime import datetime
    import uuid

    processo_id = str(uuid.uuid4())
    extensao = arquivo.name.split(".")[-1]
    caminho_arquivo = f"uploads/{processo_id}.{extensao}"

    with open(caminho_arquivo, "wb") as f:
        f.write(arquivo.read())

    data_envio = datetime.now().isoformat()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO processos (id, nome_cliente, email, numero_processo, tipo, caminho_arquivo, data_envio, status, conferencia)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (processo_id, nome_cliente, email, numero, tipo, caminho_arquivo, data_envio, "pendente", conferencia))
    conn.commit()
    conn.close()

def carregar_processos_pendentes():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS processos (
            id TEXT PRIMARY KEY,
            nome_cliente TEXT,
            email TEXT,
            numero_processo TEXT,
            tipo TEXT,
            caminho_arquivo TEXT,
            data_envio TEXT,
            status TEXT,
            conferencia TEXT
        )
    """)
    conn.commit()

    cursor.execute("""
        SELECT id, nome_cliente, email, numero_processo, tipo, conferencia, data_envio, caminho_arquivo 
        FROM processos 
        WHERE status = 'pendente' 
        ORDER BY data_envio DESC
    """)
    dados = cursor.fetchall()
    colunas = [desc[0] for desc in cursor.description]
    conn.close()

    df = pd.DataFrame(dados, columns=colunas)
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

    with open(relatorio_path, "rb") as f:
        file_data = f.read()
        file_name = os.path.basename(relatorio_path)

    msg.add_attachment(file_data, maintype="application", subtype="octet-stream", filename=file_name)

    contexto = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=contexto) as smtp:
        smtp.login(EMAIL_REMETENTE, SENHA_APP)
        smtp.send_message(msg)

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

# ========= INTERFACE =========
st.sidebar.title("Navegação")
pagina = st.sidebar.selectbox("Escolha a página", ["Enviar Processo", "Área dos Advogados"])

if pagina == "Enviar Processo":
    exibir_logo_e_titulo_lado_a_lado()

    with st.form("formulario_processo"):
        nome_cliente = st.text_input("Nome ou nome da empresa")
        email = st.text_input("E-mail para receber o relatório")
        numero = st.text_input("Número do processo")
        tipo = st.selectbox("Tipo do processo", ["Cível", "Trabalhista", "Penal", "Outro"])
        conferencia = st.radio("Tipo de relatório desejado:", ["Com conferência", "Sem conferência"])
        arquivo = st.file_uploader("Anexar arquivo do processo (PDF, DOCX)", type=["pdf", "docx"])

        enviado = st.form_submit_button("📤 Enviar processo")

        if enviado:
            if not (nome_cliente and email and numero and arquivo):
                st.warning("Por favor, preencha todos os campos obrigatórios.")
            else:
                salvar_processo(nome_cliente, email, numero, tipo, arquivo, conferencia)
                st.success("✅ Processo enviado com sucesso!")

elif pagina == "Área dos Advogados":
    st.title("Área Interna - Advogados JUSREPORT")

    senha = st.text_input("Digite a senha de acesso:", type="password")

    if senha != SENHA_ADVOGADO:
        st.warning("Acesso restrito. Insira a senha correta para continuar.")
        st.stop()

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
