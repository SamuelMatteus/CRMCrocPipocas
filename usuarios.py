# models/usuarios.py
import os
import pandas as pd
import hashlib
import streamlit as st

ARQUIVO_USUARIOS = "usuarios.csv"

EMAILS_PERMITIDOS = [
    "gerente@croc.com.br"
]

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def carregar_usuarios():
    if os.path.exists(ARQUIVO_USUARIOS):
        return pd.read_csv(ARQUIVO_USUARIOS)
    return pd.DataFrame(columns=["email", "senha_hash"])

def salvar_usuarios(df):
    df.to_csv(ARQUIVO_USUARIOS, index=False)

def autenticar_usuario():
    usuarios_df = carregar_usuarios()
    st.image("images/logo_croc_pipocas.jpg", width=250)
    st.title("🔐 Login")

    email = st.text_input("E-mail")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if email not in EMAILS_PERMITIDOS:
            st.error("E-mail não autorizado.")
            return

        senha_hash = hash_senha(senha)

        if email in usuarios_df["email"].values:
            usuario = usuarios_df[usuarios_df["email"] == email].iloc[0]
            if senha_hash == usuario["senha_hash"]:
                st.session_state.usuario_logado = email
                st.success("Login realizado com sucesso!")
                st.experimental_rerun()
            else:
                st.error("Senha incorreta.")
        else:
            novo = pd.DataFrame([{"email": email, "senha_hash": senha_hash}])
            usuarios_df = pd.concat([usuarios_df, novo], ignore_index=True)
            salvar_usuarios(usuarios_df)
            st.success("Senha criada com sucesso! Você está logado.")
            st.session_state.usuario_logado = email
            st.experimental_rerun()
