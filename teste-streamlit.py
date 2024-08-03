import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import sqlite3

# Funções auxiliares para manipulação do banco de dados
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT,
            data TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            usuario TEXT PRIMARY KEY,
            senha TEXT
        )
    ''')
    conn.commit()
    conn.close()

def autenticar_usuario(usuario, senha):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM usuarios WHERE usuario = ? AND senha = ?', (usuario, senha))
    user = cursor.fetchone()
    conn.close()
    return user is not None

def registrar_usuario(usuario, senha):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO usuarios (usuario, senha) VALUES (?, ?)', (usuario, senha))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def adicionar_entrada(usuario):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    hoje = datetime.now().date()
    cursor.execute('SELECT * FROM registros WHERE usuario = ? AND DATE(data) = ?', (usuario, hoje))
    if cursor.fetchone() is None:
        cursor.execute('INSERT INTO registros (usuario, data) VALUES (?, ?)', (usuario, datetime.now()))
        conn.commit()
    conn.close()

def obter_dados():
    conn = sqlite3.connect('database.db')
    df = pd.read_sql_query('SELECT * FROM registros', conn)
    conn.close()
    return df

def atualizar_tabelas(df):
    df['Data'] = pd.to_datetime(df['data'])
    df['Dia'] = df['Data'].dt.date
    df['Semana'] = df['Data'].apply(lambda x: (x - timedelta(days=x.weekday() + 1)).isocalendar()[1])
    
    dias_concluidos = df.groupby('usuario')['Dia'].nunique().reset_index(name='Dias Concluidos')
    semanas_concluidas = df[df.groupby(['usuario', 'Semana'])['Dia'].transform('nunique') >= 5].groupby('usuario')['Semana'].nunique().reset_index(name='Semanas Concluidas')
    
    resumo = pd.merge(dias_concluidos, semanas_concluidas, on='usuario', how='left').fillna(0)
    resumo['Semanas Concluidas'] = resumo['Semanas Concluidas'].astype(int)
    resumo['Total de Dias'] = df.groupby('usuario')['Dia'].count().values
    resumo = resumo.sort_values(by=['Semanas Concluidas', 'Total de Dias'], ascending=False)
    return resumo

# Inicializando o banco de dados
init_db()

# Definição da interface de login e registro
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    escolha = st.radio("Escolha uma opção", ["Login", "Registrar"])
    
    if escolha == "Registrar":
        novo_usuario = st.text_input("Novo Usuário")
        nova_senha = st.text_input("Nova Senha", type="password")
        if st.button("Registrar"):
            if registrar_usuario(novo_usuario, nova_senha):
                st.success("Usuário registrado com sucesso! Faça o login.")
            else:
                st.error("Usuário já existe. Escolha um nome de usuário diferente.")
    
    elif escolha == "Login":
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        if st.button("Login"):
            if autenticar_usuario(usuario, senha):
                st.session_state.logged_in = True
                st.session_state.usuario = usuario
            else:
                st.error("Usuário ou senha inválidos")
else:
    st.write(f"Bem-vindo, {st.session_state.usuario}!")
    
    if st.button("Registrar o dia!"):
        adicionar_entrada(st.session_state.usuario)
        st.success("Dia registrado!")

    # Atualizando e mostrando a tabela de resumo
    df = obter_dados()
    resumo = atualizar_tabelas(df)
    st.write("Tabela do ranking:")
    st.table(resumo)
    
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.usuario = None
