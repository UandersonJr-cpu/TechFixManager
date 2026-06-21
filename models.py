from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    senha = db.Column(db.String(200))

    # 👇 ADICIONAR ISSO
    tipo = db.Column(db.String(20), default="usuario")

# ===================== CLIENTE =====================
class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    nome = db.Column(db.String(100))
    email = db.Column(db.String(100))
    telefone = db.Column(db.String(20))

    # 👇 VÍNCULO COM O USUÁRIO QUE É DONO DO CLIENTE
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))

    equipamentos = db.relationship(
        "Equipamento",
        backref="cliente",
        lazy=True
    )

# ===================== EQUIPAMENTO =====================
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

# ===================== ORDEM DE SERVIÇO =====================
class OrdemServico(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    cliente_id = db.Column(
        db.Integer,
        db.ForeignKey("cliente.id"),
        nullable=False
    )

    equipamento_id = db.Column(
        db.Integer,
        db.ForeignKey("equipamento.id"),
        nullable=False
    )

    defeito = db.Column(
        db.Text,
        nullable=False
    )

    diagnostico = db.Column(
        db.Text
    )

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

    cliente = db.relationship(
        "Cliente",
        foreign_keys=[cliente_id]
    )

    equipamento = db.relationship(
        "Equipamento",
        foreign_keys=[equipamento_id]
    )

    # ===================== HISTÓRICO OS =====================

class HistoricoOS(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    os_id = db.Column(
        db.Integer,
        db.ForeignKey("ordem_servico.id")
    )

    status = db.Column(
        db.String(100)
    )

    data = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )