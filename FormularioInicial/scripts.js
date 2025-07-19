document.getElementById("reembolsoForm").addEventListener("submit", async function (e) {
  e.preventDefault();

  const form = e.target;
  const mensajeDiv = document.getElementById("mensaje");
  mensajeDiv.innerText = ""; // limpiar mensaje

  // Recolectar campos del formulario
  const nombre = form.nombre.value.trim();
  const cedula = form.cedula.value.trim();
  const departamento = form.departamento.value.trim();
  const correo = form.correo.value.trim();
  const telefono = form.telefono.value.trim();
  const fechaGasto = form.fechaGasto.value;
  const tipoGasto = form.tipoGasto.value;
  const numeroFactura = form.numeroFactura.value.trim();
  const monto = parseFloat(form.monto.value);
  const medioPago = form.medioPago.value;
  const descripcion = form.descripcion.value.trim();
  const archivo = form.archivo.files[0];

  // Validación mínima personalizada (opcional)
  if (!nombre || !cedula || !departamento || !correo || !fechaGasto || !tipoGasto || !numeroFactura || isNaN(monto) || monto <= 0 || !medioPago || !descripcion) {
    mensajeDiv.innerText = "⚠️ Por favor completa todos los campos requeridos.";
    return;
  }

  try {
    // Crear las variables para Camunda
    const variables = {
      nombre: { value: nombre, type: "String" },
      cedula: { value: cedula, type: "String" },
      departamento: { value: departamento, type: "String" },
      correo: { value: correo, type: "String" },
      telefono: { value: telefono, type: "String" },
      fechaGasto: { value: fechaGasto, type: "String" },
      tipoGasto: { value: tipoGasto, type: "String" },
      numeroFactura: { value: numeroFactura, type: "String" },
      monto: { value: monto, type: "Double" },
      medioPago: { value: medioPago, type: "String" },
      descripcion: { value: descripcion, type: "String" }
      // Puedes agregar más variables si se requiere
    };

    const payload = {
      variables: variables,
      businessKey: `reembolso-${cedula}-${Date.now()}`
    };

    // 1. Opcional: manejo del archivo (si tienes backend)
    // Aquí podrías enviar el archivo a un backend con FormData.
    // Luego, podrías guardar el nombre o la URL como variable.

    // 2. Enviar los datos al motor BPM
    const response = await fetch("http://localhost:8080/engine-rest/process-definition/key/reembolso/start", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });

    if (response.ok) {
      mensajeDiv.innerText = "✅ Solicitud enviada correctamente.";
      form.reset();
    } else {
      const errorText = await response.text();
      mensajeDiv.innerText = "❌ Error al enviar solicitud: " + errorText;
    }

  } catch (error) {
    console.error("Error de conexión:", error);
    mensajeDiv.innerText = "❌ No se pudo conectar al servidor.";
  }
});
