  const map = L.map("map").setView([0, 0], 2);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(map);

  let markers = [];

  function cargarSismos() {
    const min_magnitud = document.getElementById("min_magnitud").value || 0;
    const start_time = document.getElementById("start_time").value || "2025-01-01";
    const end_time = document.getElementById("end_time").value || new Date().toISOString().split("T")[0];

    fetch(`/api/sismos_filtrados?min_magnitud=${min_magnitud}&start_time=${start_time}&end_time=${end_time}`)
      .then(res => res.json())
      .then(data => {
        // Limpiar marcadores previos
        markers.forEach(m => map.removeLayer(m));
        markers = [];

        data.forEach(sismo => {
          const marker = L.marker([sismo.lat, sismo.lng])
            .addTo(map)
            .bindPopup(`
              <b>${sismo.lugar}</b><br>
              Magnitud: ${sismo.magnitud}<br>
              Profundidad: ${sismo.profundidad} km<br>
              Fecha: ${sismo.fecha}
            `);
          markers.push(marker);
        });

        if (data.length > 0) {
          map.setView([data[0].lat, data[0].lng], 3);
        }
      });
  }

  document.getElementById("btn_filtrar").addEventListener("click", cargarSismos);

  // Cargar al inicio
  cargarSismos();