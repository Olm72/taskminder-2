from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import TareasSemana, Usuario, MensajesCliente, OpinionesCliente, TiempoDisponible, db
from apscheduler.schedulers.background import BackgroundScheduler
from db import session
from datetime import datetime, timedelta
from tzlocal import get_localzone
from sqlalchemy.sql import text
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
login_manager.login_message = "Por favor, inicia sesión para entrar."

# Configuración del scheduler
scheduler = BackgroundScheduler(timezone=local_tz)
scheduler.start()

# Configuración del logger para depuración
logging.basicConfig(level=logging.DEBUG)

# Configuración de la base de datos
base_dir = os.path.abspath(os.path.dirname(__file__))
database_dir = os.path.join(base_dir, 'database')
database_path = os.path.join(database_dir, 'task_minder_db.db')

# CreaMOS el directorio de la BBDD si no existe
if not os.path.exists(database_dir):
    os.makedirs(database_dir)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + database_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicialización de la base de datos
db.init_app(app)

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
                flash('Has iniciado sesión', 'success')
                return redirect(url_for('taskminder'))
            else:
                flash('Tu cuenta está inactiva. Contacta al administrador.', 'error')
                return render_template('sitio/login.html')
        else:
            flash('Credenciales inválidas', 'error')
            return render_template('sitio/login.html')

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

# Funciones de redondeos
# Función para redondear a cuartos los decimales de los tiempos en horas
def redondear_a_cuartos(valor):
    if isinstance(valor, str):
        valor = float(valor)
    return round(valor * 4) / 4

# Función para redondear a dos decimales
def redondear_a_dos_decimales(valor):
    if isinstance(valor, str):
        valor = float(valor)
    return "{:.2f}".format(valor)

# Registramos los filtros en Jinja
app.jinja_env.filters['redondear_a_cuartos'] = redondear_a_cuartos
app.jinja_env.filters['redondear_a_dos_decimales'] = redondear_a_dos_decimales

@app.template_filter('redondear_a_dos_decimales')
def redondear_a_dos_decimales(valor):
    if isinstance(valor, str):
        valor = float(valor)
    return "{:.2f}".format(valor)

@app.route('/taskminder', methods=['GET', 'POST'])
@login_required
def taskminder():
    id_usuario = current_user.id_usuario

    tiempo_disponible = session.query(TiempoDisponible).filter_by(id_usuario=id_usuario).first()

    if tiempo_disponible:
        horas = {
            'lunes': redondear_a_dos_decimales(redondear_a_cuartos(float(tiempo_disponible.minutos_disponibles_lunes) / 60)),
            'martes': redondear_a_dos_decimales(redondear_a_cuartos(float(tiempo_disponible.minutos_disponibles_martes) / 60)),
            'miercoles': redondear_a_dos_decimales(redondear_a_cuartos(float(tiempo_disponible.minutos_disponibles_miercoles) / 60)),
            'jueves': redondear_a_dos_decimales(redondear_a_cuartos(float(tiempo_disponible.minutos_disponibles_jueves) / 60)),
            'viernes': redondear_a_dos_decimales(redondear_a_cuartos(float(tiempo_disponible.minutos_disponibles_viernes) / 60)),
            'sabado': redondear_a_dos_decimales(redondear_a_cuartos(float(tiempo_disponible.minutos_disponibles_sabado) / 60)),
            'domingo': redondear_a_dos_decimales(redondear_a_cuartos(float(tiempo_disponible.minutos_disponibles_domingo) / 60))
        }
        horas_totales_disponibles = redondear_a_dos_decimales(redondear_a_cuartos(float(tiempo_disponible.horas_totales_disponibles)))
    else:
        horas = {
            'lunes': 0,
            'martes': 0,
            'miercoles': 0,
            'jueves': 0,
            'viernes': 0,
            'sabado': 0,
            'domingo': 0
        }
        horas_totales_disponibles = 0

    tareas = session.query(TareasSemana).filter_by(id_usuario=id_usuario).order_by(TareasSemana.horario_inicio).all()

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
        dia = tarea.dia_semana
        if dia in tareas_por_dia:
            tarea.tiempo = int(tarea.tiempo)  # Asegúrate de que los minutos no tengan decimales
            tareas_por_dia[dia].append(tarea)

    return render_template('sitio/taskminder.html', tareas=tareas_por_dia, horas=horas, horas_totales_disponibles=horas_totales_disponibles)

@app.route('/reemplazar_tiempo_disponible', methods=['POST'])
@login_required
def reemplazar_tiempo_disponible():
    data = request.get_json()

    replace_data = {
        'id': data.get('id', None),  # ID de la fila a reemplazar
        'id_usuario': current_user.id_usuario,
        'minutos_disponibles_lunes': data.get('minutos_disponibles_lunes', 0),
        'minutos_disponibles_martes': data.get('minutos_disponibles_martes', 0),
        'minutos_disponibles_miercoles': data.get('minutos_disponibles_miercoles', 0),
        'minutos_disponibles_jueves': data.get('minutos_disponibles_jueves', 0),
        'minutos_disponibles_viernes': data.get('minutos_disponibles_viernes', 0),
        'minutos_disponibles_sabado': data.get('minutos_disponibles_sabado', 0),
        'minutos_disponibles_domingo': data.get('minutos_disponibles_domingo', 0),
        'horas_totales_disponibles_col': data.get('horas_totales_disponibles_col', 0.0)
    }

    replace_query = text("""
        REPLACE INTO tiempo_disponible (
            id, id_usuario, minutos_disponibles_lunes, minutos_disponibles_martes, 
            minutos_disponibles_miercoles, minutos_disponibles_jueves, 
            minutos_disponibles_viernes, minutos_disponibles_sabado, 
            minutos_disponibles_domingo, horas_totales_disponibles_col
        ) VALUES (
            :id, :id_usuario, :minutos_disponibles_lunes, :minutos_disponibles_martes, 
            :minutos_disponibles_miercoles, :minutos_disponibles_jueves, 
            :minutos_disponibles_viernes, :minutos_disponibles_sabado, 
            :minutos_disponibles_domingo, :horas_totales_disponibles_col
        );
    """)

    session.execute(replace_query, replace_data)
    session.commit()

    return jsonify({"success": True, "message": "Tiempo disponible reemplazado correctamente"})

from datetime import datetime

@app.route('/agregar_tarea', methods=['POST'])
@login_required
def agregar_tarea():
    if request.is_json:
        data = request.get_json()
    else:
        return jsonify({"error": "La solicitud debe tener el tipo de contenido 'application/json'"}), 415

    try:
        contenido_tarea = data.get('contenido_tarea')
        if contenido_tarea is None:
            return jsonify({"error": "Introduce el contenido de la tarea por favor"}), 400

        prioridad = data.get('prioridad')
        dias_semana = data.get('dias_semana')
        horario_inicio = data.get('horario_inicio')
        if horario_inicio is None:
            return jsonify({"error": "Introduce el horario por favor"}), 400

        # Convertimos la cadena de horario a objeto "time" de Python
        horario_inicio = datetime.strptime(horario_inicio, '%H:%M').time()

        tiempo = data.get('tiempo')
        if tiempo is not None:
            tiempo = int(tiempo)

        switch_alarma = data.get('alarma') == True
        switch_recordatorio = data.get('recordatorio') == True

        tiempo_recordatorio = data.get('tiempo_recordatorio')
        if tiempo_recordatorio is not None:
            tiempo_recordatorio = int(tiempo_recordatorio)

        estado = data.get('realizada_hoy') == True

        # Verificar si es una tarea existente o nueva
        id_tarea = data.get("index")

        if id_tarea:
            # Eliminar las tareas existentes con el mismo index
            session.query(TareasSemana).filter_by(id_tarea=id_tarea, id_usuario=current_user.id_usuario).delete()
            session.commit()

        for dia in dias_semana:
            nueva_tarea = TareasSemana(
                contenido_tarea=contenido_tarea,
                prioridad=prioridad,
                dia_semana=dia,
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
        flash('Tarea guardada con éxito', 'success')

        # Obtenemos todas las tareas del usuario
        tareas = session.query(TareasSemana).filter_by(id_usuario=current_user.id_usuario).order_by(TareasSemana.horario_inicio).all()
        tiempo_disponible = session.query(TiempoDisponible).filter_by(id_usuario=current_user.id_usuario).first().horas_totales_disponibles * 60  # Convertimos tiempo a minutos
        reestructurar_tareas(tareas, tiempo_disponible)

    except Exception as e:
        session.rollback()
        return jsonify({"error": "Error al agregar la tarea: " + str(e)}), 500

    return jsonify({"success": True})

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

    tiempo_disponible.actualizar_horas_totales()  # Actualiza las horas totales disponibles

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

@app.route('/posponer_alarma', methods=['POST'])
@login_required
def posponer_alarma():
    data = request.form
    id_tarea = int(data.get('id_tarea'))
    tiempo_posponer = int(data.get('tiempo_posponer', 0))  # El tiempo es en minutos

    tarea = session.query(TareasSemana).filter_by(id_tarea=id_tarea, id_usuario=current_user.id_usuario).first()

    if not tarea:
        flash('Tarea no encontrada.', 'error')
        return redirect(url_for('taskminder'))

    try:
        # Para posponer el horario de inicio de la tarea
        nuevo_horario_inicio = datetime.strptime(tarea.horario_inicio, '%H:%M') + timedelta(minutes=tiempo_posponer)
        tarea.horario_inicio = nuevo_horario_inicio.strftime('%H:%M')

        session.commit()

        # Recalculamos tiempos de todas las tareas
        tareas = session.query(TareasSemana).filter_by(id_usuario=current_user.id_usuario).order_by(TareasSemana.horario_inicio).all()
        tiempo_disponible = session.query(TiempoDisponible).filter_by(id_usuario=current_user.id_usuario).first().horas_totales_disponibles * 60  # Convertir a minutos
        reestructurar_tareas(tareas, tiempo_disponible)

        flash('Tarea pospuesta ' + str(tiempo_posponer) + ' minutos.', 'success')
    except Exception as e:
        flash('Error al posponer la tarea: ' + str(e), 'error')
        return redirect(url_for('taskminder'))

    return redirect(url_for('taskminder'))

@app.route('/borrar_tarea', methods=['POST'])
@login_required
def borrar_tarea():
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()

    try:
        tarea_id = int(data['id_tarea'])
        tarea = session.query(TareasSemana).filter_by(id_tarea=tarea_id, id_usuario=current_user.id_usuario).first()

        if tarea:
            session.delete(tarea)
            session.commit()
            return jsonify({'success': True}), 200
        else:
            return jsonify({'error': 'Tarea no encontrada'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/modificar_tarea/<int:index>', methods=['GET', 'POST'])
@login_required
def modificar_tarea(id_tarea, dia):
    tarea = session.query(TareasSemana).filter_by(id_tarea=id_tarea, dia_semana=dia, id_usuario=current_user.id_usuario).first()
    if not tarea:
        flash('Tarea no encontrada')
        return redirect(url_for('taskminder'))

    if request.method == 'POST':
        tarea.contenido_tarea = request.form.get('contenido_tarea')
        try:
            tarea.prioridad = int(request.form.get('prioridad'))
            tarea.tiempo = int(request.form.get('tiempo'))
        except ValueError:
            flash('Por favor, introduce valores válidos para prioridad y tiempo.')
            return redirect(url_for('taskminder', id_tarea=id_tarea, dia=dia))
        session.commit()
        flash('Tarea modificada con éxito')
        return redirect(url_for('taskminder'))

    return render_template('modificar_tarea.html', tarea=tarea, id_tarea=id_tarea, dia=dia)

@app.route('/eliminar_tarea/<int:index>', methods=['POST'])
@login_required
def eliminar_tarea(index):
    tarea = session.query(TareasSemana).filter_by(id_tarea=index, id_usuario=current_user.id_usuario).first()
    if not tarea:
        flash('Tarea no encontrada')
        return redirect(url_for('taskminder'))

    session.delete(tarea)
    session.commit()
    flash('Tarea eliminada con éxito.')
    return redirect(url_for('taskminder'))

@app.route('/actualizar_tarea', methods=['POST'])
@login_required
def actualizar_tarea():
    if request.is_json:
        data = request.get_json()
    else:
        return jsonify({"error": "La solicitud debe tener el tipo de contenido 'application/json'"}), 415

    tarea_id = data.get("tarea_id")
    estado = data.get("estado")

    tarea = session.query(TareasSemana).filter_by(id_tarea=tarea_id, id_usuario=current_user.id_usuario).first()

    if not tarea:
        return jsonify({"error": "Tarea no encontrada"}), 404

    tarea.estado = estado
    session.commit()

    return jsonify({"success": True})

@app.route('/obtener_tareas')
@login_required
def obtener_tareas():
    tareas = session.query(TareasSemana).filter_by(id_usuario=current_user.id_usuario).all()
    tareas_dict = [{'id': tarea.id_tarea, 'contenido_tarea': tarea.contenido_tarea, 'prioridad': tarea.prioridad,
                    'dia_semana': tarea.dia_semana, 'horario_inicio': tarea.horario_inicio,
                    'tiempo': tarea.tiempo, 'realizada': tarea.estado} for tarea in tareas]
    return jsonify({'tareas': tareas_dict})

@app.route("/tareas_hoy")
@login_required
def tareas_hoy():
    return render_template('sitio/tareas_hoy.html')

@app.route('/ver_horario')
@login_required
def ver_horario():
    tareas = session.query(TareasSemana).filter_by(id_usuario=current_user.id_usuario).all()
    tiempo_disponible_obj = session.query(TiempoDisponible).filter_by(id_usuario=current_user.id_usuario).first()
    tiempo_disponible = tiempo_disponible_obj.horas_totales_disponibles if tiempo_disponible_obj else 0

    recalcular_horas(tareas, tiempo_disponible)

    return render_template('ver_horario.html', horas=tiempo_disponible, tareas=tareas)

# Funciones auxiliares:

#  Esta función recalcula los tiempos de las tareas teniendo en cuenta las prioridades y asegura que el tiempo total de las tareas no exceda el tiempo disponible.
def ajustar_tiempos_tareas(tareas, tiempo_disponible):
    reduccion_por_prioridad = {
        3: 0.1,  # Prioridad máxima
        2: 0.2,  # Prioridad importante
        1: 0.3,  # Prioridad moderada
        0: 0.4   # Prioridad menor
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

# Esta función se encarga de ajustar los tiempos de las tareas siguientes y reducirlas proporcionalmente según su importancia.
def reestructurar_tareas(tareas, total_horas_disponibles):
    # Paso 1: Calculamos los tiempos ajustados iniciales
    tiempos_ajustados_iniciales = []
    reduccion_por_prioridad = {
        3: 0.1,  # Prioridad máxima
        2: 0.2,  # Prioridad importante
        1: 0.3,  # Prioridad moderada
        0: 0.4   # Prioridad menor
    }

    for tarea in tareas:
        prioridad = tarea.prioridad
        tiempo_inicial = tarea.tiempo
        if prioridad in reduccion_por_prioridad:
            porcentaje_reduccion = reduccion_por_prioridad[prioridad]
            tiempo_ajustado = tiempo_inicial * (1 - porcentaje_reduccion)
            tiempo_ajustado = max(tiempo_ajustado, tiempo_inicial * 0.5)  # No reducir más del 50%
            tiempos_ajustados_iniciales.append(tiempo_ajustado)
        else:
            tiempos_ajustados_iniciales.append(tiempo_inicial)

    # Paso 2: Sumamos los tiempos ajustados iniciales y comparamos con las horas disponibles
    total_tiempo_ajustado_inicial = sum(tiempos_ajustados_iniciales)
    diferencia_tiempo = total_horas_disponibles - total_tiempo_ajustado_inicial

    if diferencia_tiempo > 0:
        # Paso 3: Reorganizamos el tiempo faltante según la prioridad de cada tarea, proporcionalmente.
        total_reduccion = sum(reduccion_por_prioridad.get(tarea.prioridad, 0.4) for tarea in tareas)

        tiempos_finales = []
        for tarea, tiempo_ajustado in zip(tareas, tiempos_ajustados_iniciales):
            prioridad = tarea.prioridad
            proporcion_redistribucion = reduccion_por_prioridad.get(prioridad, 0.4) / total_reduccion
            tiempo_final = tiempo_ajustado + (proporcion_redistribucion * diferencia_tiempo)
            tiempos_finales.append(tiempo_final)
    else:
        tiempos_finales = tiempos_ajustados_iniciales

    # Aplicamos los nuevos tiempos ajustados a las tareas y los guardamos en la BBDD
    for tarea, tiempo_final in zip(tareas, tiempos_finales):
        tarea.tiempo = max(tiempo_final, tarea.tiempo * 0.5)  # ¡No reducir más del 50% del tiempo fijado por el usuario como tiempo máximo para dedicar a las tareas del día!
        session.commit()

    return tiempos_finales

def recalcular_horas(tareas, tiempo_disponible):
    reduccion_por_prioridad = {
        3: 0.1,  # Máxima
        2: 0.2,  # Importante
        1: 0.3,  # Moderada
        0: 0.4   # Menor
    }

    nuevos_tiempos = []
    for tarea in tareas:
        prioridad = tarea.prioridad
        tiempo_inicial = tarea.tiempo
        if prioridad in reduccion_por_prioridad:
            porcentaje_reduccion = reduccion_por_prioridad[prioridad]
            tiempo_ajustado = tiempo_inicial * (1 - porcentaje_reduccion)
            nuevos_tiempos.append(tiempo_ajustado)
        else:
            nuevos_tiempos.append(tiempo_inicial)

    tiempo_total_ajustado_inicial = sum(nuevos_tiempos)

    if tiempo_total_ajustado_inicial < tiempo_disponible:
        tiempo_faltante = tiempo_disponible - tiempo_total_ajustado_inicial
        suma_reducciones = sum(reduccion_por_prioridad.values())

        for i, tarea in enumerate(tareas):
            porcentaje_reduccion = reduccion_por_prioridad.get(tarea.prioridad, 0)
            proporcion_ajuste = porcentaje_reduccion / suma_reducciones
            tiempo_extra = proporcion_ajuste * tiempo_faltante
            nuevos_tiempos[i] += tiempo_extra

    for tarea, nuevo_tiempo in zip(tareas, nuevos_tiempos):
        tarea.tiempo = max(nuevo_tiempo, tarea.tiempo * 0.5)
        session.commit()

    return nuevos_tiempos

def verificar_cambio_actividad():
    usuarios = session.query(Usuario).all()
    for usuario in usuarios:
        tareas = session.query(TareasSemana).filter_by(id_usuario=usuario.id_usuario).all()
        for tarea in tareas:
            if not tarea.horario_inicio:
                continue
            tiempo_actual = datetime.now().time()
            horario_inicio = datetime.strptime(tarea.horario_inicio.strftime('%H:%M'), '%H:%M').time()
            if horario_inicio <= tiempo_actual < (datetime.combine(datetime.today(), horario_inicio) + timedelta(minutes=tarea.tiempo)).time():
                usuario.ultima_actividad = tarea.contenido_tarea
                session.commit()
                break

scheduler.add_job(verificar_cambio_actividad, 'interval', minutes=1)

def alarma(tarea):
    print("Alarma para la tarea: " + tarea.contenido_tarea)


# Para errores:
@app.errorhandler(404)
def pagina_no_encontrada(e):
    return render_template('404.html'), 404


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
