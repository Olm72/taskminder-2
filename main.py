from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import TareasSemana, Usuario, MensajesCliente, OpinionesCliente, TiempoDisponible, db
from apscheduler.schedulers.background import BackgroundScheduler
from db import session
from datetime import datetime, timedelta
from tzlocal import get_localzone
import pytz
import logging
import os

# Para obtener la zona horaria local del ordenador del usuario
local_tz = get_localzone()
# Convertir la zona horaria a un objeto pytz
local_tz = pytz.timezone(str(local_tz))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'taskminder24_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Por favor, inicia sesión para acceder a esta página."

# Configuración del scheduler
scheduler = BackgroundScheduler(timezone=local_tz)
scheduler.start()

# Configuración del logger para depuración
logging.basicConfig(level=logging.DEBUG)

# Configuración de la base de datos
base_dir = os.path.abspath(os.path.dirname(__file__))
database_dir = os.path.join(base_dir, 'database')
database_path = os.path.join(database_dir, 'task_minder_db.db')

# Crear el directorio de la base de datos si no existe
if not os.path.exists(database_dir):
    os.makedirs(database_dir)

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicialización de la base de datos
db.init_app(app)

# Función para codificar la clave secreta personalizada
def get_secret_key():
    return app.config['SECRET_KEY'].encode()

# Función que se ejecuta antes de cada solicitud para almacenar las cookies.
@app.before_request
def before_request_logging():
    logging.debug('Cookies: ' + str(request.cookies))

# Rutas para las páginas principales de la web
@app.route("/")
def home():
    usuario = request.cookies.get('usuario')
    if usuario:
        return render_template('sitio/index.html', usuario=usuario)
    return render_template('sitio/index.html')

# Rutas para los diferentes html del menú:
@app.route("/aplicacion")
@login_required
def aplicacion():
    return redirect(url_for('taskminder'))

@app.route("/registrate")
def registrate():
    return render_template('sitio/registrate.html')

@app.route("/sobre_nosotros")
def sobre_nosotros():
    return render_template('sitio/sobre_nosotros.html')

@app.route("/opiniones")
def opiniones():
    return render_template('sitio/opiniones.html')

@app.route("/tu_opinion_importa", methods=['GET', 'POST'])
def tu_opinion_importa():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        opinion = request.form.get('opinion')
        acuerdo = request.form.get('acuerdo')

        if acuerdo:
            nueva_opinion = OpinionesCliente(nombre_usuario=nombre, email=email, opinion=opinion)
            session.add(nueva_opinion)
            session.commit()
            flash('Opinión enviada con éxito')
            return redirect(url_for('tu_opinion_importa'))
        else:
            flash('Debes estar de acuerdo con los términos y condiciones para enviar tu opinión.')
            return redirect(url_for('tu_opinion_importa'))
    return render_template('sitio/tu_opinion_importa.html')

@app.route("/premium")
def premium():
    return render_template('sitio/premium.html')

@app.route("/contacto", methods=['GET'])
def contacto():
    return render_template('sitio/contacto.html')

@app.route("/enviar_mensaje", methods=['POST'])
def enviar_mensaje():
    nombre_usuario = request.form['nombre_usuario']
    email = request.form['email']
    mensaje = request.form['mensaje']
    nuevo_mensaje = MensajesCliente(nombre_usuario=nombre_usuario, email=email, mensaje=mensaje)
    session.add(nuevo_mensaje)
    session.commit()

    flash('Mensaje enviado con éxito')
    return redirect(url_for('contacto'))

@app.route("/terminos_condiciones")
def terminos_condiciones():
    return render_template('sitio/terminos_condiciones.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        password = request.form.get('password')
        recordarme = request.form.get('recordarme')
        usuario_obj = session.query(Usuario).filter_by(nombre=usuario).first()
        if usuario_obj and usuario_obj.check_password(password):
            if usuario_obj.activo:
                recordarme_bool = True if recordarme else False
                login_user(usuario_obj, remember=recordarme_bool)
                if current_user.is_authenticated:
                    return redirect(url_for('taskminder'))
            else:
                flash('Tu cuenta está inactiva. Contacta al administrador.', 'error')
                return render_template('sitio/login.html')
        else:
            flash('Credenciales inválidas', 'error')
            return render_template('sitio/login.html')

    if current_user.is_authenticated:
        return redirect(url_for('taskminder'))
    return render_template('sitio/login.html')

@app.route("/logout")
@login_required
def logout():
    logout_user()

    flash('Has cerrado sesión correctamente')
    return redirect(url_for('login'))

@login_manager.user_loader
def cargar_usuario(id_usuario):
    return session.get(Usuario, int(id_usuario))

@app.route("/confirmacion-registro-html")
def confirmacion_registro_html():
    return render_template('sitio/confirmacion_registro.html')

@app.route("/confirmacion-registro", methods=['GET', 'POST'])
def confirmacion_registro():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        email = request.form.get('email')
        password = request.form.get('password')
        print("Intentando registrar nuevo usuario: " + usuario)

        if not usuario or not email or not password:
            mensaje = 'Por favor, completa todos los campos.'
            return render_template('sitio/registrate.html', mensaje=mensaje)

        usuario_existente = session.query(Usuario).filter_by(nombre=usuario).first()
        if usuario_existente:
            mensaje = 'El nombre de usuario ya está en uso.'
            return render_template('sitio/registrate.html', mensaje=mensaje)

        email_existente = session.query(Usuario).filter_by(email=email).first()
        if email_existente:
            mensaje = 'El correo electrónico ya está en uso.'
            return render_template('sitio/registrate.html', mensaje=mensaje)

        nuevo_usuario = Usuario(nombre=usuario, email=email)
        nuevo_usuario.set_password(password)
        nuevo_usuario.activo = True
        session.add(nuevo_usuario)
        session.commit()

        print("Usuario " + usuario + " registrado correctamente")

        flash('¡Enhorabuena, te has registrado con éxito! Ya puedes iniciar sesión.')

        return redirect(url_for('confirmacion_registro_html'))
    return render_template('sitio/registrate.html')

@app.route('/taskminder', methods=['GET', 'POST'])
@login_required
def taskminder():
    id_usuario = current_user.id_usuario

    tiempo_disponible = session.query(TiempoDisponible).filter_by(id_usuario=id_usuario).first()

    if tiempo_disponible:
        horas = {
            'Lunes': tiempo_disponible.minutos_disponibles_lunes / 60,
            'Martes': tiempo_disponible.minutos_disponibles_martes / 60,
            'Miercoles': tiempo_disponible.minutos_disponibles_miercoles / 60,
            'Jueves': tiempo_disponible.minutos_disponibles_jueves / 60,
            'Viernes': tiempo_disponible.minutos_disponibles_viernes / 60,
            'Sabado': tiempo_disponible.minutos_disponibles_sabado / 60,
            'Domingo': tiempo_disponible.minutos_disponibles_domingo / 60
        }
        horas_totales_disponibles = tiempo_disponible.horas_totales_disponibles
    else:
        horas = {
            'Lunes': 0,
            'Martes': 0,
            'Miercoles': 0,
            'Jueves': 0,
            'Viernes': 0,
            'Sabado': 0,
            'Domingo': 0
        }
        horas_totales_disponibles = 0

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'agregar':
            contenido_tarea = request.form.get('contenido_tarea')
            try:
                prioridad = request.form.get('prioridad')
                tiempo = int(request.form.get('tiempo'))
            except ValueError:
                flash('Por favor, introduce valores válidos para prioridad y tiempo.')
                return redirect(url_for('taskminder'))

            nueva_tarea = TareasSemana(
                contenido_tarea=contenido_tarea,
                prioridad=prioridad,
                dias_semana="",
                horario_inicio="",
                tiempo=tiempo,
                switch_alarma=False,
                switch_recordatorio=False,
                tiempo_recordatorio=None,
                estado=False,
                id_usuario=id_usuario
            )
            session.add(nueva_tarea)
            session.commit()
            flash('Tarea agregada con éxito')

        elif action.startswith('modificar'):
            index = int(action.split('-')[1])
            tarea = session.query(TareasSemana).filter_by(id_tarea=index, id_usuario=id_usuario).first()
            if tarea:
                tarea.contenido_tarea = request.form.get('contenido_tarea')
                try:
                    tarea.prioridad = request.form.get('prioridad')
                    tarea.tiempo = int(request.form.get('tiempo'))
                except ValueError:
                    flash('Por favor, introduce valores válidos para prioridad y tiempo.')
                    return redirect(url_for('taskminder'))
                session.commit()
                flash('Tarea modificada con éxito')
            else:
                flash('Tarea no encontrada')

        elif action.startswith('eliminar'):
            index = int(action.split('-')[1])
            tarea = session.query(TareasSemana).filter_by(id_tarea=index, id_usuario=id_usuario).first()
            if tarea:
                session.delete(tarea)
                session.commit()
                flash('Tarea eliminada con éxito')
            else:
                flash('Tarea no encontrada')

    tareas = session.query(TareasSemana).filter_by(id_usuario=id_usuario).all()

    tareas_por_dia = {
        'lunes': [],
        'martes': [],
        'miercoles': [],
        'jueves': [],
        'viernes': [],
        'sabado': [],
        'domingo': []
    }

    for tarea in tareas:
        dias = tarea.dias_semana.split(',')
        for dia in dias:
            tareas_por_dia[dia].append(tarea)

    return render_template('sitio/taskminder.html', tareas=tareas_por_dia, horas=horas, horas_totales_disponibles=horas_totales_disponibles)

@app.route('/configurar_horas', methods=['POST'])
@login_required
def configurar_horas():
    data = request.form
    minutos_disponibles_por_dia = {dia: int(data.get(dia, 0)) for dia in ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']}

    tiempo_disponible = session.query(TiempoDisponible).filter_by(id_usuario=current_user.id_usuario).first()
    if not tiempo_disponible:
        tiempo_disponible = TiempoDisponible(id_usuario=current_user.id_usuario)

    tiempo_disponible.minutos_disponibles_lunes = minutos_disponibles_por_dia['lunes']
    tiempo_disponible.minutos_disponibles_martes = minutos_disponibles_por_dia['martes']
    tiempo_disponible.minutos_disponibles_miercoles = minutos_disponibles_por_dia['miercoles']
    tiempo_disponible.minutos_disponibles_jueves = minutos_disponibles_por_dia['jueves']
    tiempo_disponible.minutos_disponibles_viernes = minutos_disponibles_por_dia['viernes']
    tiempo_disponible.minutos_disponibles_sabado = minutos_disponibles_por_dia['sabado']
    tiempo_disponible.minutos_disponibles_domingo = minutos_disponibles_por_dia['domingo']

    session.add(tiempo_disponible)
    session.commit()

    return redirect(url_for('taskminder'))

@app.route("/horas_disponibles", methods=["GET", "POST"])
@login_required
def horas_disponibles():
    if request.method == "POST":
        horas = float(request.form.get("horas"))
        if horas <= 0:
            flash('Por favor, introduce un valor válido para las horas disponibles.')
            return redirect(url_for("horas_disponibles"))

        tiempo_disponible_obj = session.query(TiempoDisponible).filter_by(id_usuario=current_user.id_usuario).first()
        if tiempo_disponible_obj:
            tiempo_disponible_obj.minutos_disponibles_lunes = horas * 60 / 7  # Distribuir las horas por igual para todos los días
            tiempo_disponible_obj.minutos_disponibles_martes = horas * 60 / 7
            tiempo_disponible_obj.minutos_disponibles_miercoles = horas * 60 / 7
            tiempo_disponible_obj.minutos_disponibles_jueves = horas * 60 / 7
            tiempo_disponible_obj.minutos_disponibles_viernes = horas * 60 / 7
            tiempo_disponible_obj.minutos_disponibles_sabado = horas * 60 / 7
            tiempo_disponible_obj.minutos_disponibles_domingo = horas * 60 / 7
        else:
            tiempo_disponible_obj = TiempoDisponible(
                id_usuario=current_user.id_usuario,
                minutos_disponibles_lunes=horas * 60 / 7,
                minutos_disponibles_martes=horas * 60 / 7,
                minutos_disponibles_miercoles=horas * 60 / 7,
                minutos_disponibles_jueves=horas * 60 / 7,
                minutos_disponibles_viernes=horas * 60 / 7,
                minutos_disponibles_sabado=horas * 60 / 7,
                minutos_disponibles_domingo=horas * 60 / 7
            )
            session.add(tiempo_disponible_obj)
        session.commit()

        flash("Horas disponibles actualizadas con éxito.")
        return redirect(url_for("taskminder"))

    tiempo_disponible_obj = session.query(TiempoDisponible).filter_by(id_usuario=current_user.id_usuario).first()
    horas_disponibles_ = tiempo_disponible_obj.horas_totales_disponibles if tiempo_disponible_obj else 0
    return render_template('sitio/horas_disponibles.html', horas_disponibles=horas_disponibles_)

@app.route('/tareas_creadas', methods=['POST'])
@login_required
def agregar_tarea():
    data = request.get_json()
    id_tarea = int(data.get("id_tarea"))
    contenido_tarea = data.get('contenido_tarea')
    prioridad = data.get('prioridad')
    dias_semana = ','.join(data.get('dias_semana', []))
    horario_inicio = data.get('horario_inicio')
    tiempo = int(data.get('tiempo'))
    switch_alarma = bool(data.get('alarma'))
    switch_recordatorio = bool(data.get('recordatorio'))
    tiempo_recordatorio = int(data.get('tiempo_recordatorio'))
    estado = bool(data.get('estado'))

    nueva_tarea = TareasSemana(
        id_tarea=id_tarea,
        contenido_tarea=contenido_tarea,
        prioridad=prioridad,
        dias_semana=dias_semana,
        horario_inicio=horario_inicio,
        tiempo=tiempo,
        switch_alarma=switch_alarma,
        switch_recordatorio=switch_recordatorio,
        tiempo_recordatorio=tiempo_recordatorio,
        estado=estado,
        id_usuario=current_user.id_usuario
    )
    session.add(nueva_tarea)
    session.commit()

    return jsonify({"success": True})

@app.route('/obtener_tareas')
@login_required
def obtener_tareas():
    tareas = session.query(TareasSemana).filter_by(id_usuario=current_user.id_usuario).all()
    tareas_dict = [{'id': tarea.id_tarea, 'contenido_tarea': tarea.contenido_tarea, 'prioridad': tarea.prioridad,
                    'dias_semana': tarea.dias_semana, 'horario_inicio': tarea.horario_inicio,
                    'tiempo': tarea.tiempo, 'realizada': tarea.estado} for tarea in tareas]
    return jsonify({'tareas': tareas_dict})

@app.route('/modificar_tarea/<int:index>', methods=['GET', 'POST'])
def modificar_tarea(index):
    tarea = session.query(TareasSemana).filter_by(id_tarea=index, id_usuario=current_user.id_usuario).first()
    if not tarea:
        flash('Tarea no encontrada')
        return redirect(url_for('taskminder'))

    if request.method == 'POST':
        tarea.contenido_tarea = request.form.get('contenido_tarea')
        try:
            tarea.prioridad = request.form.get('prioridad')
            tarea.tiempo = int(request.form.get('tiempo'))
        except ValueError:
            flash('Por favor, introduce valores válidos para prioridad y tiempo.')
            return redirect(url_for('modificar_tarea', index=index))
        session.commit()
        flash('Tarea modificada con éxito')
        return redirect(url_for('taskminder'))

    return render_template('modificar_tarea.html', tarea=tarea, index=index)

@app.route('/eliminar_tarea/<int:index>', methods=['POST'])
def eliminar_tarea(index):
    tarea = session.query(TareasSemana).filter_by(id_tarea=index, id_usuario=current_user.id_usuario).first()
    if not tarea:
        flash('Tarea no encontrada')
        return redirect(url_for('taskminder'))

    session.delete(tarea)
    session.commit()
    flash('Tarea eliminada con éxito.')
    return redirect(url_for('taskminder'))

@app.route('/borrar_tarea', methods=['POST'])
@login_required
def borrar_tarea():
    try:
        tarea_id = request.json['id_tarea']
        tarea = session.query(TareasSemana).filter_by(id_tarea=tarea_id, id_usuario=current_user.id_usuario).first()

        if tarea:
            session.delete(tarea)
            session.commit()
            return jsonify({'success': True}), 200
        else:
            return jsonify({'error': 'Tarea no encontrada'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def alarma(tarea):
    print("Alarma para la tarea: " + tarea.contenido_tarea)

@app.route('/configurar_alarma', methods=['POST'])
@login_required
def configurar_alarma():
    index = int(request.form.get('index'))
    tarea = session.query(TareasSemana).filter_by(id_tarea=index, id_usuario=current_user.id_usuario).first()

    if not tarea:
        flash('Tarea no encontrada', 'error')
        return redirect(url_for('taskminder'))

    tiempo = request.form.get('tiempo')
    if tiempo:
        run_date = datetime.strptime(tiempo, '%Y-%m-%dT%H:%M')
        scheduler.add_job(alarma, 'date', run_date=run_date, args=[tarea])
        flash('Alarma configurada con éxito.')
    else:
        flash('Por favor, proporciona una fecha y hora válida para la alarma.', 'error')

    return redirect(url_for('taskminder'))

@app.route('/ver_horario')
@login_required
def ver_horario():
    tareas = session.query(TareasSemana).filter_by(id_usuario=current_user.id_usuario).all()
    tiempo_disponible_obj = session.query(TiempoDisponible).filter_by(id_usuario=current_user.id_usuario).first()
    tiempo_disponible = tiempo_disponible_obj.horas_totales_disponibles if tiempo_disponible_obj else 0

    recalcular_horas(tareas, tiempo_disponible)

    return render_template('ver_horario.html', horas=tiempo_disponible, tareas=tareas)

def recalcular_horas(tareas, tiempo_disponible):
    reduccion_por_prioridad = {
        3: 0.1,
        2: 0.2,
        1: 0.3,
        0: 0.4
    }

    nuevos_tiempos = []

    for tarea in tareas:
        prioridad = tarea.prioridad
        tiempo_inicial = tarea.tiempo
        if prioridad in reduccion_por_prioridad:
            porcentaje_reduccion = reduccion_por_prioridad[prioridad]
            nuevo_tiempo = tiempo_inicial * (1 - porcentaje_reduccion)
            nuevo_tiempo = max(nuevo_tiempo, tiempo_inicial * 0.5)
            nuevos_tiempos.append(nuevo_tiempo)
        else:
            nuevos_tiempos.append(tiempo_inicial)

    tiempo_total_asignado = sum(nuevos_tiempos)

    if tiempo_total_asignado > tiempo_disponible:
        factor_ajuste = tiempo_disponible / tiempo_total_asignado
        nuevos_tiempos = [tiempo * factor_ajuste for tiempo in nuevos_tiempos]

    for tarea, nuevo_tiempo in zip(tareas, nuevos_tiempos):
        tarea.tiempo = nuevo_tiempo
        session.commit()

    return nuevos_tiempos

def verificar_cambio_actividad():
    usuarios = session.query(Usuario).all()
    for usuario in usuarios:
        tareas = session.query(TareasSemana).filter_by(id_usuario=usuario.id_usuario).all()
        for tarea in tareas:
            tiempo_actual = datetime.now().time()
            horario_inicio = datetime.strptime(tarea.horario_inicio, '%H:%M').time()
            if horario_inicio <= tiempo_actual < (datetime.combine(datetime.today(), horario_inicio) + timedelta(minutes=tarea.tiempo)).time():
                usuario.ultima_actividad = tarea.contenido_tarea
                session.commit()
                break

scheduler.add_job(verificar_cambio_actividad, 'interval', minutes=1)

@app.route("/tareas_hoy")
@login_required
def tareas_hoy():
    return render_template('sitio/tareas_hoy.html')

@app.errorhandler(404)
def pagina_no_encontrada():
    return render_template('404.html'), 404


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
