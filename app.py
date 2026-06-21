import os
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect
from flask_login import login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin,
    login_user, login_required,
    logout_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app.config["SECRET_KEY"] = "..."
app.config["SQLALCHEMY_DATABASE_URI"] = \
    "sqlite:///" + os.path.join(BASE_DIR, "techfix.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Uploads de equipamentos
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Arquivos da área técnica
UPLOAD_TECNICO = "static/tecnico"
app.config["UPLOAD_TECNICO"] = UPLOAD_TECNICO

# Banco de dados
db = SQLAlchemy(app)
# ================= LOGIN =================
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# ================= MODELOS =================

class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)

    nome = db.Column(db.String(100))

    email = db.Column(
        db.String(100),
        unique=True
    )

    senha = db.Column(db.String(200))

    tipo = db.Column(
        db.String(20),
        default="usuario"
    )

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    nome = db.Column(db.String(100))
    email = db.Column(db.String(100))
    telefone = db.Column(db.String(20))

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuario.id")
    )

    equipamentos = db.relationship(
        "Equipamento",
        backref="cliente",
        lazy=True
    )


class Equipamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    nome = db.Column(db.String(100))
    marca = db.Column(db.String(100))
    modelo = db.Column(db.String(100))
    serial = db.Column(db.String(100))

    foto = db.Column(db.String(200))

    cliente_id = db.Column(
        db.Integer,
        db.ForeignKey("cliente.id")
    )

class OrdemServico(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    cliente_id = db.Column(db.Integer, db.ForeignKey("cliente.id"))
    equipamento_id = db.Column(db.Integer, db.ForeignKey("equipamento.id"))

    defeito = db.Column(db.String(200))
    diagnostico = db.Column(db.String(200))

    status = db.Column(
        db.String(50),
        default="Recebido"
    )

    valor = db.Column(
        db.Float,
        default=0
    )

    observacoes = db.Column(
        db.Text
    )

    data = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class HistoricoOS(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    os_id = db.Column(
        db.Integer,
        db.ForeignKey("ordem_servico.id")
    )

    status = db.Column(db.String(100))

    data = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

class ArquivoTecnico(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    titulo = db.Column(
        db.String(200)
    )

    categoria = db.Column(
        db.String(50)
    )

    fabricante = db.Column(
        db.String(100)
    )

    modelo = db.Column(
        db.String(100)
    )

    descricao = db.Column(
        db.Text
    )

    arquivo = db.Column(
        db.String(300)
    )

    data = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )
# ================= LOGIN LOAD =================
@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))


# ================= ROTAS =================

@app.route("/")
def index():
    return redirect("/login")

@app.route("/os/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_os(id):

    os = OrdemServico.query.get_or_404(id)

    if request.method == "POST":

        os.status = request.form.get("status")
        os.diagnostico = request.form.get("diagnostico")
        os.valor = request.form.get("valor")
        os.observacoes = request.form.get("observacoes")

        # salva no histórico
        historico = HistoricoOS(
            os_id=os.id,
            status=os.status
        )

        db.session.add(historico)

        db.session.commit()

        return redirect("/os")

    return render_template(
        "os/editar.html",
        os=os
    )

@app.route("/os/imprimir/<int:id>")
@login_required
def imprimir_os(id):

    os = OrdemServico.query.get_or_404(id)

    cliente = Cliente.query.get(os.cliente_id)

    equipamento = Equipamento.query.get(os.equipamento_id)

    return render_template(
        "os/imprimir.html",
        os=os,
        cliente=cliente,
        equipamento=equipamento
    )


# ---------- LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        email = request.form.get("email")
        senha = request.form.get("senha")

        user = Usuario.query.filter_by(email=email).first()

        if user and check_password_hash(user.senha, senha):

            login_user(user)

            # 👇 redireciona por tipo
            if user.tipo == "admin":
                return redirect("/dashboard")
            else:
                return redirect("/minha-area")

        return "Login inválido"

    return render_template("auth/login.html")

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():

    if request.method == "POST":

        nome = request.form.get("nome")
        email = request.form.get("email")
        telefone = request.form.get("telefone")
        senha = request.form.get("senha")

        if Usuario.query.filter_by(email=email).first():
            return "Email já cadastrado"

        usuario = Usuario(
            nome=nome,
            email=email,
            senha=generate_password_hash(senha),
            tipo="usuario"
        )

        db.session.add(usuario)
        db.session.commit()

        cliente = Cliente(
            nome=nome,
            email=email,
            telefone=telefone,
            usuario_id=usuario.id
        )

        db.session.add(cliente)
        db.session.commit()

        return redirect("/login")

    return render_template("auth/cadastro.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")

@app.route("/minha-area")
@login_required
def minha_area():

    if current_user.tipo == "admin":
        return redirect("/dashboard")

    cliente = Cliente.query.filter_by(
        usuario_id=current_user.id
    ).first()

    equipamentos = []

    ordens = []

    if cliente:

        equipamentos = Equipamento.query.filter_by(
            cliente_id=cliente.id
        ).all()

        ordens = OrdemServico.query.filter_by(
            cliente_id=cliente.id
        ).all()

    return render_template(
    "cliente_area.html",
    equipamentos=equipamentos,
    ordens=ordens,
    Equipamento=Equipamento
)

# ---------- DASHBOARD ----------
@app.route("/dashboard")
@login_required
def dashboard():

    total_clientes = Cliente.query.count()
    total_equipamentos = Equipamento.query.count()
    total_os = OrdemServico.query.count()

    return render_template(
        "dashboard/index.html",
        total_clientes=total_clientes,
        total_equipamentos=total_equipamentos,
        total_os=total_os
    )


# ---------- CLIENTES ----------
@app.route("/clientes")
@login_required
def clientes():

    if current_user.tipo != "admin":
        return redirect("/minha-area")

    clientes = Cliente.query.all()

    return render_template(
        "clientes/listar.html",
        clientes=clientes
    )

@app.route("/clientes/novo", methods=["GET", "POST"])
@login_required
def novo_cliente():

    if request.method == "POST":

        cliente = Cliente(
            nome=request.form.get("nome"),
            email=request.form.get("email"),
            telefone=request.form.get("telefone")
        )

        db.session.add(cliente)
        db.session.commit()

        return redirect("/clientes")

    return render_template("clientes/novo.html")

@app.route("/clientes/excluir/<int:id>")
@login_required
def excluir_cliente(id):

    cliente = Cliente.query.get_or_404(id)

    db.session.delete(cliente)
    db.session.commit()

    return redirect("/clientes")

@app.route("/os/historico/<int:id>")
@login_required
def historico_os(id):

    historicos = HistoricoOS.query.filter_by(
        os_id=id
    ).order_by(
        HistoricoOS.data.desc()
    ).all()

    return render_template(
        "os/historico.html",
        historicos=historicos
    )


# ---------- EQUIPAMENTOS ----------
@app.route("/equipamentos")
@login_required
def equipamentos():

    busca = request.args.get("busca", "")

    equipamentos = Equipamento.query.filter(
        Equipamento.nome.contains(busca)
    ).all()

    return render_template(
        "equipamentos/listar.html",
        equipamentos=equipamentos
    )

@app.route("/equipamentos/novo", methods=["GET", "POST"])
@login_required
def novo_equipamento():

    clientes = Cliente.query.all()

    if request.method == "POST":

        foto = request.files.get("foto")

        nome_arquivo = None

        if foto and foto.filename:

            nome_arquivo = secure_filename(foto.filename)

            foto.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    nome_arquivo
                )
            )

        equipamento = Equipamento(
            nome=request.form.get("nome"),
            marca=request.form.get("marca"),
            modelo=request.form.get("modelo"),
            serial=request.form.get("serial"),
            foto=nome_arquivo,
            cliente_id=int(request.form.get("cliente_id"))
        )

        db.session.add(equipamento)
        db.session.commit()

        return redirect("/equipamentos")

    return render_template(
        "equipamentos/novo.html",
        clientes=clientes
    )
@app.route("/equipamentos/excluir/<int:id>")
@login_required
def excluir_equipamento(id):

    equipamento = Equipamento.query.get_or_404(id)

    db.session.delete(equipamento)
    db.session.commit()

    return redirect("/equipamentos")


# ---------- ORDEM DE SERVIÇO ----------
@app.route("/os")
@login_required
def listar_os():

    ordens = OrdemServico.query.all()

    return render_template(
        "os/listar.html",
        ordens=ordens,
        Cliente=Cliente,
        Equipamento=Equipamento
    )

@app.route("/os/nova", methods=["GET", "POST"])
@login_required
def nova_os():

    clientes = Cliente.query.all()
    equipamentos = Equipamento.query.all()

    if request.method == "POST":

        os = OrdemServico(
            cliente_id=request.form.get("cliente_id"),
            equipamento_id=request.form.get("equipamento_id"),
            defeito=request.form.get("defeito"),
            diagnostico=request.form.get("diagnostico"),
            status="Recebido"
        )

        db.session.add(os)
        db.session.commit()

        historico = HistoricoOS(
            os_id=os.id,
            status="Recebido"
        )

        db.session.add(historico)
        db.session.commit()

        return redirect("/os")

    return render_template(
        "os/nova.html",
        clientes=clientes,
        equipamentos=equipamentos
    )
@app.route("/os/excluir/<int:id>")
@login_required
def excluir_os(id):

    os = OrdemServico.query.get_or_404(id)

    db.session.delete(os)
    db.session.commit()

    return redirect("/os")

@app.route("/tecnico")
@login_required
def area_tecnica():

    busca = request.args.get("busca", "")

    if busca:

        arquivos = ArquivoTecnico.query.filter(
            (ArquivoTecnico.titulo.contains(busca)) |
            (ArquivoTecnico.fabricante.contains(busca)) |
            (ArquivoTecnico.modelo.contains(busca)) |
            (ArquivoTecnico.categoria.contains(busca))
        ).all()

    else:

        arquivos = ArquivoTecnico.query.order_by(
            ArquivoTecnico.data.desc()
        ).all()

    return render_template(
        "tecnico/listar.html",
        arquivos=arquivos
    )

@app.route("/tecnico/novo", methods=["GET", "POST"])
@login_required
def novo_arquivo_tecnico():

    if request.method == "POST":

        arquivo = request.files.get("arquivo")

        nome_arquivo = None

        if arquivo and arquivo.filename:

            nome_arquivo = secure_filename(
                arquivo.filename
            )

            arquivo.save(
                os.path.join(
                    app.config["UPLOAD_TECNICO"],
                    nome_arquivo
                )
            )

        novo = ArquivoTecnico(
            titulo=request.form.get("titulo"),
            categoria=request.form.get("categoria"),
            fabricante=request.form.get("fabricante"),
            modelo=request.form.get("modelo"),
            descricao=request.form.get("descricao"),
            arquivo=nome_arquivo
        )

        db.session.add(novo)
        db.session.commit()

        return redirect("/tecnico")

    return render_template(
        "tecnico/novo.html"
    )

@app.route("/tecnico/excluir/<int:id>")
@login_required
def excluir_arquivo_tecnico(id):

    arquivo = ArquivoTecnico.query.get_or_404(id)

    db.session.delete(arquivo)
    db.session.commit()

    return redirect("/tecnico")

@app.route("/os/status/<int:id>/<novo_status>")
@login_required
def alterar_status(id, novo_status):

    ordem = OrdemServico.query.get_or_404(id)

    ordem.status = novo_status

    db.session.commit()

    return redirect("/os")

# ---------- CRIAR BANCO + ADMIN ----------
with app.app_context():

    db.create_all()

    # ADMIN
    if not Usuario.query.filter_by(
        email="admin@techfix.com"
    ).first():

        admin = Usuario(
            nome="Administrador",
            email="admin@techfix.com",
            senha=generate_password_hash("123456"),
            tipo="admin"
        )

        db.session.add(admin)

    # CLIENTE TESTE
    if not Usuario.query.filter_by(
        email="cliente@teste.com"
    ).first():

        cliente_user = Usuario(
            nome="Cliente Teste",
            email="cliente@teste.com",
            senha=generate_password_hash("123456"),
            tipo="usuario"
        )

        db.session.add(cliente_user)

    db.session.commit()
# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)




