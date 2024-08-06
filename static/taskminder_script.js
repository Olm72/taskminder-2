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

        var panel = acc[i].nextElementSibling;
        if (acc[i].classList.contains("active")) {
            panel.style.maxHeight = panel.scrollHeight + "px";
        }
    }

    // Función para mostrar recordatorio
    function mostrarRecordatorio() {
        var radios = document.getElementsByName('recordatorio');
        var container = document.getElementById('recordatorio-container');
        var isChecked = false;
        for (var i = 0; i < radios.length; i++) {
            if (radios[i].checked && radios[i].value === 'true') {
                isChecked = true;
                break;
            }
        }
        if (container) {
            if (isChecked) {
                container.style.display = 'block';
                container.style.maxHeight = container.scrollHeight + "px";
                // Esta línea para que no desaparezca el botón de "Agregar Tarea"
                var panel = document.querySelector("#form-agregar-tarea .panel");
                if (panel) {
                    panel.style.maxHeight = parseInt(panel.style.maxHeight) + parseInt(container.scrollHeight) + 20 + "px";
                }
            } else {
                container.style.maxHeight = 0;
                setTimeout(function() {
                    container.style.display = 'none';
                }, 200);
            }
        }
    }

    // Evento para cambiar la visibilidad del recordatorio
    var recordatorioRadios = document.getElementsByName('recordatorio');
    for (var i = 0; i < recordatorioRadios.length; i++) {
        recordatorioRadios[i].addEventListener('change', mostrarRecordatorio);
    }

    // Evento para ocultar el contenedor de recordatorio y mostrar el botón "Agregar tarea"
    document.getElementById('ok-btn').addEventListener('click', function() {
        var container = document.getElementById('recordatorio-container');
        container.style.maxHeight = 0;
        setTimeout(function() {
            container.style.display = 'none';
        }, 200);

        // Mostrar el botón "Agregar tarea"
        document.getElementById('agregar-tarea-btn').style.display = 'block';
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

    // Función para agregar una tarea
    function agregarTarea(event) {
        event.preventDefault();

        var tareaNombre = document.getElementById("contenido").value;
        var prioridad = document.getElementById("prioridad").value;
        var diasSeleccionados = obtenerDiasSeleccionados();
        var horaInicio = document.getElementById("hora_inicio").value;
        var duracion = document.getElementById("tiempo").value;
        var alarma = document.querySelector('input[name="alarma"]:checked').value === "true";
        var recordatorio = document.querySelector('input[name="recordatorio"]:checked').value === "true";
        var tiempoRecordatorio = document.getElementById("tiempo_recordatorio").value;
        var index = document.getElementById("index").value;

        fetch('/agregar_tarea', {
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
                tiempo_recordatorio: tiempoRecordatorio,
                index: index
            })
        }).then(response => {
            if (response.ok) {
                window.location.href = '/taskminder';
            } else {
                response.json().then(data => {
                    console.error("Error al agregar tarea:", data.error);
                });
            }
        }).catch(error => {
            console.error("Error al agregar tarea:", error);
        });
    }

    // Asegurar que el botón "Agregar tarea" al expandirse el panel siga visualizándose
    document.getElementById("form-agregar-tarea").addEventListener("submit", function(event) {
        var panel = document.querySelector("#form-agregar-tarea .panel");
        if (panel.style.maxHeight) {
            panel.style.maxHeight = panel.scrollHeight + "px";
        }
    });

    // Botones de modificar, borrar y checkbox realizada
    // Modificar tarea
    document.querySelectorAll(".btn-modificar").forEach(button => {
        button.addEventListener("click", function() {
            var idTarea = this.getAttribute("data-id");
            var contenido = this.getAttribute("data-contenido");
            var prioridad = this.getAttribute("data-prioridad");
            var dias = this.getAttribute("data-dia").split(',');
            var hora = this.getAttribute("data-hora")
            var tiempo = this.getAttribute("data-tiempo");
            var alarma = this.getAttribute("data-alarma") === "true";
            var recordatorio = this.getAttribute("data-recordatorio") === "true";
            var tiempoRecordatorio = this.getAttribute("data-tiempo_recordatorio");

            document.getElementById("contenido").value = contenido;
            document.getElementById("prioridad").value = prioridad;
            document.getElementById("hora_inicio").value = hora;
            document.getElementById("tiempo").value = tiempo;
            document.getElementById("index").value = idTarea;

            document.querySelectorAll('input[name="dias_semana"]').forEach(checkbox => {
                checkbox.checked = dias.includes(checkbox.value);
            });

            document.querySelector('input[name="alarma"][value="' + alarma + '"]').checked = true;
            document.querySelector('input[name="recordatorio"][value="' + recordatorio + '"]').checked = true;
            document.getElementById("tiempo_recordatorio").value = tiempoRecordatorio;

            mostrarRecordatorio();

            var panel = document.querySelector("#form-agregar-tarea .panel");
            panel.style.maxHeight = panel.scrollHeight + "px";
        });
    });

    // Borrar tarea
    document.querySelectorAll(".btn-borrar").forEach(button => {
        button.addEventListener("click", function() {
            var idTarea = this.getAttribute("data-id");
            fetch('/eliminar_tarea/' + idTarea, {
                method: 'POST'
            }).then(response => {
                if (response.ok) {
                    window.location.href = '/taskminder';
                } else {
                    console.error("Error al eliminar tarea");
                }
            }).catch(error => {
                console.error("Error al eliminar tarea:", error);
            });
        });
    });

    // Checkbox realizada
    document.querySelectorAll(".tarea-realizada").forEach(checkbox => {
        checkbox.addEventListener("change", function() {
            var idTarea = this.getAttribute("data-id");
            var estado = this.checked ? 1 : 0;
            fetch('/actualizar_tarea', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    tarea_id: idTarea,
                    estado: estado
                })
            }).then(response => {
                if (!response.ok) {
                    console.error("Error al actualizar el estado de la tarea");
                }
            }).catch(error => {
                console.error("Error al actualizar el estado de la tarea:", error);
            });
        });
    });

    // Asignar evento de submit al formulario de agregar tarea
    document.getElementById("form-agregar-tarea").addEventListener("submit", agregarTarea);
});
