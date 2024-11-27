export function getSpaceSize(nodeCount) {
  if (nodeCount < 100) {
    return 4096 / 2;
  } else if (nodeCount > 99 && nodeCount < 10000) {
    return 4096;
  } else {
    return 4096 * 2;
  }
}
export const COLORS = {
  person: "#720e07",
  place: "#5bc0eb",
  work: "#ff8600",
  event: "#9bc53d",
  institution: "#ffdd1b",
};

export function pause() {
  isPaused = true;
  pauseButton.textContent = "Start";
  graph.pause();
}

export function start() {
  isPaused = false;
  pauseButton.textContent = "Pause";
  graph.start();
}
