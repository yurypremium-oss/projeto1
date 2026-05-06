import streamlit as st
import sqlite3
import pandas as pd
import os
import re

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

def atualizar_usuario(username, novo_nome, nova_senha):
    usuarios = carregar_usuarios()
    for u in usuarios:
        if u['username'] == username:
            u['nome'] = novo_nome
            if nova_senha:
                u['password'] = nova_senha
            break
    # Reescrever o arquivo
    with open(ARQUIVO_USUARIOS, 'w', encoding='utf-8') as f:
        for u in usuarios:
            f.write(f"{u['nome']},{u['username']},{u['password']},{u['tipo']}\n")

def get_professor_username():
    usuarios = carregar_usuarios()
    for u in usuarios:
        if u['tipo'] == 'Professor':
            return u['username']
    return None

def extract_youtube_id(url):
    patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?youtu\.be/([a-zA-Z0-9_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def atualizar_exercicio(id, exercicio, series, video_url):
    c.execute('UPDATE treinos SET exercicio = ?, series = ?, video_url = ? WHERE id = ?',
              (exercicio, series, video_url, id))
    conn.commit()

def copiar_treino(username_origem, username_destino):
    # Buscar todos os exercícios do aluno de origem
    exercicios = c.execute('SELECT exercicio, series, video_url FROM treinos WHERE username_aluno = ?', 
                           (username_origem,)).fetchall()
    
    # Inserir cada exercício para o aluno de destino
    for exercicio_info in exercicios:
        c.execute('INSERT INTO treinos (username_aluno, exercicio, series, video_url) VALUES (?,?,?,?)',
                  (username_destino, exercicio_info[0], exercicio_info[1], exercicio_info[2]))
    conn.commit()
    return len(exercicios)

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

else:
    nome_usuario, username_logado, tipo_usuario = st.session_state['user_data']
    
    st.sidebar.title(f"Bem-vindo, {nome_usuario}")
    if st.sidebar.button("Sair"):
        st.session_state['logado'] = False
        st.rerun()

    # --- ÁREA DO PROFESSOR ---
    if tipo_usuario == "Professor":
        menu = ["Cadastrar Aluno", "Gerenciar Alunos", "Montar Treinos", "Mensagens dos Alunos", "Minha Conta"]
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
                        cols = st.columns([3, 1, 1, 1])
                        cols[0].markdown(f"**{row['exercicio']}**\nSéries: {row['series']}")
                        
                        if cols[1].button("✏️ Editar", key=f"edit_{row['id']}"):
                            st.session_state[f"edit_mode_{row['id']}"] = True
                        
                        if cols[2].button("❌ Excluir", key=f"delete_{row['id']}"):
                            c.execute("DELETE FROM treinos WHERE id = ?", (row['id'],))
                            conn.commit()
                            st.success("Exercício excluído com sucesso!")
                            st.rerun()
                        
                        # Formulário de edição
                        if st.session_state.get(f"edit_mode_{row['id']}", False):
                            st.info("📝 Editando Exercício")
                            with st.form(f"form_edit_{row['id']}"):
                                novo_exercicio = st.text_input("Nome do Exercício", value=row['exercicio'], key=f"ex_{row['id']}")
                                nova_serie = st.text_input("Séries/Repetições", value=row['series'], key=f"ser_{row['id']}")
                                novo_video = st.text_input("Link do Vídeo (YouTube)", value=row['video_url'], key=f"vid_{row['id']}")
                                
                                col_salvar, col_cancelar = st.columns(2)
                                with col_salvar:
                                    if st.form_submit_button("💾 Salvar Alterações"):
                                        atualizar_exercicio(row['id'], novo_exercicio, nova_serie, novo_video)
                                        st.session_state[f"edit_mode_{row['id']}"] = False
                                        st.success("Exercício atualizado com sucesso!")
                                        st.rerun()
                                with col_cancelar:
                                    if st.form_submit_button("✖️ Cancelar"):
                                        st.session_state[f"edit_mode_{row['id']}"] = False
                                        st.rerun()
                else:
                    st.write("Nenhum exercício cadastrado para este aluno.")

                if st.button("Limpar Treino Completo"):
                    c.execute("DELETE FROM treinos WHERE username_aluno = ?", (username_selecionado,))
                    conn.commit()
                    st.rerun()
                
                # --- SEÇÃO DE CÓPIA DE TREINO ---
                st.divider()
                st.subheader("📋 Copiar Treino de Outro Aluno")
                
                with st.form("form_copiar_treino"):
                    st.write("Selecione um aluno para copiar o treino completo:")
                    alunos_para_copiar = {u['nome']: u['username'] for u in lista_alunos if u[0] != selecionado}
                    
                    if alunos_para_copiar:
                        aluno_origem = st.selectbox("Aluno de origem (de quem copiar):", list(alunos_para_copiar.keys()), key="origem_copy")
                        username_origem = alunos_para_copiar[aluno_origem]
                        
                        if st.form_submit_button("📥 Copiar Treino Completo"):
                            quantidade = copiar_treino(username_origem, username_selecionado)
                            st.success(f"✅ Treino copiado com sucesso! {quantidade} exercício(s) adicionado(s) para {selecionado}!")
                            st.rerun()
                    else:
                        st.warning("Não há outros alunos para copiar treinos.")
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

            st.header("📤 Enviar Mensagem para Aluno")
            usuarios = carregar_usuarios()
            alunos = [u for u in usuarios if u['tipo'] == 'Aluno']
            if alunos:
                nomes_alunos = {u['nome']: u['username'] for u in alunos}
                selecionado = st.selectbox("Escolha o Aluno para enviar mensagem", list(nomes_alunos.keys()))
                username_selecionado = nomes_alunos[selecionado]
                msg_texto = st.text_area("Digite a mensagem:")
                if st.button("Enviar Mensagem"):
                    c.execute('INSERT INTO mensagens (remetente, destinatario, texto) VALUES (?,?,?)', 
                              (username_logado, username_selecionado, msg_texto))
                    conn.commit()
                    st.success(f"Mensagem enviada para {selecionado}!")
            else:
                st.warning("Nenhum aluno cadastrado.")

        elif choice == "Minha Conta":
            st.header("👤 Minha Conta")
            with st.form("form_minha_conta"):
                novo_nome = st.text_input("Nome Completo", value=nome_usuario)
                nova_senha = st.text_input("Nova Senha", type="password")
                if st.form_submit_button("Salvar Alterações"):
                    atualizar_usuario(username_logado, novo_nome, nova_senha)
                    st.success("Informações atualizadas!")
                    st.rerun()

    # --- ÁREA DO ALUNO ---
    elif tipo_usuario == "Aluno":
        tab1, tab2, tab3 = st.tabs(["Meu Treino", "Falar com Personal", "Mensagens do Personal"])
        
        with tab1:
            st.header(f"💪 Seu Treino, {nome_usuario}")
            treinos = pd.read_sql(f"SELECT * FROM treinos WHERE username_aluno = '{username_logado}'", conn)
            
            if not treinos.empty:
                st.markdown(
                    """
                    <style>
                    .video-responsive {
                        position: relative;
                        width: 100%;
                        padding-bottom: 56.25%;
                        height: 0;
                        overflow: hidden;
                    }
                    .video-responsive iframe {
                        position: absolute;
                        top: 0;
                        left: 0;
                        width: 100%;
                        height: 100%;
                    }
                    </style>
                    """,
                    unsafe_allow_html=True,
                )
                for idx, row in treinos.iterrows():
                    with st.expander(f"{row['exercicio']} - {row['series']}"):
                        if row['video_url']:
                            video_id = extract_youtube_id(row['video_url'])
                            if video_id:
                                st.markdown(
                                    f'<div class="video-responsive"><iframe src="https://www.youtube.com/embed/{video_id}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe></div>',
                                    unsafe_allow_html=True,
                                )
                            else:
                                st.write("URL de vídeo inválida.")
                        else:
                            st.write("Vídeo não disponível.")
            else:
                st.write("Você ainda não possui treinos cadastrados.")

        with tab2:
            st.header("📨 Enviar dúvida")
            msg_texto = st.text_area("Descreva sua dúvida para o professor:")
            if st.button("Enviar Mensagem"):
                prof_username = get_professor_username()
                if prof_username:
                    c.execute('INSERT INTO mensagens (remetente, destinatario, texto) VALUES (?,?,?)', 
                              (nome_usuario, prof_username, msg_texto))
                    conn.commit()
                    st.success("Mensagem enviada ao professor!")
                else:
                    st.error("Professor não encontrado.")

        with tab3:
            st.header("💬 Mensagens do Personal")
            prof_username = get_professor_username()
            if prof_username:
                mensagens_prof = pd.read_sql(f"SELECT texto FROM mensagens WHERE remetente = '{prof_username}' AND destinatario = '{username_logado}'", conn)
                if not mensagens_prof.empty:
                    for idx, row in mensagens_prof.iterrows():
                        st.info(f"**Personal**: {row['texto']}")
                else:
                    st.write("Nenhuma mensagem do personal.")
            else:
                st.error("Professor não encontrado.")
#1 atualização                