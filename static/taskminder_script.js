// Para los desplegables
var acc = document.getElementsByClassName("accordion");
for (var i = 0; i < acc.length; i++) {
    acc[i].addEventListener("click", function() {
        this.classList.toggle("active");
        var panel = this.nextElementSibling;
        panel.style.display = (panel.style.display === "block") ? "none" : "block";
    });
}

function mostrarRecordatorio() {
    var recordatorioRadio = document.querySelector('input[name="recordatorio"]:checked');
    var recordatorioContainer = document.getElementById('recordatorio-container');
    if (recordatorioRadio && recordatorioRadio.value === "si") {
        recordatorioContainer.style.display = "block";
    } else {
        recordatorioContainer.style.display = "none";
    }
}

function obtenerDiasSeleccionados() {
    var diasSeleccionados = [];
    var checkboxes = document.querySelectorAll('input[name="dias_semana"]:checked');
    checkboxes.forEach(function(checkbox) {
        diasSeleccionados.push(checkbox.value);
    });
    return diasSeleccionados;
}

function agregarTarea() {
    var tareaNombre = document.getElementById("contenido").value;
    var prioridad = document.getElementById("prioridad").value;
    var diasSeleccionados = obtenerDiasSeleccionados();
    var horaInicio = document.getElementById("hora_inicio").value;
    var duracion = document.getElementById("tiempo").value;
    var alarma = document.querySelector('input[name="alarma"]:checked').value === "si";
    var recordatorio = document.querySelector('input[name="recordatorio"]:checked').value === "si";
    var tiempoRecordatorio = document.getElementById("tiempo-recordatorio").value;

    // Verifica valores obtenidos
    console.log({
        contenido_tarea: tareaNombre,
        prioridad: prioridad,
        dias_semana: diasSeleccionados,
        horario_inicio: horaInicio,
        tiempo: duracion,
        alarma: alarma,
        recordatorio: recordatorio,
        tiempo_recordatorio: tiempoRecordatorio
    });

    fetch('/tareas_creadas', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            contenido_tarea: tareaNombre,
            prioridad: prioridad,
            dias_semana: diasSeleccionados,
            horario_inicio: horaInicio,
            tiempo: duracion,
            alarma: alarma,
            recordatorio: recordatorio,
            tiempo_recordatorio: tiempoRecordatorio
        })
    }).then(response => {
        if (response.ok) {
            location.reload();
        } else {
            console.error("Error al agregar tarea:", response.statusText);
        }
    }).catch(error => {
        console.error("Error al agregar tarea:", error);
    });
}

document.getElementById("agregar-tarea-btn").addEventListener("click", agregarTarea);

document.querySelectorAll('.modificar-tarea').forEach(button => {
    button.addEventListener('click', function() {
        var id_tarea = this.getAttribute('data-id');
        // Implementar lógica de modificación aquí
    });
});

document.querySelectorAll('.borrar-tarea').forEach(button => {
    button.addEventListener('click', function() {
        var id_tarea = this.getAttribute('data-id');
        fetch('/borrar_tarea', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ id_tarea: id_tarea })
        }).then(response => {
            if (response.ok) {
                location.reload();
            }
        });
    });
});

function actualizarHorario(tareas) {
    var dias = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo'];

    dias.forEach(function(dia) {
        var listaTareas = document.getElementById('tareas-' + dia);
        listaTareas.innerHTML = ''; // Limpiar lista

        tareas.filter(tarea => tarea.dias_semana.includes(dia)).forEach(function(tarea) {
            var listItem = document.createElement('li');
            var horaInicio = moment(tarea.horario_inicio, 'HH:mm').format('h:mm A');
            var duracion = tarea.tiempo + ' horas';

            listItem.innerHTML = `
                <div class="tarea-item">
                    <h4>${tarea.contenido}</h4>
                    <p>Prioridad: ${tarea.prioridad}</p>
                    <p>Hora de inicio: ${horaInicio}</p>
                    <p>Duración: ${duracion}</p>
                    <button class="modificar-tarea" data-id="${tarea.id}">Modificar</button>
                    <button class="borrar-tarea" data-id="${tarea.id}">Borrar</button>
                    <input type="checkbox" class="tarea-realizada" data-id="${tarea.id}" ${tarea.realizada ? 'checked' : ''}> Realizada
                </div>
            `;
            listaTareas.appendChild(listItem);
        });
    });

    // Añadir eventos a los botones de "Modificar" y "Borrar"
    document.querySelectorAll('.modificar-tarea').forEach(button => {
        button.addEventListener('click', function() {
            var id_tarea = this.getAttribute('data-id');
            // Implementar lógica de modificación aquí
        });
    });

    document.querySelectorAll('.borrar-tarea').forEach(button => {
        button.addEventListener('click', function() {
            var id_tarea = this.getAttribute('data-id');
            fetch('/borrar_tarea', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ id_tarea: id_tarea })
            }).then(response => {
                if (response.ok) {
                    location.reload();
                }
            });
        });
    });

    document.querySelectorAll('.tarea-realizada').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            var id_tarea = this.getAttribute('data-id');
            var realizada = this.checked;
            fetch('/actualizar_tarea', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ id_tarea: id_tarea, realizada: realizada })
            }).then(response => {
                if (!response.ok) {
                    console.error("Error al actualizar tarea:", response.statusText);
                }
            }).catch(error => {
                console.error("Error al actualizar tarea:", error);
            });
        });
    });
}

// Llamar a la función `actualizarHorario` con las tareas iniciales
fetch('/obtener_tareas')
    .then(response => response.json())
    .then(data => actualizarHorario(data.tareas))
    .catch(error => console.error("Error al obtener tareas:", error));
