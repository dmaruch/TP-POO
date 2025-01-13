import sqlite3
import flet as ft

# Banco de Dados
class Database:
    def __init__(self, db_name="gestao.db"):
        self.conn = sqlite3.connect(db_name)
        self.create_tables()

    def create_tables(self):
        with self.conn:
            self.conn.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                senha TEXT NOT NULL,
                tipo TEXT NOT NULL CHECK(tipo IN ('Administrador', 'Demandante', 'Bolsista'))
            )
            ''')
            self.conn.execute('''
            CREATE TABLE IF NOT EXISTS demandas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                descricao TEXT,
                solicitante_id INTEGER,
                projeto_id INTEGER,
                status TEXT DEFAULT 'Pendente',
                bolsista_id INTEGER,
                FOREIGN KEY (solicitante_id) REFERENCES usuarios (id),
                FOREIGN KEY (projeto_id) REFERENCES projetos (id),
                FOREIGN KEY (bolsista_id) REFERENCES usuarios (id)
            )
            ''')
            self.conn.execute('''
            CREATE TABLE IF NOT EXISTS projetos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                area TEXT NOT NULL
            )
            ''')
            self.conn.execute('''
            CREATE TABLE IF NOT EXISTS projeto_usuarios (
                projeto_id INTEGER,
                usuario_id INTEGER,
                PRIMARY KEY (projeto_id, usuario_id),
                FOREIGN KEY (projeto_id) REFERENCES projetos (id),
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
            ''')

    def adicionar_usuario(self, nome, email, senha, tipo):
        with self.conn:
            self.conn.execute(
                "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)", (nome, email, senha, tipo)
            )

    def validar_usuario(self, email, senha):
        with self.conn:
            return self.conn.execute(
                "SELECT id, nome, tipo FROM usuarios WHERE email = ? AND senha = ?",
                (email, senha)
            ).fetchone()

    def listar_demandas(self, usuario_id=None, tipo_usuario=None):
        with self.conn:
            if tipo_usuario == "Demandante":
                return self.conn.execute(
                    "SELECT * FROM demandas WHERE solicitante_id = ?", (usuario_id,)
                ).fetchall()
            elif tipo_usuario == "Bolsista":
                return self.conn.execute(
                    "SELECT * FROM demandas WHERE bolsista_id = ?", (usuario_id,)
                ).fetchall()
            elif tipo_usuario == "Administrador":
                return self.conn.execute(
                    "SELECT * FROM demandas"
                ).fetchall()
            else:
                return []

    def listar_usuarios(self, tipo):
        with self.conn:
            return self.conn.execute(
                "SELECT id, nome, email FROM usuarios WHERE tipo = ?", (tipo,)
            ).fetchall()

    def remover_usuario(self, usuario_id):
        with self.conn:
            self.conn.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))

    def listar_projetos(self, usuario_id=None, tipo_usuario=None):
        with self.conn:
            if tipo_usuario == "Administrador":
                return self.conn.execute(
                    "SELECT id, nome, area FROM projetos WHERE id IN (SELECT projeto_id FROM projeto_usuarios WHERE usuario_id = ?)",
                    (usuario_id,)
                ).fetchall()
            else:
                return self.conn.execute("SELECT id, nome, area FROM projetos").fetchall()

    def adicionar_projeto(self, nome, area):
        with self.conn:
            self.conn.execute(
                "INSERT INTO projetos (nome, area) VALUES (?, ?)", (nome, area)
            )
            return self.conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    def adicionar_participante_projeto(self, projeto_id, usuario_id):
        with self.conn:
            self.conn.execute(
                "INSERT INTO projeto_usuarios (projeto_id, usuario_id) VALUES (?, ?, ?)", (projeto_id, usuario_id)
            )

    def remover_participante_projeto(self, projeto_id, usuario_id):
        with self.conn:
            self.conn.execute(
                "DELETE FROM projeto_usuarios WHERE projeto_id = ? AND usuario_id = ?", (projeto_id, usuario_id)
            )

    def cadastrar_demanda(self, titulo, descricao, solicitante_id, projeto_id):
        with self.conn:
            self.conn.execute(
                "INSERT INTO demandas (titulo, descricao, solicitante_id, projeto_id) VALUES (?, ?, ?, ?)",
                (titulo, descricao, solicitante_id, projeto_id)
            )

    def atualizar_status_demanda(self, demanda_id, status, bolsista_id=None):
        with self.conn:
            self.conn.execute(
                "UPDATE demandas SET status = ?, bolsista_id = ? WHERE id = ?",
                (status, bolsista_id, demanda_id)
            )

    def atribuir_demanda(self, bolsista_id, demanda_id):
        with self.conn:
            self.conn.execute(
                "UPDATE demandas SET bolsista_id = ? WHERE id = ?", (bolsista_id, demanda_id)
            )

    def obter_demanda(self, demanda_id):
        with self.conn:
            return self.conn.execute("SELECT * FROM demandas WHERE id = ?", (demanda_id,)).fetchone()

    def atualizar_estado_demanda(self, demanda_id, novo_estado):
        with self.conn:
            self.conn.execute("UPDATE demandas SET estado = ? WHERE id = ?", (novo_estado, demanda_id))

# Interface Flet
def main(page: ft.Page):
    db = Database()
    page.title = "Gestão de Demandas e Projetos"
    page.scroll = "auto"

    def limpar_tela():
        page.controls.clear()
        page.update()

    def login_page(e=None):
        limpar_tela()

        def autenticar_usuario(e):
            email = email_field.value
            senha = senha_field.value
            usuario = db.validar_usuario(email, senha)

            if usuario:
                page.session.set("user_id", usuario[0])
                page.session.set("user_name", usuario[1])
                page.session.set("user_type", usuario[2])

                if usuario[2] == "Administrador":
                    administrador_menu()
                elif usuario[2] == "Demandante":
                    demandante_page()
                elif usuario[2] == "Bolsista":
                    bolsista_page()
            else:
                page.snack_bar = ft.SnackBar(ft.Text("Credenciais inválidas!"))
                page.snack_bar.open = True
                page.update()

        def abrir_cadastro_page(e):
            cadastro_page()

        email_field = ft.TextField(label="Email")
        senha_field = ft.TextField(label="Senha", password=True)
        login_button = ft.ElevatedButton("Login", on_click=autenticar_usuario)
        cadastro_button = ft.ElevatedButton("Cadastrar", on_click=abrir_cadastro_page)

        page.add(
            ft.Column([
                ft.Text("Login", size=24, weight="bold"),
                email_field,
                senha_field,
                login_button,
                cadastro_button
            ])
        )

    def cadastro_page():
        limpar_tela()

        def cadastrar_usuario(e):
            if nome_field.value and email_field.value and senha_field.value and tipo_selector.value:
                try:
                    db.adicionar_usuario(
                        nome_field.value,
                        email_field.value,
                        senha_field.value,
                        tipo_selector.value
                    )
                    page.snack_bar = ft.SnackBar(ft.Text(f"Cadastro realizado com sucesso!"))
                    page.snack_bar.open = True
                    page.update()
                    login_page()
                except sqlite3.IntegrityError:
                    page.snack_bar = ft.SnackBar(ft.Text("Erro: Email já cadastrado!"))
                    page.snack_bar.open = True
                    page.update()
            else:
                page.snack_bar = ft.SnackBar(ft.Text("Preencha todos os campos!"))
                page.snack_bar.open = True
                page.update()

        nome_field = ft.TextField(label="Nome")
        email_field = ft.TextField(label="Email")
        senha_field = ft.TextField(label="Senha", password=True)
        tipo_selector = ft.Dropdown(
            label="Tipo de Usuário",
            options=[
                ft.dropdown.Option("Administrador"),
                ft.dropdown.Option("Demandante"),
                ft.dropdown.Option("Bolsista")
            ]
        )
        cadastrar_button = ft.ElevatedButton("Cadastrar", on_click=cadastrar_usuario)
        voltar_button = ft.ElevatedButton("Voltar", on_click=login_page)

        page.add(
            ft.Column([
                ft.Text("Cadastro", size=24, weight="bold"),
                nome_field,
                email_field,
                senha_field,
                tipo_selector,
                cadastrar_button,
                voltar_button
            ])
        )

    def administrador_menu(e=None):
        limpar_tela()

        def voltar_ao_login(e):
            login_page()

        def gerenciar_projetos_page(e):
            limpar_tela()

            def adicionar_projeto(e):
                if nome_projeto_field.value and area_projeto_field.value:
                    projeto_id = db.adicionar_projeto(nome_projeto_field.value, area_projeto_field.value)
                    page.snack_bar = ft.SnackBar(ft.Text(f"Projeto '{nome_projeto_field.value}' adicionado com sucesso!"))
                    page.snack_bar.open = True
                    nome_projeto_field.value = ""
                    area_projeto_field.value = ""
                    listar_projetos()
                    page.update()

            def listar_projetos():
                projetos = db.listar_projetos()
                projetos_list.controls.clear()
                for projeto in projetos:
                    projetos_list.controls.append(
                        ft.Text(f"{projeto[1]} - {projeto[2]}")
                    )
                page.update()

            voltar_button = ft.ElevatedButton("Voltar", on_click=administrador_menu)

            nome_projeto_field = ft.TextField(label="Nome do Projeto")
            area_projeto_field = ft.TextField(label="Área do Projeto")
            adicionar_projeto_button = ft.ElevatedButton("Adicionar Projeto", on_click=adicionar_projeto)

            projetos_list = ft.Column()

            page.add(
                ft.Column([
                    ft.Text("Gerenciar Projetos", size=24, weight="bold"),
                    nome_projeto_field,
                    area_projeto_field,
                    adicionar_projeto_button,
                    ft.Text("Projetos Cadastrados:"),
                    projetos_list,
                    voltar_button
                ])
            )

            listar_projetos()

        def gerenciar_demandas_page(e):
            limpar_tela()

            def listar_demandas():
                demandas = db.listar_demandas(tipo_usuario="Administrador")
                demandas_list.controls.clear()
                demanda_selector.options.clear()
                for demanda in demandas:
                    demandas_list.controls.append(
                        ft.Row([
                            ft.Text(f"{demanda[1]} - {demanda[5]} - Status: {demanda[4]}"),
                            ft.ElevatedButton("Selecionar", on_click=lambda e, demanda_id=demanda[0]: selecionar_demanda(demanda_id))
                        ])
                    )
                    demanda_selector.options.append(ft.dropdown.Option(demanda[0], text=f"{demanda[1]} - {demanda[5]}"))
                page.update()

            def selecionar_demanda(demanda_id):
                page.session.set("selected_demanda_id", demanda_id)
                demanda = db.obter_demanda(demanda_id)
                demanda_selector.value = demanda_id
                status_selector.value = demanda[4]
                page.update()

            def atualizar_status(e):
                demanda_id = page.session.get("selected_demanda_id")
                novo_status = status_selector.value
                if demanda_id and novo_status:
                    db.atualizar_status_demanda(demanda_id, novo_status)
                    page.snack_bar = ft.SnackBar(ft.Text("Status da demanda atualizado com sucesso!"))
                    page.snack_bar.open = True
                    listar_demandas()
                    page.update()

            voltar_button = ft.ElevatedButton("Voltar", on_click=administrador_menu)

            demanda_selector = ft.Dropdown(
                label="Selecione a Demanda",
                options=[]
            )
            status_selector = ft.Dropdown(
                label="Novo Status",
                options=[
                    ft.dropdown.Option("Recusada"),
                    ft.dropdown.Option("Pendente"),
                    ft.dropdown.Option("Em Andamento"),
                    ft.dropdown.Option("Concluída"),
                    ft.dropdown.Option("Entregue")
                ]
            )
            atualizar_button = ft.ElevatedButton("Atualizar Status", on_click=atualizar_status)

            demandas_list = ft.Column()

            page.add(
                ft.Column([
                    ft.Text("Gerenciar Demandas", size=24, weight="bold"),
                    demandas_list,
                    demanda_selector,
                    status_selector,
                    atualizar_button,
                    voltar_button
                ])
            )

            listar_demandas()

        def gerenciar_bolsistas_page(e):
            limpar_tela()

            def listar_bolsistas():
                bolsistas = db.listar_usuarios(tipo="Bolsista")
                bolsistas_list.controls.clear()
                bolsista_selector.options.clear()
                for bolsista in bolsistas:
                    bolsistas_list.controls.append(
                        ft.Text(f"{bolsista[1]} - {bolsista[2]}")
                    )
                    bolsista_selector.options.append(ft.dropdown.Option(bolsista[0], text=bolsista[1]))
                page.update()

            def listar_demandas():
                demandas = db.listar_demandas(tipo_usuario="Administrador")
                demanda_selector.options.clear()
                for demanda in demandas:
                    demanda_selector.options.append(ft.dropdown.Option(demanda[0], text=f"{demanda[1]} - {demanda[5]}"))
                page.update()

            def atribuir_demanda(e):
                if bolsista_selector.value and demanda_selector.value:
                    db.atribuir_demanda(bolsista_selector.value, demanda_selector.value)
                    page.snack_bar = ft.SnackBar(ft.Text("Demanda atribuída com sucesso!"))
                    page.snack_bar.open = True
                    page.update()

            voltar_button = ft.ElevatedButton("Voltar", on_click=administrador_menu)

            bolsista_selector = ft.Dropdown(label="Selecione o Bolsista")
            demanda_selector = ft.Dropdown(label="Selecione a Demanda")
            atribuir_button = ft.ElevatedButton("Atribuir Demanda", on_click=atribuir_demanda)

            bolsistas_list = ft.Column()

            page.add(
                ft.Column([
                    ft.Text("Gerenciar Bolsistas", size=24, weight="bold"),
                    bolsista_selector,
                    demanda_selector,
                    atribuir_button,
                    ft.Text("Bolsistas Cadastrados:"),
                    bolsistas_list,
                    voltar_button
                ])
            )

            listar_bolsistas()
            listar_demandas()

        titulo = ft.Text(f"Bem-vindo(a), Administrador(a): {page.session.get('user_name')}", size=24, weight="bold")
        subtitulo = ft.Text("Selecione uma funcionalidade:", size=16)

        opcoes = ft.Column([
            ft.ElevatedButton("Gerenciar Projetos", on_click=gerenciar_projetos_page),
            ft.ElevatedButton("Gerenciar Demandas", on_click=gerenciar_demandas_page),
            ft.ElevatedButton("Gerenciar Bolsistas", on_click=gerenciar_bolsistas_page),
            ft.ElevatedButton("Sair", on_click=voltar_ao_login)
        ])

        page.add(
            ft.Column([
                titulo,
                subtitulo,
                opcoes
            ])
        )

    def demandante_page():
        limpar_tela()

        def cadastrar_demanda(e):
            if titulo_field.value and descricao_field.value and projeto_selector.value:
                try:
                    db.cadastrar_demanda(
                        titulo_field.value,
                        descricao_field.value,
                        page.session.get("user_id"),
                        projeto_selector.value
                    )
                    page.snack_bar = ft.SnackBar(ft.Text("Demanda cadastrada com sucesso!"))
                    page.snack_bar.open = True
                    titulo_field.value = ""
                    descricao_field.value = ""
                    listar_demandas()
                    page.update()
                except Exception as ex:
                    page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao cadastrar demanda: {str(ex)}"))
                    page.snack_bar.open = True
                    page.update()
            else:
                page.snack_bar = ft.SnackBar(ft.Text("Preencha todos os campos!"))
                page.snack_bar.open = True
                page.update()

        def listar_demandas():
            demandas = db.listar_demandas(
                usuario_id=page.session.get("user_id"),
                tipo_usuario="Demandante"
            )
            demandas_list.controls.clear()
            for demanda in demandas:
                demandas_list.controls.append(
                    ft.Text(f"{demanda[1]} - {demanda[5]}")
                )
            page.update()

        voltar_button = ft.ElevatedButton("Sair", on_click=login_page)

        titulo_field = ft.TextField(label="Título da Demanda")
        descricao_field = ft.TextField(label="Descrição da Demanda", multiline=True)

        projetos = db.listar_projetos()
        projeto_selector = ft.Dropdown(
            label="Selecione o Projeto",
            options=[ft.dropdown.Option(projeto[0], text=projeto[1]) for projeto in projetos]
        )

        cadastrar_button = ft.ElevatedButton("Cadastrar Demanda", on_click=cadastrar_demanda)

        demandas_list = ft.Column()

        page.add(
            ft.Column([
                ft.Text("Bem-vindo(a), Demandante", size=24, weight="bold"),
                ft.Text("Cadastrar Nova Demanda", size=20, weight="bold"),
                titulo_field,
                descricao_field,
                projeto_selector,
                cadastrar_button,
                ft.Text("Demandas Cadastradas:", size=20, weight="bold"),
                demandas_list,
                voltar_button
            ])
        )

        listar_demandas()

    def bolsista_page():
        limpar_tela()

        def listar_demandas():
            demandas = db.listar_demandas(
                usuario_id=page.session.get("user_id"),
                tipo_usuario="Bolsista"
            )
            demandas_list.controls.clear()
            for demanda in demandas:
                demandas_list.controls.append(
                    ft.Text(f"{demanda[1]} - {demanda[5]} - Status: {demanda[4]}")
                )
            page.update()

        voltar_button = ft.ElevatedButton("Sair", on_click=login_page)

        demandas_list = ft.Column()

        page.add(
            ft.Column([
                ft.Text("Bem-vindo(a), Bolsista", size=24, weight="bold"),
                ft.Text("Demandas Atribuídas", size=20, weight="bold"),
                demandas_list,
                voltar_button
            ])
        )

        listar_demandas()

    login_page()


ft.app(target=main)
