document.addEventListener("DOMContentLoaded", () => {

  /* =========================
     FORM PRODUCTO
  ========================= */
  const productForm = document.querySelector("#product-form");

  if (productForm) {
    productForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      const response = await fetch(productForm.dataset.url, {
        method: "POST",
        headers: {
          "X-CSRFToken": document.getElementById("global-csrf-token").value,
        },
        body: new FormData(productForm),
      });

      const data = await response.json();

      if (data.ok) {
        alert("Producto actualizado correctamente");
        location.reload();
      }
    });
  }

  /* =========================
     FORM PROCESO
  ========================= */
  const processForm = document.querySelector("#process-form");
  const processIdInput = document.getElementById("process-id");

  if (processForm) {
    processForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      const formData = new FormData(processForm);
      const processId = processIdInput.value;

      const url = processId
        ? `/process/${processId}/update/`
        : processForm.dataset.createUrl;

      const response = await fetch(url, {
        method: "POST",
        headers: {
          "X-CSRFToken": document.getElementById("global-csrf-token").value,
        },
        body: formData,
      });

      const data = await response.json();

      if (data.ok) {
        alert(processId ? "Estado actualizado" : "Estado creado");
        location.reload();
      }
    });
  }
});

/* =========================
   EDITAR ESTADO
========================= */
function editProcess(id, status, encargada, salida, llegada, comment) {
  document.getElementById("process-id").value = id;
  document.querySelector('[name="status"]').value = status;
  document.querySelector('[name="encargada"]').value = encargada;
  document.querySelector('[name="fecha_salida"]').value = salida || "";
  document.querySelector('[name="fecha_llegada"]').value = llegada || "";
  document.querySelector('[name="comment"]').value = comment || "";

  document.getElementById("form-title").innerText = "Editar estado existente";
  window.scrollTo({ top: 0, behavior: "smooth" });
}

/* =========================
   ELIMINAR ESTADO
========================= */
async function deleteProcess(id) {
  if (!confirm("¿Eliminar este estado?")) return;

  const response = await fetch(`/process/${id}/delete/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": document.getElementById("global-csrf-token").value,
    },
  });

  const data = await response.json();

  if (data.ok) {
    document.getElementById(`process-${id}`).remove();
  }
}

/* =========================
   ELIMINAR PRODUCTO
========================= */
async function deleteProduct(id) {
  if (!confirm("⚠️ Esto eliminará el producto y todo su historial.\n¿Continuar?")) return;

  const response = await fetch(`/products/${id}/delete/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": document.getElementById("global-csrf-token").value,
    },
  });

  const data = await response.json();

  if (data.ok) {
    window.location.href = "/products/";
  }
}
