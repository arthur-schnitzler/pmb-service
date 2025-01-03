const url = document.getElementById("url").textContent;

function showModal(object) {
  const options = {focus: true, keyboard: true, backdrop: true, dismiss: true};
  const eventLabels = object.points.map((p) => p.source.label);
  const curDate = object.points[0].source.date;
  const listItems = eventLabels.map((label) => `<li>${label}</li>`).join("");
  const urlParams = new URLSearchParams(window.location.search);
  urlParams.set("start_date", curDate);
  const newUrl = `/network/edges/?${urlParams.toString()}`;
  document.getElementById("staticBackdropLabel").innerHTML = `<a href="${newUrl}">${curDate}</a>`;
  document.getElementById("modal-body").innerHTML = `<ul>${listItems}</ul>`;
  const myModal = new bootstrap.Modal(document.getElementById('staticBackdrop'), options);
  myModal.toggle();
}

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

    // Ensure each event has a label property
    const validEvents = data.events
      .filter((event) => event.latitude && event.longitude)
      .map((event) => ({
        ...event,
        label: event.label || "Unknown Event", // Default to 'Unknown Event' if label is missing
      }));

    console.log(validEvents);
    const deckgl = new deck.DeckGL({
      container: "map",
      initialViewState: {
        altitude: 1.5,
        height: 700,
        longitude: 80,
        latitude: 35,
        zoom: 2,
        pitch: 60,
        // bearing: -1.7
      },
      controller: true,
      // onViewStateChange: ({ viewState }) => {
      //   console.log("Current view state:", viewState);
      // },
      layers: [
        new deck.HexagonLayer({
          data: validEvents,
          getPosition: (d) => [d.longitude, d.latitude],
          radius: 50000,
          elevationScale: 4000,
          elevationRange: [0, 50],
          extruded: true,
          pickable: true,
          onClick: (object) => showModal(object.object),
          onHover: ({ object, x, y }) => {
            const tooltip = document.getElementById("tooltip");
            if (object) {
              const curDate = object.points[0].source.date;
              
              tooltip.style.display = "block";
              tooltip.style.left = `${x}px`;
              tooltip.style.top = `${y}px`;
              tooltip.innerHTML = `<strong>${curDate}</strong><p>Klicke um mehr zu sehen</p>`;
            } else {
              tooltip.style.display = "none";
            }
          },
        }),
      ],
    });

    legendDiv.appendChild(dl);
  })
  .catch((error) => {
    console.error("Something went wrong:", error);
  });

// Add this CSS for the tooltip
const style = document.createElement("style");
style.innerHTML = `
  #tooltip {
    position: absolute;
    background: white;
    padding: 5px;
    border: 1px solid black;
    display: none;
    pointer-events: none;
  }
`;
document.head.appendChild(style);

// Add this HTML for the tooltip
const tooltip = document.createElement("div");
tooltip.id = "tooltip";
document.body.appendChild(tooltip);
