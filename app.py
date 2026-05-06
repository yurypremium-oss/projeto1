import streamlit as st
import sqlite3
import pandas as pd
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Personal Pro App", layout="centered")

# --- CONEXÃO COM BANCO DE DADOS ---
conn = sqlite3.connect('sistema_personal.db', check_same_thread=False)
c = conn.cursor()

# --- ARQUIVO DE DADOS ---
ARQUIVO_USUARIOS = 'informaçoes.txt'

def create_tables():
    # Tabela de Treinos
    c.execute('''CREATE TABLE IF NOT EXISTS treinos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    username_aluno TEXT, 
                    exercicio TEXT, 
                    series TEXT, 
                    video_url TEXT)''')
    
    # Tabela de Mensagens
    c.execute('''CREATE TABLE IF NOT EXISTS mensagens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    remetente TEXT, 
                    destinatario TEXT, 
                    texto TEXT)''')
    conn.commit()

create_tables()

def carregar_usuarios():
    usuarios = []
    if os.path.exists(ARQUIVO_USUARIOS):
        with open(ARQUIVO_USUARIOS, 'r', encoding='utf-8') as f:
            for linha in f:
                if linha.strip():
                    partes = linha.strip().split(',')
                    if len(partes) == 4:
                        usuarios.append({
                            'nome': partes[0],
                            'username': partes[1],
                            'password': partes[2],
                            'tipo': partes[3]
                        })
    return usuarios

def salvar_usuario(nome, username, password, tipo):
    usuarios = carregar_usuarios()
    # Verificar se username já existe
    for u in usuarios:
        if u['username'] == username:
            return False  # Já existe
    # Adicionar novo usuário
    with open(ARQUIVO_USUARIOS, 'a', encoding='utf-8') as f:
        f.write(f"{nome},{username},{password},{tipo}\n")
    return True

def atualizar_usuario(username_antigo, nome_novo, password_novo):
    usuarios = carregar_usuarios()
    for u in usuarios:
        if u['username'] == username_antigo:
            u['nome'] = nome_novo
            u['password'] = password_novo
            break
    # Reescrever o arquivo
    with open(ARQUIVO_USUARIOS, 'w', encoding='utf-8') as f:
        for u in usuarios:
            f.write(f"{u['nome']},{u['username']},{u['password']},{u['tipo']}\n")
    return True

def criar_usuario_padrao():
    usuarios = carregar_usuarios()
    admin_existe = any(u['username'] == 'admin' for u in usuarios)
    if not admin_existe:
        salvar_usuario('Professor Master', 'admin', 'admin123', 'Professor')

criar_usuario_padrao()

# --- ESTADO DA SESSÃO ---
if 'logado' not in st.session_state:
    st.session_state['logado'] = False
if 'user_data' not in st.session_state:
    st.session_state['user_data'] = None

# --- FUNÇÕES DE AUXÍLIO ---
def login_user(user, password):
    usuarios = carregar_usuarios()
    for u in usuarios:
        if u['username'] == user and u['password'] == password:
            return (u['nome'], u['username'], u['tipo'])
    return None

# --- INTERFACE PRINCIPAL ---
if not st.session_state['logado']:
    st.title("🔐 Acesso ao Sistema")
    tab_l, tab_i = st.tabs(["Login", "Informações"])
    
    with tab_l:
        user = st.text_input("Usuário")
        password = st.text_input("Senha", type='password')
        if st.button("Entrar"):
            dados = login_user(user, password)
            if dados:
                st.session_state['logado'] = True
                st.session_state['user_data'] = dados
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")
    with tab_i:
        st.info("Login padrão do professor: admin | Senha: admin123")

else:
    nome_usuario, username_logado, tipo_usuario = st.session_state['user_data']
    
    st.sidebar.title(f"Bem-vindo, {nome_usuario}")
    st.sidebar.write(f"Perfil: {tipo_usuario}")
    if st.sidebar.button("Sair"):
        st.session_state['logado'] = False
        st.rerun()

    # --- ÁREA DO PROFESSOR ---
    if tipo_usuario == "Professor":
        menu = ["Cadastrar Aluno", "Gerenciar Alunos", "Montar Treinos", "Mensagens dos Alunos"]
        choice = st.selectbox("O que deseja fazer?", menu)

        if choice == "Cadastrar Aluno":
            st.header("📝 Cadastrar Novo Aluno")
            with st.form("form_cadastro"):
                nome_aluno = st.text_input("Nome Completo do Aluno")
                user_aluno = st.text_input("Username (Login do Aluno)")
                pass_aluno = st.text_input("Senha para o Aluno", type="password")
                if st.form_submit_button("Cadastrar Aluno"):
                    if salvar_usuario(nome_aluno, user_aluno, pass_aluno, 'Aluno'):
                        st.success(f"Aluno {nome_aluno} cadastrado com sucesso!")
                    else:
                        st.error("Erro: Este Username já está em uso.")

        elif choice == "Gerenciar Alunos":
            st.header("👥 Gerenciar Alunos")
            usuarios = carregar_usuarios()
            alunos = [u for u in usuarios if u['tipo'] == 'Aluno']
            if alunos:
                nomes_alunos = {u['nome']: u['username'] for u in alunos}
                selecionado = st.selectbox("Escolha o Aluno para Editar", list(nomes_alunos.keys()))
                username_selecionado = nomes_alunos[selecionado]
                
                aluno_atual = next(u for u in alunos if u['username'] == username_selecionado)
                
                with st.form("form_editar"):
                    novo_nome = st.text_input("Nome Completo", value=aluno_atual['nome'])
                    nova_senha = st.text_input("Nova Senha", type="password")
                    if st.form_submit_button("Salvar Alterações"):
                        atualizar_usuario(username_selecionado, novo_nome, nova_senha)
                        st.success(f"Informações de {selecionado} atualizadas!")
                        st.rerun()
            else:
                st.warning("Nenhum aluno cadastrado.")

        elif choice == "Montar Treinos":
            st.header("🏋️ Prescrever Treino")
            # Buscar lista de alunos
            usuarios = carregar_usuarios()
            lista_alunos = [(u['nome'], u['username']) for u in usuarios if u['tipo'] == 'Aluno']
            
            if lista_alunos:
                nomes_alunos = {aluno[0]: aluno[1] for aluno in lista_alunos}
                selecionado = st.selectbox("Escolha o Aluno", list(nomes_alunos.keys()))
                username_selecionado = nomes_alunos[selecionado]
                
                with st.expander("Adicionar Exercício"):
                    ex = st.text_input("Nome do Exercício")
                    se = st.text_input("Séries/Repetições")
                    vid = st.text_input("Link do Vídeo (YouTube)")
                    if st.button("Salvar no Treino"):
                        c.execute('INSERT INTO treinos (username_aluno, exercicio, series, video_url) VALUES (?,?,?,?)',
                                  (username_selecionado, ex, se, vid))
                        conn.commit()
                        st.success("Exercício adicionado!")
                
                # Mostrar treino atual
                st.subheader(f"Treino de {selecionado}")
                treino_df = pd.read_sql("SELECT id, exercicio, series, video_url FROM treinos WHERE username_aluno = ?", conn, params=(username_selecionado,))
                if not treino_df.empty:
                    for _, row in treino_df.iterrows():
                        cols = st.columns([4, 2, 1])
                        cols[0].markdown(f"**{row['exercicio']}**\nSéries: {row['series']}")
                        if cols[2].button("Excluir", key=f"delete_{row['id']}"):
                            c.execute("DELETE FROM treinos WHERE id = ?", (row['id'],))
                            conn.commit()
                            st.success("Exercício excluído com sucesso!")
                            st.experimental_rerun()
                else:
                    st.write("Nenhum exercício cadastrado para este aluno.")

                if st.button("Limpar Treino Completo"):
                    c.execute("DELETE FROM treinos WHERE username_aluno = ?", (username_selecionado,))
                    conn.commit()
                    st.rerun()
            else:
                st.warning("Nenhum aluno cadastrado.")

        elif choice == "Mensagens dos Alunos":
            st.header("💬 Caixa de Entrada")
            mensagens = pd.read_sql(f"SELECT remetente, texto FROM mensagens WHERE destinatario = '{username_logado}'", conn)
            if not mensagens.empty:
                for idx, row in mensagens.iterrows():
                    st.info(f"**{row['remetente']}**: {row['texto']}")
            else:
                st.write("Nenhuma mensagem nova.")

    # --- ÁREA DO ALUNO ---
    elif tipo_usuario == "Aluno":
        tab1, tab2 = st.tabs(["Meu Treino", "Falar com Personal"])
        
        with tab1:
            st.header(f"💪 Seu Treino, {nome_usuario}")
            treinos = pd.read_sql(f"SELECT * FROM treinos WHERE username_aluno = '{username_logado}'", conn)
            
            if not treinos.empty:
                for idx, row in treinos.iterrows():
                    with st.expander(f"{row['exercicio']} - {row['series']}"):
                        if row['video_url']:
                            st.video(row['video_url'])
                        else:
                            st.write("Vídeo não disponível.")
            else:
                st.write("Você ainda não possui treinos cadastrados.")

        with tab2:
            st.header("📨 Enviar dúvida")
            msg_texto = st.text_area("Descreva sua dúvida para o professor:")
            if st.button("Enviar Mensagem"):
                c.execute('INSERT INTO mensagens (remetente, destinatario, texto) VALUES (?,?,?)', 
                          (nome_usuario, 'admin', msg_texto))
                conn.commit()
                st.success("Mensagem enviada ao professor!")
#1 atualização                