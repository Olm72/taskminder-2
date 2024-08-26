document.addEventListener('DOMContentLoaded', function() {
    console.log("taskminder_script.js cargado");

    // Verifica si window.taskminderData está definido antes de acceder a sus propiedades
    if (typeof window.taskminderData !== 'undefined') {
        console.log("window.taskminderData:", window.taskminderData);

        // Mostrar los valores de las alarmas, tareas y recordatorios en la página
        if (document.getElementById("proxima-alarma-display")) {
            document.getElementById("proxima-alarma-display").textContent = window.taskminderData.proximaAlarma || 'Ninguna alarma programada';
        }
        if (document.getElementById("contenido-tarea-display")) {
            document.getElementById("contenido-tarea-display").textContent = window.taskminderData.contenidoTarea || 'Ninguna tarea disponible';
        }
        if (document.getElementById("tiempo-recordatorio-display")) {
            document.getElementById("tiempo-recordatorio-display").textContent = window.taskminderData.tiempoRecordatorio + " minuto" + (window.taskminderData.tiempoRecordatorio !== 1 ? "s" : "");
        }

        console.log("Próxima alarma:", window.taskminderData.proximaAlarma);
        console.log("Contenido de la tarea:", window.taskminderData.contenidoTarea);
        console.log("Tiempo de recordatorio:", window.taskminderData.tiempoRecordatorio);
    } else {
        console.log("window.taskminderData no está definido. Este script no se ejecuta en esta página.");
    }

    // Configuración de los paneles de acordeón
    var acc = document.getElementsByClassName("accordion");
    console.log("Elementos con clase 'accordion':", acc);

    if (acc.length > 0) {
        for (var i = 0; i < acc.length; i++) {
            if (acc[i]) {
                acc[i].addEventListener("click", function() {
                    this.classList.toggle("active");
                    var panel = this.nextElementSibling;
                    if (panel) {
                        if (panel.style.maxHeight) {
                            panel.style.maxHeight = null;
                        } else {
                            panel.style.maxHeight = panel.scrollHeight + "px";
                        }
                    }
                });

                // Verificar si el panel siguiente existe y ajustar la altura si ya está activo
                var panel = acc[i].nextElementSibling;
                if (acc[i].classList.contains("active") && panel) {
                    panel.style.maxHeight = panel.scrollHeight + "px";
                }
            }
        }
    } else {
        console.log("No se encontraron elementos 'accordion'. Este script no se ejecuta en esta página.");
    }

    // Verifica si el recordatorio-container existe antes de intentar manipularlo
    var recordatorioContainer = document.getElementById('recordatorio-container');
    if (recordatorioContainer) {
        // Función para mostrar el contenedor de recordatorio
        function mostrarRecordatorio() {
            var isChecked = document.querySelector('input[name="recordatorio"]:checked').value === 'true';
            if (isChecked) {
                recordatorioContainer.style.display = 'block';
                recordatorioContainer.style.maxHeight = recordatorioContainer.scrollHeight + "px";
                var panel = document.querySelector("#form-agregar-tarea .panel");
                if (panel) {
                    panel.style.maxHeight = parseInt(panel.style.maxHeight) + parseInt(recordatorioContainer.scrollHeight) + 20 + "px";
                }
            } else {
                recordatorioContainer.style.maxHeight = 0;
                setTimeout(function() {
                    recordatorioContainer.style.display = 'none';
                }, 200);
            }
        }

        // Evento para cambiar la visibilidad del recordatorio
        document.querySelectorAll('input[name="recordatorio"]').forEach(radio => {
            radio.addEventListener('change', mostrarRecordatorio);
        });

        // Evento para ocultar el contenedor de recordatorio y mostrar el botón "Agregar tarea"
        document.getElementById('ok-btn').addEventListener('click', function() {
            recordatorioContainer.style.maxHeight = 0;
            setTimeout(function() {
                recordatorioContainer.style.display = 'none';
            }, 200);
            document.getElementById('agregar-tarea-btn').style.display = 'block';
        });
    }

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
        var tiempoRecordatorio = recordatorio ? document.getElementById("tiempo_recordatorio").value : null;
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
                    alert("Error al agregar tarea: " + data.error);
                    console.error("Error al agregar tarea:", data.error);
                });
            }
        }).catch(error => {
            console.error("Error al agregar tarea:", error);
        });
    }

    // Asignar el evento de submit al formulario de agregar tarea
    var formAgregarTarea = document.getElementById("form-agregar-tarea");
    if (formAgregarTarea) {
        formAgregarTarea.addEventListener("submit", agregarTarea);
    }

    // Función para abrir el modal de alarma
    function abrirModal(tareaContenido, tareaId) {
        const modal = document.getElementById("modal");
        if (modal) {
            document.getElementById("modal-tarea-contenido").textContent = "Es el tiempo de tu tarea: " + tareaContenido;
            modal.setAttribute('data-tarea-id', tareaId);
            window.taskminderData.tareaId = tareaId;
            modal.style.display = "block";
        }
    }

    // Función para cerrar el modal de alarma
    function cerrarModal() {
        const modal = document.getElementById("modal");
        if (modal) {
            modal.style.display = "none";
        }
    }

    // Función para actualizar el estado de la tarea
    function actualizarEstadoTarea(idTarea, estado) {
        fetch('/actualizar_tarea', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                id_tarea: idTarea,
                estado: estado
            })
        }).then(response => {
            if (response.ok) {
                console.log("Tarea actualizada correctamente.");
                // Actualizamos el checkbox en la interfaz de usuario
                const checkbox = document.querySelector(`#tarea-realizada-${idTarea}`);
                if (checkbox) {
                    checkbox.checked = estado;
                }

            } else {
                console.error("Error al actualizar la tarea");
            }
        }).catch(error => {
            console.error("Error en la solicitud:", error);
        });
    }

    // Función para posponer una tarea
    function posponerTarea(tareaId, minutos) {
        fetch('/posponer_alarma', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: new URLSearchParams({
                id_tarea: tareaId,
                tiempo_posponer: minutos
            })
        }).then(response => {
            if (!response.ok) {
                console.error("Error al posponer la tarea");
            } else {
                window.location.reload(); // Recarga la página para reflejar los cambios
            }
        }).catch(error => {
            console.error("Error al posponer la tarea:", error);
        });
    }

    // Asignar eventos de los botones del modal
    var aceptarBtn = document.getElementById('aceptar-btn');
    if (aceptarBtn) {
        aceptarBtn.addEventListener('click', function() {
            cerrarModal();
            var tareaId = window.taskminderData.tareaId || document.getElementById("modal").getAttribute('data-tarea-id');
            if (tareaId) {
                actualizarEstadoTarea(tareaId, true);
            } else {
                console.error("No se pudo obtener el id_tarea.");
            }
        });
    }

    var posponerBtn = document.getElementById('posponer-btn');
    if (posponerBtn) {
        posponerBtn.addEventListener('click', function() {
            document.getElementById('posponer-container').style.display = 'block';
        });
    }

    var confirmarPosponerBtn = document.getElementById('alerta-alarma-confirmar-posponer-btn');
    if (confirmarPosponerBtn) {
        confirmarPosponerBtn.addEventListener('click', function() {
            const tiempoPosponer = parseInt(document.getElementById('tiempo-posponer').value, 10);
            posponerTarea(window.taskminderData.tareaId, tiempoPosponer);
            cerrarModal();
        });
    }

    // Función para reproducir el sonido de la alarma
    function playAlarma(tareaContenido, tareaId) {
        // Esto para asegurarme que tareaID se pasa correctamente
        console.log("playAlarma llamado con tareaId:", tareaId);
        const alarmaSonido = document.getElementById("alarma_sonido");
        if (alarmaSonido) {
            window.taskminderData.tareaId = tareaId || window.taskminderData.tareaId;
            alarmaSonido.play().then(() => {
                abrirModal(tareaContenido, window.taskminderData.tareaId);
            }).catch(error => {
                console.error("Error al reproducir la alarma: ", error);
            });
        } else {
            console.error("Elemento de sonido no encontrado.");
        }
    }

    // Función para reproducir el sonido del recordatorio
    function playRecordatorio(tareaContenido) {
        const audio = document.getElementById("recordatorio_sonido");
        if (audio) {
            audio.play().then(() => {
                alert(`Recordatorio para la tarea: ${tareaContenido}`);
            }).catch(error => {
                console.error("Error al reproducir el recordatorio: ", error);
            });
        }
    }

    // Función para dar formato a la fecha
    function formatoFecha(fecha) {
        let año = fecha.getFullYear();
        let mes = String(fecha.getMonth() + 1).padStart(2, '0');
        let dia = String(fecha.getDate()).padStart(2, '0');
        let horas = String(fecha.getHours()).padStart(2, '0');
        let minutos = String(fecha.getMinutes()).padStart(2, '0');
        let segundos = String(fecha.getSeconds()).padStart(2, '0');

        return `${año}-${mes}-${dia} ${horas}:${minutos}:${segundos}`;
    }

    // Comparar y disparar la alarma o recordatorio
    let checkInterval = setInterval(function() {
        if (typeof window.taskminderData !== 'undefined') {
            console.log("Actual taskminderData:", window.taskminderData);
            let ahora = new Date();
            let ahoraFormateada = formatoFecha(ahora);

            // Verificamos si proximaAlarma está definida y ejecutamos la lógica
            if (window.taskminderData.proximaAlarma && ahoraFormateada === window.taskminderData.proximaAlarma) {
                playAlarma(window.taskminderData.contenidoTarea, window.taskminderData.tareaId);
            }

            // Verificamos si proximoRecordatorio está definido y ejecutamos la lógica
            if (window.taskminderData.proximoRecordatorio && ahoraFormateada === window.taskminderData.proximoRecordatorio) {
                playRecordatorio(window.taskminderData.contenidoTarea);
            }
        }
    }, 1000);

    // Configuración de los botones de modificación, eliminación y checkbox de tareas realizadas
    document.querySelectorAll(".btn-modificar").forEach(button => {
        button.addEventListener("click", function() {
            var idTarea = this.getAttribute("data-id");
            var contenido = this.getAttribute("data-contenido");
            var prioridad = this.getAttribute("data-prioridad");
            var dias = this.getAttribute("data-dia").split(',');
            var hora = this.getAttribute("data-hora");
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
            var estado = this.checked ? true : false;

            // Asegúrate de que idTarea no sea undefined antes de continuar
            if (idTarea) {
                actualizarEstadoTarea(idTarea, estado);
            } else {
                console.error("No se pudo obtener el id_tarea. Asegúrate de que el checkbox tiene el atributo data-id correctamente.");
            }
        });
    });
});
