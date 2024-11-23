import {
  Cosmograph,
  CosmographSearch,
  CosmographTimeline,
} from "@cosmograph/cosmograph";
import * as d3 from "d3";

const edge_csv = "/media/edges.csv";
const node_csv = "/media/nodes.csv";

const edge_promis = d3.csv(edge_csv);
const node_promis = d3.csv(node_csv);
const alertNode = document.getElementById("alert")
const spinnerNode = document.getElementById("spinner");
const legendNode = document.getElementById("legend");
const canvas = document.createElement("div");

Promise.all([edge_promis, node_promis]).then(([edge_data, node_data]) => {
  const links = edge_data.map((d) => ({
    source: parseInt(d.source),
    target: parseInt(d.target),
    date: Date.parse(d.date),
  }));

  const nodes = node_data.map((d) => ({
    id: parseInt(d.id),
    label: d.label,
    color: d.color,
  }));
  const appNode = document.getElementById("app");

  // remove spinner
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
    onClick: (data) => alert(data.label) 
  };
  const cosmograph = new Cosmograph(canvas, config);

  const timelineContainer = document.createElement("div");
  const timeline = new CosmographTimeline(cosmograph, timelineContainer);


  const search = new CosmographSearch(cosmograph, searchContainer);
  cosmograph.setData(nodes, links);
  appNode.appendChild(timelineContainer);

});
