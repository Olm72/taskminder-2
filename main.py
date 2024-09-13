from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import TareasSemana, Usuario, MensajesCliente, OpinionesCliente, TiempoDisponible, db
from apscheduler.schedulers.background import BackgroundScheduler
from db import session
from datetime import datetime, timedelta
from sqlalchemy.sql import text
from pygame import mixer
import pytz
import logging
import os

# Para obtener la zona horaria local de Madrid, España
local_tz = pytz.timezone('Europe/Madrid')

# Convertimos la zona horaria a un objeto pytz
local_tz = pytz.timezone(str(local_tz))

# Creamos la app de flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'taskminder24_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Por favor, inicia sesión para entrar."

# Configuración del logger para mostrar información en la consola
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Verificamos que el scheduler se está iniciando
logger.info("Iniciando el scheduler...")
logger.info("Scheduler iniciado correctamente.")

# Configuración del scheduler
scheduler = BackgroundScheduler(timezone=local_tz)
scheduler.start()

# Configuración del logger para depuración
logging.basicConfig(level=logging.DEBUG)

# Configuración de la BBDD
base_dir = os.path.abspath(os.path.dirname(__file__))
database_dir = os.path.join(base_dir, 'database')
database_path = os.path.join(database_dir, 'task_minder_db.db')

# Creamos el directorio de la BBDD si no existe
if not os.path.exists(database_dir):
    os.makedirs(database_dir)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + database_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicialización de la BBDD
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

@app.template_filter('redondear_a_dos_decimales')
def redondear_a_dos_decimales(valor):
    if isinstance(valor, str):
        valor = float(valor)
    return "{:.2f}".format(valor)

# Registramos los filtros en Jinja
app.jinja_env.filters['redondear_a_cuartos'] = redondear_a_cuartos
app.jinja_env.filters['redondear_a_dos_decimales'] = redondear_a_dos_decimales

@app.route('/taskminder', methods=['GET', 'POST'])
@login_required
def taskminder():
    id_usuario = current_user.id_usuario

    # Obtenemos el tiempo disponible del usuario
    tiempo_disponible = session.query(TiempoDisponible).filter_by(id_usuario=id_usuario).first()

    # Verificamos si se encontró el tiempo disponible, si no, iniciamos con 0
    if tiempo_disponible:
        horas = {
            'lunes': redondear_a_dos_decimales(redondear_a_cuartos(int(tiempo_disponible.minutos_disponibles_lunes) / 60)),
            'martes': redondear_a_dos_decimales(redondear_a_cuartos(int(tiempo_disponible.minutos_disponibles_martes) / 60)),
            'miercoles': redondear_a_dos_decimales(redondear_a_cuartos(int(tiempo_disponible.minutos_disponibles_miercoles) / 60)),
            'jueves': redondear_a_dos_decimales(redondear_a_cuartos(int(tiempo_disponible.minutos_disponibles_jueves) / 60)),
            'viernes': redondear_a_dos_decimales(redondear_a_cuartos(int(tiempo_disponible.minutos_disponibles_viernes) / 60)),
            'sabado': redondear_a_dos_decimales(redondear_a_cuartos(int(tiempo_disponible.minutos_disponibles_sabado) / 60)),
            'domingo': redondear_a_dos_decimales(redondear_a_cuartos(int(tiempo_disponible.minutos_disponibles_domingo) / 60))
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

    # Obtenemos las tareas del usuario
    tareas = session.query(TareasSemana).filter_by(id_usuario=id_usuario).order_by(TareasSemana.horario_inicio).all()

    # Organizamos las tareas por día
    tareas_por_dia = {
        'lunes': [],
        'martes': [],
        'miercoles': [],
        'jueves': [],
        'viernes': [],
        'sabado': [],
        'domingo': []
    }

    if tareas:
        for tarea in tareas:
            dia = tarea.dia_semana
            if dia in tareas_por_dia:
                tarea.tiempo = int(tarea.tiempo)
                tareas_por_dia[dia].append(tarea)

        # Calculamos la hora de la próxima alarma considerando que la actual ya pasó
        primera_tarea = tareas[0]
        hora_alarma = calcular_proxima_alarma(primera_tarea.dia_semana, primera_tarea.horario_inicio)
        contenido_tarea = primera_tarea.contenido_tarea
        tiempo_recordatorio = primera_tarea.tiempo_recordatorio if primera_tarea.switch_recordatorio else 0
        tarea_id = primera_tarea.id_tarea

        if primera_tarea and primera_tarea.switch_recordatorio:
            hora_recordatorio = hora_alarma - timedelta(minutes=primera_tarea.tiempo_recordatorio)
            proximoRecordatorio = hora_recordatorio.strftime('%Y-%m-%d %H:%M:%S')
        else:
            proximoRecordatorio = None

    else:
        hora_alarma = None
        contenido_tarea = None
        tiempo_recordatorio = 0
        proximoRecordatorio = None
        tarea_id = None

    # Renderizamos la página con la información
    return render_template('sitio/taskminder.html', tareas=tareas_por_dia, horas=horas,
                           horas_totales_disponibles=horas_totales_disponibles,
                           alarma_formateada=hora_alarma.strftime('%Y-%m-%d %H:%M:%S') if hora_alarma else None,
                           contenido_tarea=contenido_tarea, tiempo_recordatorio=tiempo_recordatorio,
                           proximoRecordatorio=proximoRecordatorio, tarea_id=tarea_id)

@app.route('/agregar_tarea', methods=['POST'])
@login_required
def agregar_tarea():
    try:
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()

        contenido_tarea = data.get('contenido_tarea')
        if contenido_tarea is None:
            return jsonify({"error": "Introduce el contenido de la tarea por favor"}), 400

        prioridad = int(data.get('prioridad'))
        dias_semana = data.get('dias_semana')
        if not dias_semana:
            return jsonify({"error": "Selecciona al menos un día de la semana"}), 400

        horario_inicio = data.get('horario_inicio')
        if horario_inicio is None:
            return jsonify({"error": "Introduce el horario por favor"}), 400

        horario_inicio = datetime.strptime(horario_inicio, '%H:%M').time()

        try:
            tiempo = int(data.get('tiempo', 0))
        except ValueError:
            return jsonify({"error": "Tiempo no es un número válido"}), 400

        switch_alarma = data.get('alarma') == True
        switch_recordatorio = data.get('recordatorio') == True
        tiempo_recordatorio = int(data.get('tiempo_recordatorio', 0)) if data.get('tiempo_recordatorio') else None

        estado = data.get('realizada_hoy') == True

        id_tarea = data.get("index")
        if id_tarea:
            session.query(TareasSemana).filter_by(id_tarea=id_tarea, id_usuario=current_user.id_usuario).delete()
            session.commit()

        tareas_creadas = []
        for dia in dias_semana:
            nueva_tarea = TareasSemana(
                contenido_tarea=contenido_tarea,
                prioridad=prioridad,
                dia_semana=dia,
                horario_inicio=horario_inicio,
                tiempo=tiempo,
                tiempo_original=tiempo,
                historial_tiempos=[tiempo],
                switch_alarma=switch_alarma,
                switch_recordatorio=switch_recordatorio,
                tiempo_recordatorio=tiempo_recordatorio,
                estado=estado,
                id_usuario=current_user.id_usuario
            )
            session.add(nueva_tarea)
            session.commit()

            # Actualiza el historial de otras tareas del mismo día
            otras_tareas = session.query(TareasSemana).filter_by(dia_semana=dia, id_usuario=current_user.id_usuario).filter(TareasSemana.id_tarea != nueva_tarea.id_tarea).all()
            for otra_tarea in otras_tareas:
                otra_tarea.historial_tiempos.append(otra_tarea.tiempo)
            session.commit()

            if switch_alarma:
                programar_alarma(nueva_tarea, switch_alarma, switch_recordatorio)

            if switch_recordatorio and tiempo_recordatorio:
                programar_recordatorio(nueva_tarea, switch_alarma, switch_recordatorio)

            # Ajustamos los tiempos para cada día
            ajustar_tiempos_tareas(dia, get_minutos_disponibles(dia))

            tareas_creadas.append(nueva_tarea)

        # Calculamos la próxima alarma basándonos en la primera tarea creada
        if tareas_creadas:
            proxima_alarma = calcular_proxima_alarma(tareas_creadas[0].dia_semana, tareas_creadas[0].horario_inicio)
        else:
            proxima_alarma = None

        flash('Tarea guardada con éxito', 'success')

    except Exception as e:
        session.rollback()
        app.logger.error(f"Error al agregar la tarea: {str(e)}")
        return jsonify({"error": "Error al agregar la tarea: " + str(e)}), 500

    if proxima_alarma:
        return jsonify({"success": True, "proxima_alarma": proxima_alarma.strftime('%Y-%m-%d %H:%M:%S')})
    else:
        return jsonify({"success": True})

@app.route('/posponer_alarma', methods=['POST'])
@login_required
def posponer_alarma():
    try:
        data = request.form
        id_tarea = int(data.get('id_tarea'))
        tiempo_posponer = int(data.get('tiempo_posponer', 0))  # Tiempo en minutos

        tarea = session.query(TareasSemana).filter_by(id_tarea=id_tarea, id_usuario=current_user.id_usuario).first()

        if not tarea:
            flash('Tarea no encontrada.', 'error')
            return jsonify({"error": "Tarea no encontrada"}), 404

        # Para posponer el horario de inicio de la tarea
        nuevo_horario_inicio = (datetime.combine(datetime.today(), tarea.horario_inicio) + timedelta(minutes=tiempo_posponer)).time()
        tarea.horario_inicio = nuevo_horario_inicio

        session.commit()

        # Recalculamos tiempos de todas las tareas
        tareas = session.query(TareasSemana).filter_by(id_usuario=current_user.id_usuario).order_by(TareasSemana.horario_inicio).all()
        tiempo_disponible = session.query(TiempoDisponible).filter_by(id_usuario=current_user.id_usuario).first().horas_totales_disponibles * 60  # Convertimos a minutos
        reestructurar_tareas(tareas, tiempo_disponible)

        flash('Tarea pospuesta ' + str(tiempo_posponer) + ' minutos.', 'success')
        return jsonify({"success": True}), 200
    except Exception as e:
        flash('Error al posponer la tarea: ' + str(e), 'error')
        return jsonify({"error": "Error interno del servidor: " + str(e)}), 500

@app.route('/configurar_alarma', methods=['POST'])
@login_required
def configurar_alarma():
    index = int(request.form.get('index'))
    tarea = session.query(TareasSemana).filter_by(id_tarea=index, id_usuario=current_user.id_usuario).first()

    if not tarea:
        flash('Tarea no encontrada', 'error')
        return redirect(url_for('taskminder'))

    hora_alarma = datetime.combine(datetime.today(), tarea.horario_inicio)
    tiempo_recordatorio = tarea.tiempo_recordatorio

    app.logger.info("Programando alarma para %s a las %s", tarea.contenido_tarea, hora_alarma)

    job_alarma = scheduler.add_job(alarma, 'date', run_date=hora_alarma, args=[tarea])
    app.logger.info("Alarma programada con ID: %s", job_alarma.id)

    if tiempo_recordatorio:
        hora_recordatorio = hora_alarma - timedelta(minutes=tiempo_recordatorio)
        app.logger.info("Programando recordatorio para %s a las %s", tarea.contenido_tarea, hora_recordatorio)
        job_recordatorio = scheduler.add_job(recordatorio, 'date', run_date=hora_recordatorio, args=[tarea])
        app.logger.info("Recordatorio programado con ID: %s", job_recordatorio.id)

    flash('Alarma configurada con éxito para la tarea.')
    return redirect(url_for('taskminder'))

@app.route('/borrar_tarea', methods=['POST'])
@login_required
def borrar_tarea():
    data = request.get_json() if request.is_json else request.form.to_dict()

    try:
        tarea_id = int(data['id_tarea'])
        tarea = session.query(TareasSemana).filter_by(id_tarea=tarea_id, id_usuario=current_user.id_usuario).first()

        if tarea:
            dia_semana = tarea.dia_semana

            # Obtenemos todas las tareas del día antes de borrar
            tareas_del_dia = session.query(TareasSemana).filter_by(dia_semana=dia_semana, id_usuario=current_user.id_usuario).all()

            # Borrar la tarea
            session.delete(tarea)
            session.commit()

            # Restaura los tiempos de las tareas restantes
            tareas_restantes = [t for t in tareas_del_dia if t.id_tarea != tarea_id]

            if len(tareas_restantes) == len(tareas_del_dia) - 1:
                for t in tareas_restantes:
                    if len(t.historial_tiempos) > 1:
                        t.tiempo = t.historial_tiempos[-2]  # Vuelve al tiempo anterior
                        t.historial_tiempos = t.historial_tiempos[:-1]  # Elimina el último tiempo del historial
                    else:
                        t.tiempo = t.tiempo_original

            session.commit()

            # Reajustamos tiempos si es necesario
            minutos_disponibles = get_minutos_disponibles(dia_semana)
            if sum(t.tiempo for t in tareas_restantes) > minutos_disponibles:
                ajustar_tiempos_tareas(dia_semana, minutos_disponibles)

            return jsonify({'success': True}), 200
        else:
            return jsonify({'error': 'Tarea no encontrada'}), 404
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/modificar_tarea/<int:index>', methods=['GET', 'POST'])
@login_required
def modificar_tarea(index):
    tarea = session.query(TareasSemana).filter_by(id_tarea=index, id_usuario=current_user.id_usuario).first()

    # Verificamos que la tarea pertenece al usuario actual
    if not tarea:
        flash('Tarea no encontrada o no tienes permisos para modificarla.')
        return redirect(url_for('taskminder'))

    if request.method == 'POST':
        tarea.contenido_tarea = request.form.get('contenido_tarea')
        try:
            tarea.prioridad = int(request.form.get('prioridad'))
            tarea.tiempo = int(request.form.get('tiempo'))
        except ValueError:
            flash('Por favor, introduce valores válidos para prioridad y tiempo.')
            return redirect(url_for('taskminder', id_tarea=index))
        session.commit()
        flash('Tarea modificada con éxito')
        return redirect(url_for('taskminder'))

    return render_template('modificar_tarea.html', tarea=tarea, id_tarea=index)

@app.route('/eliminar_tarea/<int:index>', methods=['POST'])
@login_required
def eliminar_tarea(index):
    logging.info(f"Iniciando eliminación de tarea con ID: {index}")
    tarea = session.query(TareasSemana).filter_by(id_tarea=index, id_usuario=current_user.id_usuario).first()
    if not tarea:
        logging.warning(f"Tarea con ID {index} no encontrada")
        flash('Tarea no encontrada')
        return redirect(url_for('taskminder'))

    dia_semana = tarea.dia_semana
    logging.info(f"Tarea encontrada. Día de la semana: {dia_semana}")

    # Obtenemos todas las tareas del día antes de eliminar
    tareas_del_dia = session.query(TareasSemana).filter_by(dia_semana=dia_semana, id_usuario=current_user.id_usuario).all()
    logging.info(f"Número de tareas en el día antes de eliminar: {len(tareas_del_dia)}")

    session.delete(tarea)
    session.commit()
    logging.info(f"Tarea con ID {index} eliminada")

    # Restauramos tiempos de las tareas restantes
    tareas_restantes = session.query(TareasSemana).filter_by(dia_semana=dia_semana, id_usuario=current_user.id_usuario).all()
    logging.info(f"Número de tareas restantes: {len(tareas_restantes)}")

    for t in tareas_restantes:
        logging.info(f"Procesando tarea restante ID {t.id_tarea}")
        logging.info(f"Historial de tiempos actual: {t.historial_tiempos}")
        if len(t.historial_tiempos) > 1:
            t.tiempo = t.historial_tiempos[-2]  # Volver al tiempo anterior
            t.historial_tiempos.pop()  # Eliminar el último tiempo del historial
            logging.info(f"Restaurando tiempo anterior: {t.tiempo}")
            logging.info(f"Nuevo historial de tiempos: {t.historial_tiempos}")
        else:
            t.tiempo = t.tiempo_original
            logging.info(f"Restaurando tiempo original: {t.tiempo}")

    session.commit()
    logging.info("Cambios guardados en la base de datos")

    # Reajustamos tiempos si es necesario
    minutos_disponibles = get_minutos_disponibles(dia_semana)
    logging.info(f"Minutos disponibles para el día {dia_semana}: {minutos_disponibles}")
    if sum(t.tiempo for t in tareas_restantes) > minutos_disponibles:
        logging.info("Se requiere reajuste de tiempos")
        ajustar_tiempos_tareas(dia_semana, minutos_disponibles)
    else:
        logging.info("No se requiere reajuste de tiempos")

    flash('Tarea eliminada con éxito.')
    return redirect(url_for('taskminder'))

@app.route('/actualizar_tarea', methods=['POST'])
@login_required
def actualizar_tarea():
    data = request.json
    id_tarea = data.get('id_tarea')
    estado = data.get('estado')

    app.logger.info(f"Actualizando tarea: id={id_tarea}, estado={estado}")

    tarea = session.query(TareasSemana).filter_by(id_tarea=id_tarea, id_usuario=current_user.id_usuario).first()

    if tarea:
        tarea.estado = estado
        try:
            session.commit()
            app.logger.info(f"Tarea actualizada correctamente: id={id_tarea}")
            return jsonify({"success": True}), 200
        except Exception as e:
            session.rollback()
            app.logger.error(f"Error al actualizar tarea: {str(e)}")
            return jsonify({"error": "Error al actualizar la tarea en la base de datos"}), 500
    else:
        app.logger.error(f"Tarea no encontrada: id={id_tarea}")
        return jsonify({"error": "Tarea no encontrada"}), 404

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

# Control tiempo y horarios:
@app.route('/reemplazar_tiempo_disponible', methods=['POST'])
@login_required
def reemplazar_tiempo_disponible():
    data = request.get_json()

    replace_data = {
        'id': data.get('id', None),
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

    tiempo_disponible.actualizar_horas_totales()

    session.add(tiempo_disponible)
    session.commit()

    return redirect(url_for('taskminder'))

@app.route("/horas_disponibles", methods=["GET", "POST"])
@login_required
def horas_disponibles():
    if request.method == "POST":
        minutos_disponibles_por_dia = {
            'lunes': int(request.form.get("lunes", 0)),
            'martes': int(request.form.get("martes", 0)),
            'miercoles': int(request.form.get("miercoles", 0)),
            'jueves': int(request.form.get("jueves", 0)),
            'viernes': int(request.form.get("viernes", 0)),
            'sabado': int(request.form.get("sabado", 0)),
            'domingo': int(request.form.get("domingo", 0))
        }

        if any(tiempo < 0 for tiempo in minutos_disponibles_por_dia.values()):
            flash('Por favor, introduce valores válidos para las horas disponibles.')
            return redirect(url_for("horas_disponibles"))

        tiempo_disponible_obj = session.query(TiempoDisponible).filter_by(id_usuario=current_user.id_usuario).first()
        if tiempo_disponible_obj:
            tiempo_disponible_obj.minutos_disponibles_lunes = minutos_disponibles_por_dia['lunes']
            tiempo_disponible_obj.minutos_disponibles_martes = minutos_disponibles_por_dia['martes']
            tiempo_disponible_obj.minutos_disponibles_miercoles = minutos_disponibles_por_dia['miercoles']
            tiempo_disponible_obj.minutos_disponibles_jueves = minutos_disponibles_por_dia['jueves']
            tiempo_disponible_obj.minutos_disponibles_viernes = minutos_disponibles_por_dia['viernes']
            tiempo_disponible_obj.minutos_disponibles_sabado = minutos_disponibles_por_dia['sabado']
            tiempo_disponible_obj.minutos_disponibles_domingo = minutos_disponibles_por_dia['domingo']
        else:
            tiempo_disponible_obj = TiempoDisponible(
                id_usuario=current_user.id_usuario,
                minutos_disponibles_lunes=minutos_disponibles_por_dia['lunes'],
                minutos_disponibles_martes=minutos_disponibles_por_dia['martes'],
                minutos_disponibles_miercoles=minutos_disponibles_por_dia['miercoles'],
                minutos_disponibles_jueves=minutos_disponibles_por_dia['jueves'],
                minutos_disponibles_viernes=minutos_disponibles_por_dia['viernes'],
                minutos_disponibles_sabado=minutos_disponibles_por_dia['sabado'],
                minutos_disponibles_domingo=minutos_disponibles_por_dia['domingo']
            )
            session.add(tiempo_disponible_obj)
        session.commit()

        flash("Horas disponibles actualizadas con éxito.")
        return redirect(url_for("taskminder"))

    tiempo_disponible_obj = session.query(TiempoDisponible).filter_by(id_usuario=current_user.id_usuario).first()
    horas_disponibles_dias = {
        'lunes': tiempo_disponible_obj.minutos_disponibles_lunes if tiempo_disponible_obj else 0,
        'martes': tiempo_disponible_obj.minutos_disponibles_martes if tiempo_disponible_obj else 0,
        'miercoles': tiempo_disponible_obj.minutos_disponibles_miercoles if tiempo_disponible_obj else 0,
        'jueves': tiempo_disponible_obj.minutos_disponibles_jueves if tiempo_disponible_obj else 0,
        'viernes': tiempo_disponible_obj.minutos_disponibles_viernes if tiempo_disponible_obj else 0,
        'sabado': tiempo_disponible_obj.minutos_disponibles_sabado if tiempo_disponible_obj else 0,
        'domingo': tiempo_disponible_obj.minutos_disponibles_domingo if tiempo_disponible_obj else 0
    }
    return render_template('sitio/horas_disponibles.html', horas_disponibles=horas_disponibles_dias)

def calcular_proxima_alarma(dia_semana, hora):

    # Aseguramos que la variable 'hora' es de tipo datetime.time
    if isinstance(hora, str):
        hora = datetime.strptime(hora, '%H:%M').time()

    dias = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
    hoy = datetime.now()
    dia_actual = hoy.weekday()
    dias_hasta_alarma = dias.index(dia_semana) - dia_actual

    # Si el día de la alarma es hoy y la hora ya pasó, programar para la próxima semana
    if dias_hasta_alarma == 0 and hora <= hoy.time():
        dias_hasta_alarma += 7
    elif dias_hasta_alarma < 0:
        # Si la alarma es para un día que ya pasó en la semana, mover a la próxima semana
        dias_hasta_alarma += 7

    proxima_fecha = hoy.date() + timedelta(days=dias_hasta_alarma)
    return datetime.combine(proxima_fecha, hora)

# Alarmas y recordatorios
@app.route('/alarma')
def alarma(tarea):
    print("Alarma para la tarea: " + tarea.contenido_tarea)
    mixer.init()
    sound_path = os.path.join(base_dir, 'static', 'alarma_taskminder.mp3')
    if os.path.exists(sound_path):
        try:
            mixer.music.load(sound_path)
            mixer.music.play()
            print("Alarma sonando...")
        except Exception as e:
            print("Error al reproducir el sonido: " + str(e))
    else:
        print("Archivo de sonido no encontrado: " + sound_path)

    return redirect(url_for('taskminder'))

def recordatorio(tarea):
    print("Ejecutando recordatorio para la tarea: " + tarea.contenido_tarea)

    # Verificamos si el archivo de sonido es accesible
    sound_path = os.path.join(base_dir, 'static', 'recordatorio_taskminder.mp3')
    if os.path.exists(sound_path):
        try:
            mixer.init()
            mixer.music.load(sound_path)
            mixer.music.set_volume(1.0)  # Asegura que el volumen está al 100%
            mixer.music.play()
            print("Reproduciendo sonido de recordatorio...")
        except Exception as e:
            print("Error al reproducir el sonido: " + str(e))
    else:
        print("Archivo de sonido no encontrado en la ruta: " + sound_path)

def programar_alarma(tarea, switch_alarma, switch_recordatorio):
    hora_alarma = datetime.combine(datetime.now().date(), tarea.horario_inicio)
    if switch_alarma == 1 and switch_recordatorio == 1:
        scheduler.add_job(alarma, 'date', run_date=hora_alarma, args=[tarea])
        scheduler.add_job(recordatorio, 'date', run_date=hora_alarma - timedelta(minutes=tarea.tiempo_recordatorio), args=[tarea])
    elif switch_alarma == 1 and switch_recordatorio == 0:
        scheduler.add_job(alarma, 'date', run_date=hora_alarma, args=[tarea])
    elif switch_alarma == 0 and switch_recordatorio == 1:
        scheduler.add_job(recordatorio, 'date', run_date=hora_alarma - timedelta(minutes=tarea.tiempo_recordatorio), args=[tarea])

def programar_recordatorio(tarea, switch_alarma, switch_recordatorio):
    hora_recordatorio = datetime.combine(datetime.now().date(), tarea.horario_inicio) - timedelta(minutes=tarea.tiempo_recordatorio)
    if switch_alarma == 1 and switch_recordatorio == 1:
        scheduler.add_job(alarma, 'date', run_date=hora_recordatorio + timedelta(minutes=tarea.tiempo_recordatorio), args=[tarea])
        scheduler.add_job(recordatorio, 'date', run_date=hora_recordatorio, args=[tarea])
    elif switch_alarma == 1 and switch_recordatorio == 0:
        scheduler.add_job(alarma, 'date', run_date=hora_recordatorio + timedelta(minutes=tarea.tiempo_recordatorio), args=[tarea])
    elif switch_alarma == 0 and switch_recordatorio == 1:
        scheduler.add_job(recordatorio, 'date', run_date=hora_recordatorio, args=[tarea])

    print("Programando recordatorio para la tarea " + tarea.contenido_tarea + " a las " + str(hora_recordatorio))
    scheduler.add_job(recordatorio, 'date', run_date=hora_recordatorio, args=[tarea])

# Funciones auxiliares:
def get_minutos_disponibles(dia):
    tiempo_disponible = session.query(TiempoDisponible).filter_by(id_usuario=current_user.id_usuario).first()
    if tiempo_disponible:
        return getattr(tiempo_disponible, "minutos_disponibles_" + dia)
    return 0

#  Esta función recalcula los tiempos de las tareas teniendo en cuenta las prioridades y asegura que el tiempo total de las tareas no exceda el tiempo disponible.
def ajustar_tiempos_tareas(dia, minutos_disponibles_dia):
    logging.info(f"Iniciando ajuste de tiempos para el día {dia}. Minutos disponibles: {minutos_disponibles_dia}")

    tareas = session.query(TareasSemana).filter_by(dia_semana=dia, id_usuario=current_user.id_usuario).order_by(TareasSemana.prioridad.desc()).all()
    logging.info(f"Tareas encontradas: {len(tareas)}")

    tiempo_total_original = sum(tarea.tiempo_original for tarea in tareas)
    logging.info(f"Tiempo total original: {tiempo_total_original}")

    if tiempo_total_original <= minutos_disponibles_dia:
        logging.info("No se requiere ajuste, el tiempo total es menor o igual al disponible")
        for tarea in tareas:
            if tarea.tiempo != tarea.tiempo_original:
                logging.info(f"Restaurando tiempo original para tarea {tarea.id_tarea}: {tarea.tiempo} -> {tarea.tiempo_original}")
                tarea.tiempo = tarea.tiempo_original
                if tarea.tiempo not in tarea.historial_tiempos:
                    tarea.historial_tiempos.append(tarea.tiempo)
                    logging.info(f"Actualizado historial_tiempos para tarea {tarea.id_tarea}: {tarea.historial_tiempos}")
        session.commit()
        logging.info("Cambios guardados en la base de datos")
        return True

    factor_ajuste = minutos_disponibles_dia / tiempo_total_original
    logging.info(f"Factor de ajuste calculado: {factor_ajuste}")

    tiempo_ajustado_total = 0

    for tarea in tareas:
        tiempo_ajustado = round(tarea.tiempo_original * factor_ajuste)
        tiempo_ajustado = max(tiempo_ajustado, round(tarea.tiempo_original * 0.5))  # No reducir más del 50% el tiempo de las tareas
        logging.info(f"Ajustando tarea {tarea.id_tarea}: {tarea.tiempo} -> {tiempo_ajustado}")

        if tarea.tiempo != tiempo_ajustado:
            tarea.tiempo = tiempo_ajustado
            if tiempo_ajustado not in tarea.historial_tiempos:
                tarea.historial_tiempos.append(tiempo_ajustado)
                logging.info(f"Actualizado historial_tiempos para tarea {tarea.id_tarea}: {tarea.historial_tiempos}")
        tiempo_ajustado_total += tiempo_ajustado

    # Distribuye el tiempo restante (si lo hay) a las tareas de mayor prioridad
    tiempo_restante = minutos_disponibles_dia - tiempo_ajustado_total
    logging.info(f"Tiempo restante después del ajuste inicial: {tiempo_restante}")

    for tarea in tareas:
        if tiempo_restante <= 0:
            break
        aumento = min(tiempo_restante, tarea.tiempo_original - tarea.tiempo)
        if aumento > 0:
            logging.info(f"Aumentando tiempo de tarea {tarea.id_tarea} en {aumento} minutos")
            tarea.tiempo += aumento
            if tarea.tiempo not in tarea.historial_tiempos:
                tarea.historial_tiempos.append(tarea.tiempo)
                logging.info(f"Actualizado historial_tiempos para tarea {tarea.id_tarea}: {tarea.historial_tiempos}")
        tiempo_restante -= aumento

    try:
        session.commit()
        logging.info("Cambios guardados en la base de datos")
    except Exception as e:
        logging.error(f"Error al guardar cambios en la base de datos: {str(e)}")
        session.rollback()
        raise

    logging.info("Ajuste de tiempos completado")
    return True

# Esta función se encarga de ajustar los tiempos de las tareas siguientes y reducirlas proporcionalmente según su importancia
def reestructurar_tareas(tareas, total_horas_disponibles):
    reduccion_por_prioridad = {
        3: 0.05, # Prioridad máxima
        2: 0.1,  # Prioridad importante
        1: 0.2,  # Prioridad moderada
        0: 0.3   # Prioridad menor
    }

    tiempos_ajustados_iniciales = []
    total_reduccion = 0

    for tarea in tareas:
        prioridad = tarea.prioridad
        tiempo_inicial = tarea.tiempo
        porcentaje_reduccion = reduccion_por_prioridad.get(prioridad, 0.4)
        tiempo_ajustado = tiempo_inicial * (1 - porcentaje_reduccion)
        tiempos_ajustados_iniciales.append(tiempo_ajustado)
        total_reduccion += porcentaje_reduccion

    tiempo_total_ajustado_inicial = sum(tiempos_ajustados_iniciales)
    diferencia_tiempo = total_horas_disponibles - tiempo_total_ajustado_inicial

    tiempos_finales = []
    if diferencia_tiempo > 0:
        for tarea, tiempo_ajustado in zip(tareas, tiempos_ajustados_iniciales):
            proporcion_redistribucion = reduccion_por_prioridad.get(tarea.prioridad, 0.4) / total_reduccion
            tiempo_final = tiempo_ajustado + (proporcion_redistribucion * diferencia_tiempo)
            tiempos_finales.append(tiempo_final)
    else:
        tiempos_finales = tiempos_ajustados_iniciales

    for tarea, tiempo_final in zip(tareas, tiempos_finales):
        # Aseguramos que el tiempo final no sea negativo y no reducimos más del 50%
        tiempo_final = max(tiempo_final, 0)
        tarea.tiempo = max(tiempo_final, tarea.tiempo * 0.5)
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
            horario_inicio = datetime.strptime(tarea.horario_inicio.strftime('%H:%M:%S'), '%H:%M:%S').time()
            if horario_inicio <= tiempo_actual < (datetime.combine(datetime.today(), horario_inicio) + timedelta(minutes=tarea.tiempo)).time():
                usuario.ultima_actividad = tarea.contenido_tarea
                session.commit()
                break

scheduler.add_job(verificar_cambio_actividad, 'interval', minutes=1)


@app.route('/ver_horario')
@login_required
def ver_horario():
    tareas = session.query(TareasSemana).filter_by(id_usuario=current_user.id_usuario).all()
    tiempo_disponible_obj = session.query(TiempoDisponible).filter_by(id_usuario=current_user.id_usuario).first()
    tiempo_disponible = tiempo_disponible_obj.horas_totales_disponibles if tiempo_disponible_obj else 0

    recalcular_horas(tareas, tiempo_disponible)

    return render_template('ver_horario.html', horas=tiempo_disponible, tareas=tareas)


# Para errores:
@app.errorhandler(404)
def pagina_no_encontrada():
    return render_template('404.html'), 404



if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
