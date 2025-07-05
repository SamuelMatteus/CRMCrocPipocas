import streamlit as st
import pandas as pd
import os
import json
import hashlib
import re
from enum import Enum
from datetime import datetime, date, time, timedelta
import plotly.express as px

# --- Enums --- Estabelecidos

class ClassificacaoProduto(Enum):
    PIPOCA = 'Pipoca'
    BEBIDAS = 'Bebidas'
    OUTROS = 'Outros'

class TipoPedido(Enum):
    VENDA_BALCAO = "Retirada"
    PEDIDO_ENTREGA = "Entrega/Delivery"

class ClassificacaoDespesa(Enum):
    CUSTOS_PRODUCAO = "Custos de Produção"
    IMPREVISTOS = "Imprevistos"
    MATERIA_PRIMA = "Matéria Prima"
    DESPESAS_REGULARES = "Despesas Regulares"

# --- Constantes e arquivos ---

ARQUIVO_USUARIOS = "usuarios.csv"
EMAILS_PERMITIDOS = ["gerente@croc.com.br"]

DATA_PRODUTOS = "produtos.csv"
DATA_CLIENTES = "clientes.csv"
DATA_PEDIDOS = "pedidos.csv"
DATA_DESPESAS = "despesas.csv"

# --- Funções gerais ---

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
                st.rerun()
            else:
                st.error("Senha incorreta.")
        else:
            novo = pd.DataFrame([{"email": email, "senha_hash": senha_hash}])
            usuarios_df = pd.concat([usuarios_df, novo], ignore_index=True)
            salvar_usuarios(usuarios_df)
            st.success("Senha criada com sucesso! Você está logado.")
            st.session_state.usuario_logado = email
            st.rerun()


def get_next_id(df):
    if df.empty:
        return 1
    return int(df["ID"].max()) + 1

def normalize_num(text):
    if pd.isna(text):
        return ""
    return re.sub(r'\D', '', str(text))

def format_cpf(cpf_raw):
    digits = re.sub(r'\D', '', cpf_raw)
    if len(digits) != 11:
        return cpf_raw
    return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"

def format_telefone(tel_raw):
    digits = re.sub(r'\D', '', tel_raw)
    if len(digits) == 11:
        return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
    elif len(digits) == 10:
        return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
    else:
        return tel_raw

# --- Carregar e salvar dados ---

def carregar_produtos():
    if os.path.exists(DATA_PRODUTOS):
        df = pd.read_csv(DATA_PRODUTOS)
        if "Classificação" not in df.columns:
            df["Classificação"] = ""
        return df
    else:
        return pd.DataFrame(columns=["ID", "Nome", "Classificação", "Preço", "Quantidade"])

def salvar_produtos(df):
    df.to_csv(DATA_PRODUTOS, index=False)

def carregar_clientes():
    if os.path.exists(DATA_CLIENTES):
        return pd.read_csv(DATA_CLIENTES)
    else:
        return pd.DataFrame(columns=["ID", "Nome", "CPF", "Endereço", "Telefone"])

def salvar_clientes(df):
    df.to_csv(DATA_CLIENTES, index=False)

def carregar_pedidos():
    if os.path.exists(DATA_PEDIDOS):
        return pd.read_csv(DATA_PEDIDOS)
    return pd.DataFrame(columns=["ID", "DataHora", "Tipo", "ClienteID", "ValorItens", "TaxaEntrega", "ValorTotal", "ItensJSON"])

def salvar_pedidos(df):
    df.to_csv(DATA_PEDIDOS, index=False)

def carregar_despesas():
    if os.path.exists(DATA_DESPESAS):
        df = pd.read_csv(DATA_DESPESAS)
        expected_cols = ["ID", "Descrição", "Classificação", "Valor", "Data"]
        for col in expected_cols:
            if col not in df.columns:
                df[col] = ""
        return df
    else:
        return pd.DataFrame(columns=["ID", "Descrição", "Classificação", "Valor", "Data"])

def salvar_despesas(df):
    df.to_csv(DATA_DESPESAS, index=False)

# --- Telas ---

def tela_produtos():
    st.title("📦 Cadastro de Produtos")

    df = carregar_produtos()

    nome = st.text_input("Nome do produto")
    preco = st.number_input("Preço (R$)", min_value=0.0, format="%.2f")
    quantidade = st.number_input("Quantidade em estoque", min_value=0, step=1)
    opcao = st.selectbox(
        "Classificação",
        options=list(ClassificacaoProduto),
        format_func=lambda x: x.value
    )

    if st.button("Cadastrar"):
        if not nome:
            st.error("O nome do produto é obrigatório.")
        else:
            novo_id = get_next_id(df)
            novo_produto = {
                "ID": novo_id,
                "Nome": nome,
                "Classificação": opcao.value,
                "Preço": preco,
                "Quantidade": quantidade
            }
            df = pd.concat([df, pd.DataFrame([novo_produto])], ignore_index=True)
            salvar_produtos(df)
            st.success(f"Produto '{nome}' cadastrado com sucesso!")
            st.rerun()

    st.subheader("Produtos Cadastrados")

    if df.empty:
        st.info("Nenhum produto cadastrado.")
    else:
        if "produto_editando" not in st.session_state:
            st.session_state.produto_editando = None
        if "edits_temp" not in st.session_state:
            st.session_state.edits_temp = {}

        col1, col2, col3, col4, col5, col6 = st.columns([3, 2, 2, 2, 1, 1])
        col1.markdown("**Nome**")
        col2.markdown("**Preço (R$)**")
        col3.markdown("**Qtd. Estoque**")
        col4.markdown("**Categoria**")
        col5.markdown("")
        col6.markdown("")

        for idx, produto in df.iterrows():
            col1, col2, col3, col4, col5, col6 = st.columns([3, 2, 2, 2, 1, 1])
            pid = produto["ID"]

            if st.session_state.produto_editando == pid:
                nome_edit = col1.text_input(f"nome_{pid}", value=st.session_state.edits_temp.get(f"nome_{pid}", produto["Nome"]), label_visibility="hidden")
                preco_edit = col2.number_input(
                    f"preco_{pid}",
                    min_value=0.0,
                    format="%.2f",
                    value=float(st.session_state.edits_temp.get(f"preco_{pid}", produto["Preço"])),
                    label_visibility="hidden"
                )
                quantidade_edit = col3.number_input(
                    f"qtd_{pid}",
                    min_value=0,
                    step=1,
                    value=int(st.session_state.edits_temp.get(f"qtd_{pid}", produto["Quantidade"])),
                    label_visibility="hidden"
                )
                col4.write(produto["Classificação"])

                if col5.button("💾", key=f"save_{pid}"):
                    df.loc[df["ID"] == pid, "Nome"] = nome_edit
                    df.loc[df["ID"] == pid, "Preço"] = preco_edit
                    df.loc[df["ID"] == pid, "Quantidade"] = quantidade_edit
                    salvar_produtos(df)
                    st.session_state.produto_editando = None
                    st.session_state.edits_temp = {}
                    st.success(f"Produto '{nome_edit}' atualizado com sucesso!")
                    st.rerun()

                if col6.button("✖", key=f"cancel_{pid}"):
                    st.session_state.produto_editando = None
                    st.session_state.edits_temp = {}
                    st.rerun()

            else:
                col1.write(produto["Nome"])
                col2.write(f"R$ {produto['Preço']:.2f}")
                col3.write(produto["Quantidade"])
                col4.write(produto["Classificação"])

                if col5.button("✏️", key=f"edit_{pid}"):
                    st.session_state.produto_editando = pid
                    st.session_state.edits_temp = {
                        f"nome_{pid}": produto["Nome"],
                        f"preco_{pid}": float(produto["Preço"]),
                        f"qtd_{pid}": int(produto["Quantidade"])
                    }
                    st.rerun()

                if col6.button("🗑️", key=f"del_{pid}"):
                    df = df[df["ID"] != pid]
                    salvar_produtos(df)
                    st.success(f"Produto '{produto['Nome']}' excluído com sucesso!")
                    st.rerun()

def tela_clientes():
    st.title("👤 Cadastro de Clientes")

    df = carregar_clientes()

    nome = st.text_input("Nome do cliente")
    cpf = st.text_input("CPF (somente números)")
    endereco = st.text_input("Endereço")
    telefone = st.text_input("Telefone")

    if st.button("Cadastrar cliente"):
        if not nome:
            st.error("O nome do cliente é obrigatório.")
        else:
            cpf_normalizado = normalize_num(cpf)
            telefone_normalizado = normalize_num(telefone)

            cpfs_existentes = df["CPF"].apply(normalize_num).tolist()
            telefones_existentes = df["Telefone"].apply(normalize_num).tolist()

            if cpf_normalizado in cpfs_existentes:
                st.error("Este CPF já está cadastrado.")
            elif telefone_normalizado in telefones_existentes:
                st.error("Este telefone já está cadastrado.")
            else:
                cpf_fmt = format_cpf(cpf)
                telefone_fmt = format_telefone(telefone)

                novo_id = get_next_id(df)
                novo_cliente = {
                    "ID": novo_id,
                    "Nome": nome,
                    "CPF": cpf_fmt,
                    "Endereço": endereco,
                    "Telefone": telefone_fmt
                }
                df = pd.concat([df, pd.DataFrame([novo_cliente])], ignore_index=True)
                salvar_clientes(df)
                st.success(f"Cliente '{nome}' cadastrado com sucesso!")
                st.rerun()

    st.subheader("Clientes cadastrados")

    if df.empty:
        st.info("Nenhum cliente cadastrado.")
    else:
        st.dataframe(df)

def tela_pedidos():
    st.title("🛒 Cadastrar Pedidos")

    produtos_df = carregar_produtos()
    clientes_df = carregar_clientes()
    pedidos_df = carregar_pedidos()

    tipo_pedido = st.radio(
        "Tipo de Venda",
        options=list(TipoPedido),
        format_func=lambda x: x.value
    )

    cliente_selecionado = None
    if tipo_pedido == TipoPedido.PEDIDO_ENTREGA:
        st.subheader("Cliente")

        if clientes_df.empty:
            st.warning("Nenhum cliente cadastrado. Cadastre clientes na aba 'Clientes' antes de fazer pedidos de entrega.")
            st.stop()
        else:
            selecionado = st.selectbox("Selecione o cliente", options=clientes_df["Nome"].tolist())
            cliente_selecionado = clientes_df[clientes_df["Nome"] == selecionado].iloc[0]

    st.subheader("Itens do pedido")

    if produtos_df.empty:
        st.info("Nenhum produto cadastrado.")
    else:
        itens_pedido = []

        for idx, produto in produtos_df.iterrows():
            qtd = st.number_input(
                f"{produto['Nome']} (R$ {produto['Preço']:.2f}) - Estoque: {produto['Quantidade']}",
                min_value=0,
                max_value=int(produto['Quantidade']),
                step=1,
                key=f"qtd_{produto['ID']}"
            )
            if qtd > 0:
                itens_pedido.append({
                    "produto_id": int(produto['ID']),
                    "nome": produto['Nome'],
                    "quantidade": qtd,
                    "preco_unitario": float(produto['Preço'])
                })

        valor_itens = sum(item['quantidade'] * item['preco_unitario'] for item in itens_pedido)

        taxa_entrega = 0.0
        if tipo_pedido == TipoPedido.PEDIDO_ENTREGA:
            if st.checkbox("Possui taxa de entrega?"):
                taxa_entrega = st.number_input("Valor da taxa de entrega (R$)", min_value=0.0, format="%.2f")

        valor_total = valor_itens + taxa_entrega

        st.markdown(f"**Subtotal:** R$ {valor_itens:.2f}")
        st.markdown(f"**Taxa de entrega:** R$ {taxa_entrega:.2f}")
        st.markdown(f"### Valor total: R$ {valor_total:.2f}")

        if st.button("Registrar pedido"):
            if not itens_pedido:
                st.error("Selecione ao menos um item.")
            elif tipo_pedido == TipoPedido.PEDIDO_ENTREGA and cliente_selecionado is None:
                st.error("Selecione um cliente para pedidos de entrega.")
            else:
                novo_id = get_next_id(pedidos_df)
                pedido = {
                    "ID": novo_id,
                    "DataHora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Tipo": tipo_pedido.value,
                    "ClienteID": cliente_selecionado["ID"] if cliente_selecionado is not None else "",
                    "ValorItens": valor_itens,
                    "TaxaEntrega": taxa_entrega,
                    "ValorTotal": valor_total,
                    "ItensJSON": json.dumps(itens_pedido, ensure_ascii=False)
                }
                pedidos_df = pd.concat([pedidos_df, pd.DataFrame([pedido])], ignore_index=True)
                salvar_pedidos(pedidos_df)
                st.success(f"Pedido #{novo_id} registrado com sucesso!")
                st.rerun()

    st.subheader("📆 Pedidos de hoje")

    hoje = datetime.now().strftime("%Y-%m-%d")
    pedidos_hoje = pedidos_df[pedidos_df["DataHora"].str.startswith(hoje)]

    if pedidos_hoje.empty:
        st.info("Nenhum pedido registrado hoje.")
    else:
        pedidos_mostrar = pedidos_hoje.copy()

        clientes_para_merge = clientes_df[["ID", "Nome"]].rename(columns={"ID": "ClienteID_Cliente", "Nome": "Cliente"})

        pedidos_mostrar = pedidos_mostrar.merge(
            clientes_para_merge,
            left_on="ClienteID",
            right_on="ClienteID_Cliente",
            how="left"
        )

        pedidos_mostrar["ValorTotal"] = pedidos_mostrar["ValorTotal"].apply(lambda v: f"R$ {v:.2f}")

        pedidos_mostrar = pedidos_mostrar[["ID", "DataHora", "Tipo", "Cliente", "ValorTotal"]]

        st.dataframe(pedidos_mostrar, use_container_width=True)

def tela_despesas():
    st.title("💸 Cadastro de Despesas")

    despesas_df = carregar_despesas()

    descricao = st.text_input("Descrição")
    classificacao = st.selectbox(
        "Classificação",
        options=list(ClassificacaoDespesa),
        format_func=lambda x: x.value
    )
    valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
    data = st.date_input("Data", value=date.today())

    if st.button("Cadastrar despesa"):
        if not descricao:
            st.error("Descrição é obrigatória.")
        else:
            novo_id = get_next_id(despesas_df)
            nova_despesa = {
                "ID": novo_id,
                "Descrição": descricao,
                "Classificação": classificacao.value,
                "Valor": valor,
                "Data": data.strftime("%Y-%m-%d")
            }
            despesas_df = pd.concat([despesas_df, pd.DataFrame([nova_despesa])], ignore_index=True)
            salvar_despesas(despesas_df)
            st.success(f"Despesa '{descricao}' cadastrada com sucesso!")
            st.rerun()

    st.subheader("Despesas cadastradas")

    if despesas_df.empty:
        st.info("Nenhuma despesa cadastrada.")
    else:
        st.dataframe(despesas_df.sort_values(by="Data", ascending=False), use_container_width=True)

# --- APP principal ---

if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None

if not st.session_state.usuario_logado:
    autenticar_usuario()
    st.stop()

st.title("🧑‍💼 Croc Pipocas - Gerente")

pedidos_df = carregar_pedidos()
despesas_df = carregar_despesas()

# Formata datas para datetime
pedidos_df["DataHora"] = pd.to_datetime(pedidos_df["DataHora"], errors="coerce")
despesas_df["Data"] = pd.to_datetime(despesas_df["Data"], errors="coerce")

hoje = datetime.now().date()
data_30dias_atras = hoje - timedelta(days=30)

# Pedidos do dia
pedidos_hoje = pedidos_df[pedidos_df["DataHora"].dt.date == hoje]

total_pedidos_hoje = len(pedidos_hoje)
venda_balcao_hoje = len(pedidos_hoje[pedidos_hoje["Tipo"] == TipoPedido.VENDA_BALCAO.value])
pedido_entrega_hoje = len(pedidos_hoje[pedidos_hoje["Tipo"] == TipoPedido.PEDIDO_ENTREGA.value])
receita_hoje = pedidos_hoje["ValorTotal"].sum()

# Pedidos últimos 30 dias
pedidos_30dias = pedidos_df[
    (pedidos_df["DataHora"].dt.date >= data_30dias_atras) & (pedidos_df["DataHora"].dt.date <= hoje)]

total_pedidos_30dias = len(pedidos_30dias)
receita_30dias = pedidos_30dias["ValorTotal"].sum()

# Exibindo no Streamlit
st.header("📊 Resumo dos Pedidos")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Pedidos de Hoje")
    st.write(f"Total: **{total_pedidos_hoje}**")
    st.write(f"Venda Balcão: **{venda_balcao_hoje}**")
    st.write(f"Entrega: **{pedido_entrega_hoje}**")
    st.write(f"Receita: R$ **{receita_hoje:.2f}**")

with col2:
    st.subheader("Pedidos Últimos 30 Dias")
    st.write(f"Total: **{total_pedidos_30dias}**")
    st.write(f"Receita: R$ **{receita_30dias:.2f}**")

# --- Gráfico pizza de despesas ---

if despesas_df.empty:
    st.info("Nenhuma despesa cadastrada para exibir gráfico.")
else:
    # Agrupa por classificação e soma os valores
    df_graf = despesas_df.groupby("Classificação")["Valor"].sum().reset_index()

    fig = px.pie(
        df_graf,
        names="Classificação",
        values="Valor",
        title="Distribuição das Despesas por Classificação",
        hole=0.3,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    st.plotly_chart(fig, use_container_width=True)

menu = st.sidebar.radio(
    "Navegação",
    ("Pedidos", "Clientes", "Produtos", "Despesas")
)

if menu == "Pedidos":
    tela_pedidos()
elif menu == "Clientes":
    tela_clientes()
elif menu == "Produtos":
    tela_produtos()
elif menu == "Despesas":
    tela_despesas()
