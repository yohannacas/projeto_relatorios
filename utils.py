import sqlite3
import os
from datetime import datetime
import uuid

def salvar_processo(nome_cliente, email, numero, tipo, arquivo, conferencia):
    conn = sqlite3.connect("banco_dados.db")
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

    processo_id = str(uuid.uuid4())
    extensao = os.path.splitext(arquivo.name)[1]
    caminho_arquivo = f"uploads/{processo_id}{extensao}"

    with open(caminho_arquivo, "wb") as f:
        f.write(arquivo.read())

    data_envio = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO processos (id, nome_cliente, email, numero_processo, tipo, caminho_arquivo, data_envio, status, conferencia)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        processo_id, nome_cliente, email, numero, tipo, caminho_arquivo, data_envio, "pendente", conferencia
    ))

    conn.commit()
    conn.close()
