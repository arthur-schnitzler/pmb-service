import { Cosmograph, CosmographTimeline } from "@cosmograph/cosmograph";

async function init() {
  const alertNode = document.getElementById("alert");
  const spinnerNode = document.getElementById("spinner");
  const legendNode = document.getElementById("legend");
  const canvas = document.createElement("div");

  const queryString = window.location.search;
  const url = `/network/csv/${queryString}`;

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

          // Calculate the degree of each node
  const nodeDegrees = {};
  links.forEach(link => {
    nodeDegrees[link.source] = (nodeDegrees[link.source] || 0) + 1;
    nodeDegrees[link.target] = (nodeDegrees[link.target] || 0) + 1;
  });

  // Assign the degree to each node
  nodes.forEach(node => {
    node.degree = nodeDegrees[node.id] || 0;
  });

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
      nodeSize: (node) => {
        const degree = node.degree || 1; // Default to 1 if degree is not defined
        return Math.max(1, Math.log(degree * 10)); // Adjust the multiplier and minimum size as needed
      },
      nodeLabelAccessor: (d) => d.label,
      showTopLabels: true,
      showDynamicLabels: false,
      linkGreyoutOpacity: 0,
      nodeLabelColor: "white",
      hoveredNodeLabelColor: "white",
      linkWidth: 1,
      linkArrows: false,
      onClick: (data) => alert(data.label),
      simulationRepulsion: 1,
      linkDistance: 5,
      gravity: 0.5
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
