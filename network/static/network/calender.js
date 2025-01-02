const url = document.getElementById("url").textContent;
console.log("fetching data");
fetch(url)
  .then((response) => {
    if (!response.ok) {
      throw new Error("Calender data response was not ok");
    }
    return response.json();
  })
  .then((data) => {
    const legendDiv = document.getElementById("legend");
    const dl = document.createElement("dl"); // Create the <dl> element

    data.metadata.query_params.forEach((param) => {
      for (const [key, value] of Object.entries(param)) {
        const dt = document.createElement("dt"); // Create the <dt> element
        dt.textContent = key;
        const dd = document.createElement("dd"); // Create the <dd> element
        dd.textContent = value;

        dl.appendChild(dt);
        dl.appendChild(dd);
      }
    });

    const validEvents = data.events.filter(event => event.latitude && event.longitude);
    console.log(validEvents);
    const deckgl = new deck.DeckGL({
      container: 'map',
      mapStyle: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
      initialViewState: {
      longitude: -122.4,
      latitude: 37.74,
      zoom: 11,
      pitch: 40.5,
      bearing: -27
      },
      controller: true,
      layers: [
      new deck.HexagonLayer({
        data: validEvents,
        data: validEvents,
        getPosition: d => [d.longitude, d.latitude],
        radius: 100000,
        elevationScale: 4,
        elevationRange: [0, 1000],
        extruded: true,
        pickable: true,
        coverage: 1
      })
      ]
    });

    legendDiv.appendChild(dl);
  })
  .catch((error) => {
    console.error("Something went wrong:", error);
  });
