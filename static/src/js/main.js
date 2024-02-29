import { Cosmograph, CosmographSearch } from '@cosmograph/cosmograph'
import * as d3 from 'd3';

const edge_csv = "http://127.0.0.1:8000/static/src/edges.csv";
const node_csv = "http://127.0.0.1:8000/static/src/nodes.csv";

const edge_promis = d3.csv(edge_csv);
const node_promis = d3.csv(node_csv);

Promise.all([edge_promis, node_promis]).then(([edge_data, node_data]) => {
    const links = edge_data.map(d => ({
        source: parseInt(d.source),
        target: parseInt(d.target) // Convert string to number if needed
    }));
    console.log(links[0])

    const nodes = node_data.map(d => ({
        id: parseInt(d.id),
        label: d.label,
        color: d.color
    }))
    console.log(nodes[0])
    const appNode = document.getElementById("app")
    const canvas = document.createElement("div");
    canvas.style.height = "800px"
    appNode.appendChild(canvas);
    const searchContainer = document.createElement('div')
    appNode.appendChild(searchContainer);
    const config = {
        nodeColor: d => d.color,
        nodeLabelAccessor: d => d.label,
        nodeLabelColor: "white",
        hoveredNodeLabelColor: "white",
        linkWidth: 2
    }
    const cosmograph = new Cosmograph(canvas, config)
    const search = new CosmographSearch(cosmograph, searchContainer)
    cosmograph.setData(nodes, links)
    search.setData(nodes)
})

