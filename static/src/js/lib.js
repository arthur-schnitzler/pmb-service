export function getSpaceSize(nodeCount) {
  if (nodeCount < 100) {
    return {
      spaceSize: 4096 / 4,
      simulationDecay: 100,
      simulationRepulsion: 1.0
    };
  } else if (nodeCount > 99 && nodeCount < 1000) {
    return {
      spaceSize: 4096 / 2,
      simulationDecay: 400,
      simulationRepulsion: 1.0
    };
  } else if (nodeCount > 999 && nodeCount < 10000) {
    return {
      spaceSize: 4096,
      simulationDecay: 800,
      simulationRepulsion: 1.0
    };
  } else {
    return {
      spaceSize: 4096 * 2,
      simulationDecay: 1000,
      simulationRepulsion: 0.8
    };
  }
}
export const COLORS = {
  person: "#720e07",
  place: "#5bc0eb",
  work: "#ff8600",
  event: "#9bc53d",
  institution: "#ffdd1b",
};
