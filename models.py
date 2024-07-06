from sqlalchemy import Column, Integer, Float, String, Boolean, TIMESTAMP, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
import bcrypt
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash # noqa
from datetime import datetime
from flask_login import UserMixin

Base = declarative_base()

class MensajesCliente(Base):
    __tablename__ = 'mensajes_cliente'
    id_mensaje = Column(Integer, primary_key=True)
    nombre_usuario = Column(String(200), nullable=False)
    email = Column(String(200), nullable=False)
    mensaje = Column(String(500), nullable=False)
    fecha_creacion = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)

    def __init__(self, nombre_usuario, email, mensaje):
        self.nombre_usuario = nombre_usuario
        self.email = email
        self.mensaje = mensaje

    def __repr__(self):
        return "Mensaje de ({}, {}, {}, {}, {})".format(self.id_mensaje, self.nombre_usuario, self.email, self.mensaje, self.fecha_creacion)

class OpinionesCliente(Base):
    __tablename__ = 'opiniones_cliente'
    id_opinion = Column(Integer, primary_key=True)
    nombre_usuario = Column(String(200), nullable=False)
    email = Column(String(200), nullable=False)
    opinion = Column(String(500), nullable=False)
    fecha_creacion = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)

    def __init__(self, nombre_usuario, email, opinion):
        self.nombre_usuario = nombre_usuario
        self.email = email
        self.opinion = opinion

    def __repr__(self):
        return "Opinión de ({}, {}, {}, {}, {})".format(self.id_mensaje, self.nombre_usuario, self.email, self.opinion, self.fecha_creacion)

class TareasSemana(Base):
    __tablename__ = 'tareas_semana'
    id_tarea = Column(Integer, primary_key=True, autoincrement=True)
    contenido = Column(String(200), nullable=False)
    prioridad = Column(Integer, nullable=False)
    dias_semana = Column(String(9), nullable=False)
    horario_inicio = Column(String(10), nullable=False)
    tiempo = Column(Float, nullable=False)
    switch_alarma = Column(Boolean, nullable=False, default=False)
    switch_recordatorio = Column(Boolean, nullable=False, default=False)
    tiempo_recordatorio = Column(Integer, nullable=True)
    estado = Column(Boolean, nullable=False, default=False)
    id_usuario = Column(Integer, ForeignKey('usuario.id_usuario'), nullable=False)

    usuario = relationship('Usuario', back_populates='tareas_semana')

    def __init__(self, contenido, prioridad, dias_semana, horario_inicio, tiempo, switch_alarma, switch_recordatorio, tiempo_recordatorio, estado, id_usuario):
        self.contenido = contenido
        self.prioridad = prioridad
        self.dias_semana = dias_semana
        self.horario_inicio = horario_inicio
        self.tiempo = tiempo
        self.switch_alarma = switch_alarma
        self.switch_recordatorio = switch_recordatorio
        self.tiempo_recordatorio = tiempo_recordatorio
        self.estado = estado
        self.id_usuario = id_usuario

def __repr__(self):
    return "Tarea ({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {})".format(
        self.id_tarea, self.contenido, self.prioridad, self.dias_semana,
        self.horario_inicio, self.tiempo, self.switch_alarma,
        self.switch_recordatorio, self.tiempo_recordatorio, self.estado, self.id_usuario)

class TareasHoy(Base):
    __tablename__ = 'tareas_hoy'
    id_tarea_hoy = Column(Integer, primary_key=True)
    titulo = Column(String(200), nullable=False)
    descripcion = Column(String(200), nullable=False)

    def __init__(self, titulo, descripcion):
        self.titulo = titulo
        self.descripcion = descripcion

    def __repr__(self):
        return "Tarea de hoy ({}, {}, {})".format(
            self.id_tarea_hoy, self.titulo, self.descripcion)

class TiempoDisponible(Base):
    __tablename__ = 'tiempo_disponible'
    id_tiempo_disponible = Column(Integer, primary_key=True)
    id_usuario = Column(Integer, ForeignKey('usuario.id_usuario'), nullable=False)
    horas_disponibles_lunes = Column(Integer, default=0)
    horas_disponibles_martes = Column(Integer, default=0)
    horas_disponibles_miercoles = Column(Integer, default=0)
    horas_disponibles_jueves = Column(Integer, default=0)
    horas_disponibles_viernes = Column(Integer, default=0)
    horas_disponibles_sabado = Column(Integer, default=0)
    horas_disponibles_domingo = Column(Integer, default=0)

    usuario = relationship('Usuario', back_populates='tiempo_disponible')

    @property
    def horas_totales_disponibles(self):
        return (self.horas_disponibles_lunes +
                self.horas_disponibles_martes +
                self.horas_disponibles_miercoles +
                self.horas_disponibles_jueves +
                self.horas_disponibles_viernes +
                self.horas_disponibles_sabado +
                self.horas_disponibles_domingo)


class Usuario(Base, UserMixin):
    __tablename__ = 'usuario'

    id_usuario = Column(Integer, primary_key=True)
    nombre = Column(String(200), unique=True, nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    activo = Column(Integer, default=0)

    # Relación con TiempoDisponible
    tiempo_disponible = relationship('TiempoDisponible', back_populates='usuario', uselist=False)
    tareas_semana = relationship('TareasSemana', back_populates='usuario')

    def __init__(self, nombre, email, password):
        self.nombre = nombre
        self.email = email
        self.set_password(password)

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def get_id(self):
        return str(self.id_usuario)
