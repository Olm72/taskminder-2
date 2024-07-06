from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import TareasSemana, Usuario, MensajesCliente, OpinionesCliente, TiempoDisponible
from apscheduler.schedulers.background import BackgroundScheduler
import db
from db import session
import logging
from datetime import datetime, timedelta
from tzlocal import get_localzone
import pytz

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

# Función para codificar la clave secreta personalizada
def get_secret_key():
    return app.config['SECRET_KEY'].encode()

# Función que se ejecuta antes de cada solicitud para almacenar las cookies.
@app.before_request
def before_request_logging():
    logging.debug('Cookies: ' + str(request.cookies))

# Rutas para las páginas principales de la web
# Ruta que renderiza la página de inicio
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

# Ruta para que el usuario envie opiniones: recibe datos del formulario y guarda una nueva opinión en la BBDD
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

# Ruta para renderizar premium html
@app.route("/premium")
def premium():
    return render_template('sitio/premium.html')

# Rutas para contacto que permiten a los usuarios enviar mensajes
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


# Ruta para renderizar términos y condiciones
@app.route("/terminos_condiciones")
def terminos_condiciones():
    return render_template('sitio/terminos_condiciones.html')

# Rutas para temas de iniciar sesión y cerrar sesión y que el usuario pueda comprobar si está conectado
# Ruta para inicio de sesión
@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        password = request.form.get('password')
        recordarme = request.form.get('recordarme')
        usuario_obj = session.query(Usuario).filter_by(nombre=usuario).first()
        if usuario_obj and usuario_obj.check_password(password):
            if usuario_obj.activo:
                # Convertir recordarme a un valor booleano
                recordarme_bool = True if recordarme else False
                login_user(usuario_obj, remember=recordarme_bool)
                if current_user.is_authenticated:
                    return render_template('sitio/conectado.html')

            else:
                flash('Tu cuenta está inactiva. Contacta al administrador.', 'error')
                return render_template('sitio/login.html')
        else:
            flash('Credenciales inválidas', 'error')
            return render_template('sitio/login.html')

    if current_user.is_authenticated:
        return render_template('sitio/conectado.html')
    return render_template('sitio/login.html')

# Ruta para cerrar sesión
@app.route("/logout")
@login_required
def logout():
    logout_user()

    flash('Has cerrado sesión correctamente')
    return redirect(url_for('login'))

# Función para cargar usuario
@login_manager.user_loader
def cargar_usuario(id_usuario):
    return session.get(Usuario, int(id_usuario))

# Función con la que el usuario puede comprobar que está conectado.
@app.route("/confirmacion-registro-html")
def confirmacion_registro_html():
    return render_template('sitio/confirmacion_registro.html')

@app.route("/confirmacion-registro", methods=['GET', 'POST'])
def confirmacion_registro():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        email = request.form.get('email')
        password = request.form.get('password')
        print("Intentando registrar nuevo usuario: " + usuario)  # Print de depuración

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

        nuevo_usuario = Usuario(nombre=usuario, email=email, password=password)
        nuevo_usuario.activo = True
        session.add(nuevo_usuario)
        session.commit()

        print("Usuario " + usuario + " registrado correctamente")  # Agrego un print de depuración

        flash('¡Enhorabuena, te has registrado con éxito! Ya puedes iniciar sesión.')

        return redirect(url_for('confirmacion_registro_html'))
    return render_template('sitio/registrate.html')

@app.route('/taskminder', methods=['GET', 'POST'])
@login_required
def taskminder():
    id_usuario = current_user.id_usuario

    # Obtener el tiempo disponible para cada día de la semana de la base de datos
    tiempo_disponible = session.query(TiempoDisponible).filter_by(id_usuario=id_usuario).first()

    if tiempo_disponible:
        horas = {
            'Lunes': tiempo_disponible.horas_disponibles_lunes,
            'Martes': tiempo_disponible.horas_disponibles_martes,
            'Miércoles': tiempo_disponible.horas_disponibles_miercoles,
            'Jueves': tiempo_disponible.horas_disponibles_jueves,
            'Viernes': tiempo_disponible.horas_disponibles_viernes,
            'Sábado': tiempo_disponible.horas_disponibles_sabado,
            'Domingo': tiempo_disponible.horas_disponibles_domingo
        }
    else:
        horas = {
            'Lunes': 0,
            'Martes': 0,
            'Miércoles': 0,
            'Jueves': 0,
            'Viernes': 0,
            'Sábado': 0,
            'Domingo': 0
        }

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'agregar':
            contenido = request.form.get('contenido')
            try:
                prioridad = int(request.form.get('prioridad'))
                tiempo = int(request.form.get('tiempo'))
            except ValueError:
                flash('Por favor, introduce valores numéricos válidos para prioridad y tiempo.')
                return redirect(url_for('taskminder'))

            nueva_tarea = TareasSemana(
                contenido=contenido,
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
            db.session.add(nueva_tarea)
            db.session.commit()
            flash('Tarea agregada con éxito')

        elif action.startswith('modificar'):
            index = int(action.split('-')[1])
            tarea = TareasSemana.query.filter_by(id_tarea=index, id_usuario=id_usuario).first()
            if tarea:
                tarea.contenido = request.form.get('contenido')
                try:
                    tarea.prioridad = int(request.form.get('prioridad'))
                    tarea.tiempo = int(request.form.get('tiempo'))
                except ValueError:
                    flash('Por favor, introduce valores numéricos válidos para prioridad y tiempo.')
                    return redirect(url_for('taskminder'))
                db.session.commit()
                flash('Tarea modificada con éxito')
            else:
                flash('Tarea no encontrada')

        elif action.startswith('eliminar'):
            index = int(action.split('-')[1])
            tarea = TareasSemana.query.filter_by(id_tarea=index, id_usuario=id_usuario).first()
            if tarea:
                db.session.delete(tarea)
                db.session.commit()
                flash('Tarea eliminada con éxito')
            else:
                flash('Tarea no encontrada')

    tareas = TareasSemana.query.filter_by(id_usuario=id_usuario).all()

    return render_template('sitio/taskminder.html', tareas=tareas)

# Función auxiliar para calcular los tiempos restantes de las tareas
def calcular_tiempos_restantes(tareas_a_realizar_taskminder, tiempo_disponible):
    # Aquí puedes implementar la lógica que necesitas para calcular los tiempos restantes.
    # Por ahora, vamos a devolver los tiempos restantes igual a los tiempos actuales de las tareas.
    tiempos_restantes = {}
    for tarea in tareas_a_realizar:
        tiempos_restantes[tarea.id_tarea] = tarea.tiempo
    return tiempos_restantes

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
            tiempo_disponible_obj.horas_disponibles = horas
        else:
            tiempo_disponible_obj = TiempoDisponible(id_usuario=current_user.id_usuario, horas_disponibles=horas)
            session.add(tiempo_disponible_obj)
        session.commit()

        flash("Horas disponibles actualizadas con éxito.")
        return redirect(url_for("taskminder"))

    tiempo_disponible_obj = session.query(TiempoDisponible).filter_by(id_usuario=current_user.id_usuario).first()
    horas_disponibles_ = tiempo_disponible_obj.horas_disponibles if tiempo_disponible_obj else 0
    return render_template('sitio/horas_disponibles.html', horas_disponibles=horas_disponibles_)

# Propuesto por Jorge, profesor
# Consulta actualizada de las tareas realizadas
tareas_realizadas = session.query(TareasSemana).filter_by(estado=True).all()

# Formulario para ingresar horas disponibles
@app.route('/configurar_horas', methods=['GET', 'POST'])
@login_required
def configurar_horas():
    if request.method == 'POST':
        horas_disponibles_dias_semana = {
            'horas_disponibles_lunes': request.form.get('Lunes'),
            'horas_disponibles_martes': request.form.get('Martes'),
            'horas_disponibles_miercoles': request.form.get('Miércoles'),
            'horas_disponibles_jueves': request.form.get('Jueves'),
            'horas_disponibles_viernes': request.form.get('Viernes'),
            'horas_disponibles_sabado': request.form.get('Sábado'),
            'horas_disponibles_domingo': request.form.get('Domingo')
        }

        for dia, horas in horas_disponibles_dias_semana.items():
            if not horas:
                flash('Por favor, introduce un valor válido para las horas disponibles.')
                return redirect(url_for("configurar_horas"))
            try:
                horas_disponibles_dias_semana[dia] = int(horas)
            except ValueError:
                flash('Por favor, introduce un valor numérico para las horas disponibles.')
                return redirect(url_for("configurar_horas"))

        tiempo_disponible_obj = session.query(TiempoDisponible).filter_by(id_usuario=current_user.id_usuario).first()
        if tiempo_disponible_obj:
            tiempo_disponible_obj.horas_disponibles_lunes = horas_disponibles_dias_semana['horas_disponibles_lunes']
            tiempo_disponible_obj.horas_disponibles_martes = horas_disponibles_dias_semana['horas_disponibles_martes']
            tiempo_disponible_obj.horas_disponibles_miercoles = horas_disponibles_dias_semana['horas_disponibles_miercoles']
            tiempo_disponible_obj.horas_disponibles_jueves = horas_disponibles_dias_semana['horas_disponibles_jueves']
            tiempo_disponible_obj.horas_disponibles_viernes = horas_disponibles_dias_semana['horas_disponibles_viernes']
            tiempo_disponible_obj.horas_disponibles_sabado = horas_disponibles_dias_semana['horas_disponibles_sabado']
            tiempo_disponible_obj.horas_disponibles_domingo = horas_disponibles_dias_semana['horas_disponibles_domingo']

        else:
            tiempo_disponible_obj = TiempoDisponible(
                id_usuario=current_user.id_usuario,
                horas_disponibles_lunes=horas_disponibles_dias_semana['horas_disponibles_lunes'],
                horas_disponibles_martes=horas_disponibles_dias_semana['horas_disponibles_martes'],
                horas_disponibles_miercoles=horas_disponibles_dias_semana['horas_disponibles_miercoles'],
                horas_disponibles_jueves=horas_disponibles_dias_semana['horas_disponibles_jueves'],
                horas_disponibles_viernes=horas_disponibles_dias_semana['horas_disponibles_viernes'],
                horas_disponibles_sabado=horas_disponibles_dias_semana['horas_disponibles_sabado'],
                horas_disponibles_domingo=horas_disponibles_dias_semana['horas_disponibles_domingo'],
            )
            session.add(tiempo_disponible_obj)

        session.commit()
        flash('Horas disponibles configuradas con éxito.')
        return redirect(url_for("taskminder"))

    tiempo_disponible_obj = session.query(TiempoDisponible).filter_by(id_usuario=current_user.id_usuario).first()
    if tiempo_disponible_obj:
        horas_disponibles_dias_semana = {
            'Lunes': tiempo_disponible_obj.horas_disponibles_lunes,
            'Martes': tiempo_disponible_obj.horas_disponibles_martes,
            'Miércoles': tiempo_disponible_obj.horas_disponibles_miercoles,
            'Jueves': tiempo_disponible_obj.horas_disponibles_jueves,
            'Viernes': tiempo_disponible_obj.horas_disponibles_viernes,
            'Sábado': tiempo_disponible_obj.horas_disponibles_sabado,
            'Domingo': tiempo_disponible_obj.horas_disponibles_domingo
        }
    else:
        horas_disponibles_dias_semana = {dia: 0 for dia in ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']}

    return render_template("sitio/configurar_horas.html", horas=horas_disponibles_dias_semana)

# Ver las horas disponibles
@app.route('/ver_horas')
def ver_horas():
    return render_template('ver_horas.html', horas=horas_disponibles)

# Lista de tareas
tareas_a_realizar = []

@app.route('/agregar_tarea', methods=['GET', 'POST'])
def agregar_tarea():
    if request.method == 'POST':
        contenido = request.form.get('contenido')
        try:
            prioridad = int(request.form.get('prioridad'))
            tiempo = int(request.form.get('tiempo'))
        except ValueError:
            flash('Por favor, introduce valores numéricos válidos para prioridad y tiempo.')
            return redirect(url_for('agregar_tarea'))

        nueva_tarea = {'contenido': contenido, 'prioridad': prioridad, 'tiempo': tiempo}
        tareas_a_realizar.append(nueva_tarea)
        flash('Tarea agregada con éxito')
        return redirect(url_for('ver_tareas'))

    return render_template('agregar_tarea.html')


@app.route('/modificar_tarea/<int:index>', methods=['GET', 'POST'])
def modificar_tarea(index):
    if index < 0 or index >= len(tareas_a_realizar):
        flash('Índice de tarea no válido')
        return redirect(url_for('ver_tareas'))

    if request.method == 'POST':
        contenido = request.form.get('contenido')
        try:
            prioridad = int(request.form.get('prioridad'))
            tiempo = int(request.form.get('tiempo'))
        except ValueError:
            flash('Por favor, introduce valores numéricos válidos para prioridad y tiempo.')
            return redirect(url_for('modificar_tarea', index=index))

        tareas_a_realizar[index]['contenido'] = contenido
        tareas_a_realizar[index]['prioridad'] = prioridad
        tareas_a_realizar[index]['tiempo'] = tiempo

        flash('Tarea modificada con éxito')
        return redirect(url_for('ver_tareas'))

    return render_template('modificar_tarea.html', tarea=tareas_a_realizar[index], index=index)

@app.route('/eliminar_tarea/<int:index>', methods=['POST'])
def eliminar_tarea(index):
    tareas_a_realizar.pop(index)
    return redirect(url_for('ver_tareas'))

def recalcular_horas(tareas_a_realizar, tiempo_disponible):
    # Porcentajes de reducción según la prioridad (estos son ejemplos, puedes ajustarlos)
    reduccion_por_prioridad = {
        3: 0.1,  # Máxima prioridad
        2: 0.2,  # Importante
        1: 0.3,  # Moderada
        0: 0.4   # Menor
    }

    # Lista para almacenar los nuevos tiempos
    nuevos_tiempos = []

    for tarea in tareas_a_realizar:
        prioridad = tarea.prioridad
        tiempo_inicial = tarea.tiempo
        if prioridad in reduccion_por_prioridad:
            porcentaje_reduccion = reduccion_por_prioridad[prioridad]
            nuevo_tiempo = tiempo_inicial * (1 - porcentaje_reduccion * prioridad)
            # Asegurarse de que el nuevo tiempo no sea negativo
            nuevo_tiempo = max(nuevo_tiempo, 0)
            nuevos_tiempos.append(nuevo_tiempo)
        else:
            nuevos_tiempos.append(tiempo_inicial)

    tiempo_total_asignado = sum(nuevos_tiempos)

    # Asegurarse de que el tiempo total asignado no exceda el tiempo disponible
    if tiempo_total_asignado > tiempo_disponible:
        # Si excede, ajustar los tiempos proporcionalmente
        factor_ajuste = tiempo_disponible / tiempo_total_asignado
        nuevos_tiempos = [tiempo * factor_ajuste for tiempo in nuevos_tiempos]

    # Actualizar los tiempos de las tareas en la base de datos
    for tarea, nuevo_tiempo in zip(tareas_a_realizar, nuevos_tiempos):
        tarea.tiempo = nuevo_tiempo
        session.commit()

    return nuevos_tiempos

def alarma(tarea):
    print("Alarma para la tarea: " + tarea['contenido'])

@app.route('/configurar_alarma/<int:index>', methods=['POST'])
def configurar_alarma(index):
    tarea = tareas_a_realizar[index]
    tiempo = request.form['tiempo']
    scheduler.add_job(alarma, 'date', run_date=tiempo, args=[tarea])
    return redirect(url_for('ver_tareas'))

# Uso la función recalcular_horas al ver_horario
@app.route('/ver_horario')
def ver_horario():
    tareas_a_realizar = session.query(TareasSemana).filter_by(id_usuario=current_user.id_usuario).all()
    tiempo_disponible_obj = session.query(TiempoDisponible).filter_by(id_usuario=current_user.id_usuario).first()
    tiempo_disponible = tiempo_disponible_obj.horas_disponibles if tiempo_disponible_obj else 0

    recalcular_horas(tareas_a_realizar, tiempo_disponible)

    return render_template('ver_horario.html', horas=tiempo_disponible, tareas=tareas_a_realizar)

def verificar_cambio_actividad():
    usuarios = session.query(Usuario).all()
    for usuario in usuarios:
        tareas = session.query(TareasSemana).filter_by(id_usuario=usuario.id_usuario).all()
        for tarea in tareas:
            tiempo_actual = datetime.now().time()
            horario_inicio = tarea.horario_inicio
            if horario_inicio <= tiempo_actual < (datetime.combine(datetime.today(), horario_inicio) + timedelta(minutes=tarea.tiempo)).time():
                usuario.ultima_actividad = tarea.actividad
                session.commit()
                break

scheduler.add_job(verificar_cambio_actividad, 'interval', minutes=1)

# Ruta para tareas hoy para que el usuario pueda ver las tareas que tiene en el día de hoy.
@app.route("/tareas_hoy")
@login_required
def tareas_hoy():
    return render_template('sitio/tareas_hoy.html')

# Rutas para errores 404
@app.errorhandler(404)
def page_not_found():
    return render_template('errores/404.html'), 404


# Espacio reservado para administrador web





if __name__ == "__main__":
    db.Base.metadata.create_all(db.engine)  # Creo el modelo de datos
    app.run(debug=True)  # El debug=True hace que cada vez que reiniciemos el servidor o modifiquemos código,
    # el servidor Flask se reinicie solo.
