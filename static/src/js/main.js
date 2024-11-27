import { Cosmograph, CosmographTimeline } from "@cosmograph/cosmograph";
import { getSpaceSize, COLORS } from "./lib.js";

async function init() {
  const spinnerNode = document.getElementById("spinner");
  const canvas = document.getElementById("canvas");
  const queryString = window.location.search;
  const url = `/network/csv/${queryString}`;

  try {
    const res = await fetch(url);
    const data = await res.json();

    const links = data["edges"].map((d) => ({
      source: parseInt(d.s),
      target: parseInt(d.t),
      date: Date.parse(d.start),
    }));

    const nodes = data["nodes"].map((d) => ({
      id: parseInt(d.id),
      label: d.l,
      color: COLORS[d["k"]],
    }));

    // Calculate node size
    const nodeDegrees = {};
    links.forEach((link) => {
      nodeDegrees[link.source] = (nodeDegrees[link.source] || 0) + 1;
      nodeDegrees[link.target] = (nodeDegrees[link.target] || 0) + 1;
    });

    // Assign the degree to each node
    nodes.forEach((node) => {
      node.degree = nodeDegrees[node.id] || 0;
    });
    // Remove spinner
    spinnerNode.classList.add("visually-hidden");

    // configure graph
    const config = {
      backgroundColor: "white",
      spaceSize: getSpaceSize(nodes.length)["spaceSize"],
      nodeColor: (d) => d.color,
      linkColor: "#ebeded",
      nodeSize: (node) => {
        const degree = node.degree || 1; // Default to 1 if degree is not defined
        return Math.max(1, Math.log(degree * 100)); // Adjust the multiplier and minimum size as needed
      },
      nodeGreyoutOpacity: 0.1,
      nodeLabelAccessor: (d) => d.label,
      showTopLabels: false,
      showDynamicLabels: false,
      linkGreyoutOpacity: 0,
      nodeLabelColor: "white",
      hoveredNodeLabelColor: "white",
      linkWidth: 1,
      linkArrows: false,
      onClick: (data) => alert(data.label),
      simulationRepulsion: getSpaceSize(nodes.length)["simulationRepulsion"],
      simulationDecay: getSpaceSize(nodes.length)["simulationDecay"],
      simulationlinkDistance: 2,
      gravity: 0.5,
    };

    const graph = new Cosmograph(canvas, config);
    const timelineContainer = document.getElementById("timeline");
    new CosmographTimeline(graph, timelineContainer);
    graph.setData(nodes, links);

    // PAUSE BUTTON
    let isPaused = false;
    const pauseButton = document.getElementById("pause");

    function pause() {
      isPaused = true;
      pauseButton.textContent = "Start";
      graph.pause();
    }

    function start() {
      isPaused = false;
      pauseButton.textContent = "Pause";
      graph.start();
    }

    function togglePause() {
      if (isPaused) start();
      else pause();
    }

    pauseButton.addEventListener("click", togglePause);

    // FIT VIEW
    function fitView() {
      graph.fitView();
    }
    document.getElementById("fit-view")?.addEventListener("click", fitView);

    
  } catch (error) {
    console.error("Failed to fetch data:", error);
    alertNode.textContent = "Failed to load data. Please try again later.";
    alertNode.style.visibility = "visible";
  }
}

init();
