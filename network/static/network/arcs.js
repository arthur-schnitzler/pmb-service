const url = document.getElementById("url").textContent;

function showModal(object) {
  const options = {
    focus: true,
    keyboard: true,
    backdrop: true,
    dismiss: true,
  };
  // const eventLabels = object.points.map((p) => p.source.label);
  // const curDate = object.points[0].source.date;
  // const listItems = eventLabels.map((label) => `<li>${label}</li>`).join("");
  // const urlParams = new URLSearchParams(window.location.search);
  // urlParams.set("start_date", curDate);
  const newUrl = `/entity/${object.id}`;
  const label = object.label;
  document.getElementById("staticBackdropLabel").innerHTML = `<a href="${newUrl}">${label}</a>`;
  // document.getElementById("modal-body").innerHTML = `<ul>${listItems}</ul>`;
  const myModal = new bootstrap.Modal(
    document.getElementById("staticBackdrop"),
    options
  );
  myModal.toggle();
}

console.log("fetching data hansi");
document.getElementById("loading-spinner").style.display = "block";
fetch(url)
  .then((response) => {
    if (!response.ok) {
      throw new Error("Timespan data response was not ok");
    }
    return response.json();
  })
  .then((data) => {
    document.getElementById("loading-spinner").style.display = "none"; // Hide spinner
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

    const items = data.items;

    console.log(items[1]);
    new deck.DeckGL({
      container: "map",
      mapStyle:
        "https://basemaps.cartocdn.com/gl/dark-matter-nolabels-gl-style/style.json",
      initialViewState: {
        longitude: 10.4356549,
        latitude: 48.9833712,
        zoom: 5,
        minZoom: 1,
        maxZoom: 15,
        pitch: 45,
      },
      onViewStateChange: ({ viewState }) => {
        console.log("Current view state:", viewState);
      },
      controller: true,
      layers: [
        new deck.ArcLayer({
          id: "arc-layer",
          data: items,
          getSourcePosition: (d) => d.from,
          getTargetPosition: (d) => d.to,
          getSourceColor: [0, 0, 0],
          getTargetColor: [255, 0, 0],
          getWidth: 4,
          pickable: true,
          onClick: (info) => showModal(info.object),
        }),
      ],
    });

    legendDiv.appendChild(dl);
  })
  .catch((error) => {
    document.getElementById("loading-spinner").style.display = "none"; // Hide spinner on error
    console.error("Something went wrong:", error);
  });
