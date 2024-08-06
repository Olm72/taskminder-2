import os
from sqlalchemy import Column, Integer, String, Boolean, Float, Time, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

app = Flask(__name__)
base_dir = os.path.abspath(os.path.dirname(__file__))
database_dir = os.path.join(base_dir, 'database')
database_path = os.path.join(database_dir, 'task_minder_db.db')

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class MensajesCliente(db.Model):
    __tablename__ = 'mensajes_cliente'
    id_mensaje = Column(Integer, primary_key=True)
    nombre_usuario = Column(String(200), nullable=False)
    email = Column(String(200), nullable=False)
    mensaje = Column(String(500), nullable=False)
    fecha_creacion = Column(TIMESTAMP, default=datetime.now, nullable=False)

    def __init__(self, nombre_usuario, email, mensaje):
        self.nombre_usuario = nombre_usuario
        self.email = email
        self.mensaje = mensaje

    def __repr__(self):
        return "Mensaje de ({}, {}, {}, {}, {})".format(self.id_mensaje, self.nombre_usuario, self.email, self.mensaje, self.fecha_creacion)

class OpinionesCliente(db.Model):
    __tablename__ = 'opiniones_cliente'
    id_opinion = Column(Integer, primary_key=True)
    nombre_usuario = Column(String(200), nullable=False)
    email = Column(String(200), nullable=False)
    opinion = Column(String(500), nullable=False)
    fecha_creacion = Column(TIMESTAMP, default=datetime.now, nullable=False)

    def __init__(self, nombre_usuario, email, opinion):
        self.nombre_usuario = nombre_usuario
        self.email = email
        self.opinion = opinion

    def __repr__(self):
        return "Opinión de ({}, {}, {}, {}, {})".format(self.id_opinion, self.nombre_usuario, self.email, self.opinion, self.fecha_creacion)

class TareasHoy(db.Model):
    __tablename__ = 'tareas_hoy'
    id_tarea_hoy = Column(Integer, primary_key=True)
    titulo = Column(String(200), nullable=False)
    descripcion = Column(String(200), nullable=False)

    def __init__(self, titulo, descripcion):
        self.titulo = titulo
        self.descripcion = descripcion

    def __repr__(self):
        return "Tarea de hoy ({}, {}, {})".format(self.id_tarea_hoy, self.titulo, self.descripcion)

class TareasSemana(db.Model):
    __tablename__ = 'tareas_semana'
    id_tarea = Column(Integer, primary_key=True)
    contenido_tarea = Column(String(200), nullable=False)
    prioridad = Column(Integer, nullable=False)
    dia_semana = Column(String(20), nullable=False)
    horario_inicio = Column(Time, nullable=False)
    tiempo = Column(Integer, nullable=False)
    switch_alarma = Column(Boolean, default=False)
    switch_recordatorio = Column(Boolean, default=False)
    tiempo_recordatorio = Column(Integer, nullable=True)
    estado = Column(Boolean, default=False)
    id_usuario = Column(Integer, ForeignKey('usuario.id_usuario'), nullable=False)

    usuario = relationship("Usuario", back_populates="tareas")

class TiempoDisponible(db.Model):
    __tablename__ = 'tiempo_disponible'
    id = Column(Integer, primary_key=True)
    id_usuario = Column(Integer, ForeignKey('usuario.id_usuario'), nullable=False)
    minutos_disponibles_lunes = Column(Integer, default=0)
    minutos_disponibles_martes = Column(Integer, default=0)
    minutos_disponibles_miercoles = Column(Integer, default=0)
    minutos_disponibles_jueves = Column(Integer, default=0)
    minutos_disponibles_viernes = Column(Integer, default=0)
    minutos_disponibles_sabado = Column(Integer, default=0)
    minutos_disponibles_domingo = Column(Integer, default=0)
    horas_totales_disponibles_col = Column(Float, default=0.0)

    usuario = relationship("Usuario", back_populates="tiempo_disponible")

    @property
    def horas_totales_disponibles(self):
        total_minutos = (
            self.minutos_disponibles_lunes +
            self.minutos_disponibles_martes +
            self.minutos_disponibles_miercoles +
            self.minutos_disponibles_jueves +
            self.minutos_disponibles_viernes +
            self.minutos_disponibles_sabado +
            self.minutos_disponibles_domingo
        )
        return total_minutos / 60

    def actualizar_horas_totales(self):
        self.horas_totales_disponibles_col = self.horas_totales_disponibles

class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuario'
    id_usuario = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    activo = db.Column(db.Boolean, default=True)

    tiempo_disponible = relationship("TiempoDisponible", back_populates="usuario")
    tareas = relationship("TareasSemana", back_populates="usuario")  # Para relación con TareasSemana

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return str(self.id_usuario)

    def is_active(self):
        return self.activo
