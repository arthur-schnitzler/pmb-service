const url = document.getElementById("url").textContent;
console.log("fetching data");
fetch(url)
  .then((response) => {
    if (!response.ok) {
      throw new Error("Geojson response was not ok");
    }
    return response.json();
  })
  .then((data) => {
    var map = L.map("map");
    const legendDiv = document.getElementById("legend");
    const dl = document.createElement("dl"); // Create the <dl> element

    data.metadata.query_params.forEach((param) => {
      for (const [key, value] of Object.entries(param)) {
        const dt = document.createElement("dt"); // Create the <dt> element
        dt.textContent = key;
        const dd = document.createElement("dd"); // Create the <dd> element
        dd.textContent = value;

        dl.appendChild(dt); // Append <dt> to <dl>
        dl.appendChild(dd); // Append <dd> to <dl>
      }
    });

    legendDiv.appendChild(dl);
    var OSMBaseLayer = L.tileLayer(
      "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
      {
        maxZoom: 19,
        attribution:
          '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      }
    ).addTo(map);

    var CartoDB_PositronNoLabels = L.tileLayer(
      "https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png",
      {
        attribution:
          '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: "abcd",
        maxZoom: 20,
      }
    );

    var CartoDB_DarkMatterNoLabels = L.tileLayer(
      "https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png",
      {
        attribution:
          '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: "abcd",
        maxZoom: 20,
      }
    );

    const markers = L.markerClusterGroup();
    const geojsonLayer = L.geoJSON(data, {
      onEachFeature: function (feature, layer) {
        layer.bindPopup(feature.properties.label);
      },
      pointToLayer: function (feature, latlng) {
        return L.marker(latlng);
      },
    });
    markers.addTo(map);
    geojsonLayer.eachLayer((layer) => markers.addLayer(layer));

    var heatData = [];
    L.geoJSON(data, {
      onEachFeature: function (feature, layer) {
        if (feature.geometry.type === "Point") {
          var lat = feature.geometry.coordinates[1];
          var lng = feature.geometry.coordinates[0];
          heatData.push([lat, lng]);
        }
      },
    });

    // Create the heatmap layer
    var heatmapLayer = L.heatLayer(heatData, {
      radius: 25,
      blur: 10,
      maxZoom: 17,
      max: 0.7,
      gradient: { 0: "white", 0.5: "lime", 1: "red" },
    });

    var baseMaps = {
      "Base Layer": OSMBaseLayer,
      "CartoDB hell": CartoDB_PositronNoLabels,
      "CartoDB dunkel": CartoDB_DarkMatterNoLabels,
    };

    const overlayMaps = {
      "Marker Cluster": markers,
      Heatmap: heatmapLayer,
    };

    L.control.layers(baseMaps, overlayMaps, { collapsed: false }).addTo(map);
    map.fitBounds(geojsonLayer.getBounds());
  })
  .catch((error) => {
    console.error("Something went wrong:", error);
  });
