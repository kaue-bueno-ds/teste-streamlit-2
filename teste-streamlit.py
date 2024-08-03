import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

# Funções auxiliares
def autenticar_usuario(usuario, senha):
    return usuario == "admin" and senha == "password"

def adicionar_entrada(usuario, df):
    nova_entrada = {'Usuario': usuario, 'Data': datetime.now()}
    df = df.append(nova_entrada, ignore_index=True)
    return df

def atualizar_tabelas(df):
    # Calculando os dias únicos e as semanas concluídas
    df['Data'] = pd.to_datetime(df['Data'])
    df['Dia'] = df['Data'].dt.date
    df['Semana'] = df['Data'].apply(lambda x: (x - timedelta(days=x.weekday() + 1)).isocalendar()[1])
    
    dias_concluidos = df.groupby('Usuario')['Dia'].nunique().reset_index(name='Dias Concluidos')
    semanas_concluidas = df[df.groupby(['Usuario', 'Semana'])['Dia'].transform('nunique') >= 5].groupby('Usuario')['Semana'].nunique().reset_index(name='Semanas Concluidas')
    
    resumo = pd.merge(dias_concluidos, semanas_concluidas, on='Usuario', how='left').fillna(0)
    resumo['Semanas Concluidas'] = resumo['Semanas Concluidas'].astype(int)
    return resumo

# Definição da interface de login
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Login"):
        if autenticar_usuario(usuario, senha):
            st.session_state.logged_in = True
            st.session_state.usuario = usuario
            st.session_state.df = pd.DataFrame(columns=['Usuario', 'Data'])
        else:
            st.error("Usuário ou senha inválidos")
else:
    st.write(f"Bem-vindo, {st.session_state.usuario}!")
    
    if st.button("Apertar Botão"):
        st.session_state.df = adicionar_entrada(st.session_state.usuario, st.session_state.df)
        st.success("Botão apertado!")

    # Atualizando e mostrando a tabela de resumo
    resumo = atualizar_tabelas(st.session_state.df)
    st.write("Tabela de Resumo:")
    st.table(resumo)
