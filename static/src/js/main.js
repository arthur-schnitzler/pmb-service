import { Cosmograph, CosmographTimeline } from "@cosmograph/cosmograph";

async function init() {
  const alertNode = document.getElementById("alert");
  const spinnerNode = document.getElementById("spinner");
  const legendNode = document.getElementById("legend");
  const canvas = document.createElement("div");

  const queryString = window.location.search;
  const url = `/network/csv/${queryString}`;
  console.log(url);

  try {
    const res = await fetch(url);
    const data = await res.json();

    const colors = {
      person: "#720e07",
      place: "#5bc0eb",
      work: "#ff8600",
      event: "#9bc53d",
      institution: "#ffdd1b",
    };

    const links = data["edges"].map((d) => ({
      source: parseInt(d.s),
      target: parseInt(d.t),
      date: Date.parse(d.start),
    }));

    const nodes = data["nodes"].map((d) => ({
      id: parseInt(d.id),
      label: d.l,
      color: colors[d["k"]],
    }));

    const appNode = document.getElementById("app");

    // Remove spinner
    spinnerNode.classList.add("visually-hidden");
    legendNode.style.visibility = "visible";
    alertNode.classList.add("visually-hidden");

    appNode.appendChild(canvas);
    const searchContainer = document.createElement("div");
    appNode.appendChild(searchContainer);

    const config = {
      nodeColor: (d) => d.color,
      nodeLabelAccessor: (d) => d.label,
      showTopLabels: true,
      showDynamicLabels: false,
      linkGreyoutOpacity: 0,
      nodeLabelColor: "white",
      hoveredNodeLabelColor: "white",
      linkWidth: 1,
      linkArrows: false,
      onClick: (data) => alert(data.label),
    };

    const cosmograph = new Cosmograph(canvas, config);

    const timelineContainer = document.createElement("div");
    const timeline = new CosmographTimeline(cosmograph, timelineContainer);
    cosmograph.setData(nodes, links);
    appNode.appendChild(timelineContainer);
  } catch (error) {
    console.error("Failed to fetch data:", error);
    alertNode.textContent = "Failed to load data. Please try again later.";
    alertNode.style.visibility = "visible";
  }
}

init();
