import { NodeData } from "./types";

export enum NodeStatus {
    SUCCESS = "SUCCESS",
    ERROR = "ERROR",
    SKIPPED = "SKIPPED",
}
export type NodeStatusType = (typeof NodeStatus)[keyof typeof NodeStatus];

/**
 * Determine the status of a node based on its data.
 * @param nodeData - The data of the node.
 * @returns The status of the node: "SUCCESS", "ERROR", or "SKIPPED".
 */
export function getNodeStatus(nodeData: NodeData): NodeStatusType {
    // Input node is always considered successful if the run is executing
    if (nodeData.label === "input_node" || nodeData.type === "INPUT") {
        return NodeStatus.SUCCESS;
    }

    if (nodeData.run?.metadata?.error) return NodeStatus.ERROR;
    if (nodeData.run) return NodeStatus.SUCCESS;
    return NodeStatus.SKIPPED;
}

/** Calculate the duration between two timestamps.
 * @param startTime - The start time in seconds since epoch.
 * @param endTime - The end time in seconds since epoch.
 * @returns A formatted string representing the duration.
 */
export function calculateDuration(startTime: number, endTime: number): string {
    const start = new Date(startTime * 1000);
    const end = new Date(endTime * 1000);
    const duration = end.getTime() - start.getTime();
    return formatDuration(duration);
}

/** Format a duration in milliseconds into a human-readable string.
 * @param durationMs - The duration in milliseconds.
 * @returns A formatted string representing the duration.
 */
export function formatDuration(durationMs: number): string {
    const milliseconds = durationMs % 1000;
    const seconds = Math.floor(durationMs / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) {
        return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
    } else if (minutes > 0) {
        return `${minutes}m ${seconds % 60}s`;
    } else if (seconds > 0) {
        return `${seconds}s ${milliseconds}ms`;
    } else {
        return `${milliseconds}ms`;
    }
}
