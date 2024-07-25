document.addEventListener('DOMContentLoaded', function() {
    console.log("taskminder_script.js cargado");

    var acc = document.getElementsByClassName("accordion");
    for (var i = 0; i < acc.length; i++) {
        acc[i].addEventListener("click", function() {
            this.classList.toggle("active");
            var panel = this.nextElementSibling;
            if (panel.style.maxHeight) {
                panel.style.maxHeight = null;
            } else {
                panel.style.maxHeight = panel.scrollHeight + "px";
            }
        });

        // Asegurarse de que los elementos con la clase active se expandan por defecto
        var panel = acc[i].nextElementSibling;
        if (acc[i].classList.contains("active")) {
            panel.style.maxHeight = panel.scrollHeight + "px";
        }
    }

    // Función para mostrar recordatorio
    function mostrarRecordatorio() {
        var radios = document.getElementsByName('recordatorio');
        var container = document.getElementById('recordatorio-container');
        for (var i = 0; i < radios.length; i++) {
            if (radios[i].checked && radios[i].value == 'si') {
                container.style.display = 'block';
            } else {
                container.style.display = 'none';
            }
        }
    }

    // Añadir evento para cambiar la visibilidad del recordatorio
    var recordatorioRadios = document.getElementsByName('recordatorio');
    for (var i = 0; i < recordatorioRadios.length; i++) {
        recordatorioRadios[i].addEventListener('change', mostrarRecordatorio);
    }

    // Función para configurar la alarma
    function configurarAlarma(index) {
        document.getElementById('index').value = index;
    }

    // Botón para configurar la alarma de cada tarea
    document.querySelectorAll('.configurar-alarma-btn').forEach(button => {
        button.addEventListener('click', function() {
            const index = this.getAttribute('data-index');
            configurarAlarma(index);
        });
    });

    // Función para obtener los días seleccionados
    function obtenerDiasSeleccionados() {
        var diasSeleccionados = [];
        var checkboxes = document.querySelectorAll('input[name="dias_semana"]:checked');
        checkboxes.forEach(function(checkbox) {
            diasSeleccionados.push(checkbox.value);
        });
        return diasSeleccionados;
    }

    // Función para agregar tarea
    function agregarTarea() {
        var tareaNombre = document.getElementById("contenido").value;
        var prioridad = document.getElementById("prioridad").value;
        var diasSeleccionados = obtenerDiasSeleccionados();
        var horaInicio = document.getElementById("hora_inicio").value;
        var duracion = document.getElementById("tiempo").value;
        var alarma = document.querySelector('input[name="alarma"]:checked').value === "si";
        var recordatorio = document.querySelector('input[name="recordatorio"]:checked').value === "si";
        var tiempoRecordatorio = document.getElementById("tiempo-recordatorio").value;

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
});
