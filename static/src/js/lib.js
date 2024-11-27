export function getSpaceSize(nodeCount) {
    if (nodeCount < 100) {
      return 4096 / 2;
    } else if (nodeCount > 99 && nodeCount < 10000) {
      return 4096;
    } else {
      return 4096 * 2;
    }
  }