import { Graph } from "@cosmograph/cosmos";
import { getSpaceSize, COLORS } from "./lib.js";

async function init() {
  const spinnerNode = document.getElementById("spinner");
  const alertNode = document.getElementById("alertNode");
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
    let graph;
    let config = {
      backgroundColor: "#151515",
      nodeSize: (node) => {
        const degree = node.degree || 1; // Default to 1 if degree is not defined
        return Math.max(1, Math.log(degree * 10)); // Adjust the multiplier and minimum size as needed
      },
      nodeColor: (d) => d.color,
      nodeGreyoutOpacity: 0.1,
      linkWidth: 0.1,
      linkColor: "#5F74C2",
      linkArrows: false,
      linkGreyoutOpacity: 0,
      curvedLinks: true,
      renderHoveredNodeRing: true,
      hoveredNodeRingColor: "#4B5BBF",
      simulation: {
        linkDistance: 10,
        linkSpring: 2,
        repulsion: 0.2,
        gravity: 0.1,
        decay: 100000,
      },
    };
    graph = new Graph(canvas, config);
    graph.setData(nodes, links);
    graph.zoom(0.9);
  } catch (error) {
    console.error("Failed to fetch data:", error);
    alertNode.textContent = "Daten konnten leider nicht geladen werden";
    alertNode.classList.remove("visually-hidden");
  }
}

init();
