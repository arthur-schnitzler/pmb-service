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
        longitude: -27,
        latitude: 0,
        zoom: 1,
        pitch: 60,
        bearing: 127.511,
      },
      controller: true,
      onViewStateChange: ({ viewState }) => {
        console.log("Current view state:", viewState);
      },
      layers: [
        new deck.HexagonLayer({
          data: validEvents,
          getPosition: (d) => [d.longitude, d.latitude],
          radius: 100000,
          elevationScale: 400,
          elevationRange: [0, 10000],
          extruded: true,
          pickable: true,
          onHover: ({ object, x, y }) => {
            const tooltip = document.getElementById("tooltip");
            if (object) {
              const eventLabels = object.points.map((p) => p.source.label);
              const listItems = eventLabels
                .map((label) => `<li>${label}</li>`)
                .join("");
              tooltip.style.display = "block";
              tooltip.style.left = `${x}px`;
              tooltip.style.top = `${y}px`;
              tooltip.innerHTML = `<div><ul>${listItems}</ul></div>`;
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
