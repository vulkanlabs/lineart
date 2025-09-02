import type { Edge } from "@xyflow/react";
import type { VulkanNode } from "../types/workflow";

export const defaultElkOptions = {
    "elk.algorithm": "layered",
    "elk.layered.nodePlacement.strategy": "SIMPLE",
    "elk.layered.spacing.nodeNodeBetweenLayers": "80",
    "elk.spacing.nodeNode": "60",
    "elk.direction": "RIGHT",
    "elk.aspectRatio": "1.2",
    "elk.center": "true",
};

export type UnlayoutedVulkanNode = VulkanNode;

/**
 * Main entry point for node layout calculation
 * 
 * Strategy:
 * - If workflow has complex branching/decisions -> Use ELK algorithm
 * - If workflow is simple and linear -> Use custom level-based layout
 * - If no INPUT node found -> Fallback to ELK
 *
 * - Simple workflows: Custom algorithm is faster and produces cleaner layouts
 * - Complex workflows: ELK handles edge crossings and hierarchy better
 * 
 * @param nodes - Nodes without position data
 * @param edges - Connection data between nodes
 * @returns Nodes with calculated positions
 */
export async function getLayoutedNodes(
    nodes: UnlayoutedVulkanNode[],
    edges: Edge[],
): Promise<VulkanNode[]> {
    if (nodes.length === 0) return nodes as VulkanNode[];

    // Use ELK for complex workflows (branching, decisions, multiple inputs)
    if (shouldUseElkLayout(nodes, edges)) {
        return await getElkLayoutedNodes(nodes, edges);
    }

    // For simple workflows: Use faster custom algorithm
    const inputNode = nodes.find((node) => node.type === "INPUT");
    if (!inputNode) {
        // No INPUT node = can't determine flow direction, use ELK
        return await getElkLayoutedNodes(nodes, edges);
    }

    // Custom level-based layout for simple linear workflows
    const levels = createWorkflowLevels(nodes, edges, inputNode);
    return positionNodesInWorkflow(levels);
}

/**
 * Create workflow levels for left-to-right layout
 * 
 * Algorithm: Topological sort with dependency checking
 * - Start with INPUT node at level 0
 * - For each level, find all nodes whose dependencies are satisfied
 * - Only place a node when ALL its input dependencies are in previous levels
 * - Continue until no more nodes can be placed
 * - Handle orphaned nodes by placing them in the final level
 *
 * Ensures clean left-to-right flow without backward edges
 * 
 * Example:
 * INPUT -> [TRANSFORM, API] -> DECISION -> TERMINATE
 * Level 0: INPUT
 * Level 1: TRANSFORM, API (both depend only on INPUT)
 * Level 2: DECISION (depends on both TRANSFORM and API)
 * Level 3: TERMINATE (depends on DECISION)
 */
function createWorkflowLevels(
    nodes: UnlayoutedVulkanNode[],
    edges: Edge[],
    inputNode: UnlayoutedVulkanNode,
): UnlayoutedVulkanNode[][] {
    const levels: UnlayoutedVulkanNode[][] = [];
    const visited = new Set<string>();

    // Always start with INPUT node
    levels[0] = [inputNode];
    visited.add(inputNode.id);

    let currentLevel = 0;
    while (levels[currentLevel] && levels[currentLevel].length > 0) {
        const nextLevel: UnlayoutedVulkanNode[] = [];

        // For each node in current level, find its direct dependents
        levels[currentLevel].forEach((node) => {
            const dependents = edges
                .filter((edge) => edge.source === node.id)      // Find outgoing edges
                .map((edge) => edge.target)                      // Get target node IDs
                .map((targetId) => nodes.find((n) => n.id === targetId)) // Get actual nodes
                .filter(Boolean) as UnlayoutedVulkanNode[];      // Remove nulls

            // Check if each dependent is ready to be placed
            dependents.forEach((dependent) => {
                if (!visited.has(dependent.id)) {
                    // Get ALL dependencies of this node (not just from current level)
                    const allDeps = edges
                        .filter((edge) => edge.target === dependent.id) // All incoming edges
                        .map((edge) => edge.source);                     // All source nodes

                    // Only place node if ALL dependencies have been visited
                    // This prevents placing nodes before their inputs are ready
                    if (allDeps.every((depId) => visited.has(depId))) {
                        nextLevel.push(dependent);
                        visited.add(dependent.id);
                    }
                }
            });
        });

        // Add next level if we found any nodes
        if (nextLevel.length > 0) {
            levels[currentLevel + 1] = nextLevel;
        }
        currentLevel++;
    }

    // Handle orphaned nodes (nodes with no path from INPUT)
    const unplacedNodes = nodes.filter((node) => !visited.has(node.id));
    if (unplacedNodes.length > 0) {
        levels.push(unplacedNodes);
    }

    return levels.filter((level) => level.length > 0);
}

/**
 * Position nodes in calculated levels with proper spacing
 * 
 * - Each level gets its own column (X position)
 * - Within each column, center nodes vertically
 * - Calculate total height needed for all nodes in level
 * - Position nodes from top to bottom with even spacing
 *
 * - Horizontal: 500px between columns (room for connections)
 * - Vertical: 20px between nodes + dynamic height based on node content
 * - Centering: Start from center and work up/down for balanced layout
 */
function positionNodesInWorkflow(levels: UnlayoutedVulkanNode[][]): VulkanNode[] {
    const positionedNodes: VulkanNode[] = [];
    const HORIZONTAL_SPACING = 500; // Space between columns
    const VERTICAL_MARGIN = 20;     // Space between nodes in same column
    const START_X = 100;            // Left margin
    const START_Y = 100;            // Top margin offset

    levels.forEach((level, levelIndex) => {
        // Calculate X position for this column
        const levelX = START_X + levelIndex * HORIZONTAL_SPACING;
        
        // Get heights of all nodes in this level for spacing calculations
        const nodeHeights = level.map((node) => getNodeHeight(node));
        
        // Calculate total vertical space needed for this level
        const totalLevelHeight =
            nodeHeights.reduce((sum, height) => sum + height, 0) +  // Sum of node heights
            (level.length - 1) * VERTICAL_MARGIN;                   // Spacing between nodes

        // Start from center and work vertically to create balanced layout
        let currentY = START_Y - totalLevelHeight / 2;

        // Position each node in this level
        level.forEach((node, nodeIndex) => {
            positionedNodes.push({
                ...node,
                position: { x: levelX, y: currentY },
            } as VulkanNode);

            // Move to next vertical position
            currentY += nodeHeights[nodeIndex] + VERTICAL_MARGIN;
        });
    });

    return positionedNodes;
}

function getNodeHeight(node: UnlayoutedVulkanNode): number {
    if (node.height && node.height > 0 && node.type !== "CONNECTION") {
        return node.height + 30;
    }

    if (node.type === "CONNECTION") {
        return calculateConnectionHeight(node);
    }

    const heights: Record<string, number> = {
        INPUT: 240,
        DATA_INPUT: 240,
        TRANSFORM: 300,
        BRANCH: 480,
        DECISION: 350,
        TERMINATE: 380,
        POLICY: 220,
    };

    return heights[node.type] || 300;
}

function calculateConnectionHeight(node: UnlayoutedVulkanNode): number {
    let height = 200;

    if (node.data?.metadata) {
        const metadata = node.data.metadata;

        if (metadata.headers && typeof metadata.headers === "object") {
            height += Object.keys(metadata.headers).length * 50;
        }

        if (metadata.params && typeof metadata.params === "object") {
            height += Math.max(Object.keys(metadata.params).length * 65, 160);
        } else {
            height += 120;
        }

        if (metadata.body && typeof metadata.body === "object") {
            const bodySize = JSON.stringify(metadata.body).length;
            height += Math.max(80, Math.min(bodySize / 8, 250));
        }

        height += 200;
    } else {
        height += 320;
    }

    return height;
}

/**
 * Decide whether to use ELK algorithm or custom layout
 * 
 * ELK is needed for complex workflows with:
 * - Decision/Branch nodes (conditional logic)
 * - High fan-out (node with 3+ outputs)
 * - High fan-in (node with 3+ inputs)
 *
 * - Conditional nodes create diamond/tree patterns that need special handling
 * - High fan-out/fan-in creates complex edge crossing problems
 * - Custom algorithm assumes simple linear flow, breaks with complex patterns
 * 
 * - Custom layout: Fast, clean results for simple workflows
 * - ELK layout: Slower, but handles complexity gracefully
 */
function shouldUseElkLayout(nodes: UnlayoutedVulkanNode[], edges: Edge[]): boolean {
    // Conditional logic nodes always need ELK
    const hasConditionalNodes = nodes.some(
        (node) => node.type === "DECISION" || node.type === "BRANCH",
    );
    if (hasConditionalNodes) return true;

    // High fan-out complexity (one node connects to 3+ others)
    const hasBranchingComplexity = nodes.some((node) => {
        const outgoingEdges = edges.filter((edge) => edge.source === node.id);
        return outgoingEdges.length >= 3; // Fan-out threshold
    });
    if (hasBranchingComplexity) return true;

    // High fan-in complexity (one node receives from 3+ others)
    const targetCounts = new Map<string, number>();
    edges.forEach((edge) => {
        targetCounts.set(edge.target, (targetCounts.get(edge.target) || 0) + 1);
    });
    
    // If any node has 3+ inputs, use ELK for proper edge routing
    return Array.from(targetCounts.values()).some((count) => count >= 3);
}

async function getElkLayoutedNodes(
    nodes: UnlayoutedVulkanNode[],
    edges: Edge[],
): Promise<VulkanNode[]> {
    try {
        const ELK = (await import("elkjs/lib/elk.bundled.js")).default;
        const elk = new ELK();

        const hierarchicalStructure = createHierarchicalStructure(nodes, edges);
        const layoutedGraph = await elk.layout(hierarchicalStructure);

        return flattenHierarchicalNodes(layoutedGraph, nodes);
    } catch (error) {
        console.error("ELK layout failed:", error);
        const inputNode = nodes.find((node) => node.type === "INPUT");
        if (inputNode) {
            const levels = createWorkflowLevels(nodes, edges, inputNode);
            return positionNodesInWorkflow(levels);
        }
        return simpleGridLayout(nodes);
    }
}

function createHierarchicalStructure(nodes: UnlayoutedVulkanNode[], edges: Edge[]) {
    const conditionalNodes = nodes.filter(
        (node) => node.type === "DECISION" || node.type === "BRANCH",
    );

    const branchGroups = new Map<string, UnlayoutedVulkanNode[]>();
    const processedNodes = new Set<string>();

    conditionalNodes.forEach((conditionalNode) => {
        if (processedNodes.has(conditionalNode.id)) return;

        const childrenEdges = edges.filter((edge) => edge.source === conditionalNode.id);

        if (childrenEdges.length >= 2) {
            const siblingEntryPoints = new Set(childrenEdges.map((edge) => edge.target));
            const sortedEdges = sortEdgesByConditionLogic(conditionalNode, childrenEdges);

            sortedEdges.forEach((edge, index) => {
                const branchGroupId = `${conditionalNode.id}_branch_${index}`;
                const exclusionSet = new Set([...processedNodes, ...siblingEntryPoints]);
                exclusionSet.delete(edge.target);

                const branchNodes = findBranchNodes(edge.target, nodes, edges, exclusionSet);

                if (branchNodes.length > 0) {
                    branchGroups.set(branchGroupId, branchNodes);
                    branchNodes.forEach((node) => processedNodes.add(node.id));
                }
            });
        }
    });

    const elkNodes: any[] = [];
    const elkEdges: any[] = [];

    // Add ungrouped nodes
    const ungroupedNodes = nodes.filter((node) => !processedNodes.has(node.id));
    ungroupedNodes.forEach((node) => {
        elkNodes.push({
            id: node.id,
            width: getNodeWidth(node),
            height: getNodeHeight(node),
        });
    });

    // Add branch groups in sorted order
    const sortedBranchGroups = Array.from(branchGroups.entries()).sort((a, b) => {
        const indexA = parseInt(a[0].split("_branch_")[1] || "999", 10);
        const indexB = parseInt(b[0].split("_branch_")[1] || "999", 10);
        return indexA - indexB;
    });

    sortedBranchGroups.forEach(([groupId, branchNodes], index) => {
        elkNodes.push({
            id: groupId,
            layoutOptions: {
                "elk.algorithm": "layered",
                "elk.direction": "DOWN",
                "elk.spacing.nodeNode": "30",
                "elk.layered.nodePlacement.strategy": "LINEAR_SEGMENTS",
                "elk.layered.spacing.nodeNodeBetweenLayers": "45",
            },
            children: branchNodes.map((node) => ({
                id: node.id,
                width: getNodeWidth(node),
                height: getNodeHeight(node),
            })),
            edges: edges
                .filter(
                    (edge) =>
                        branchNodes.some((n) => n.id === edge.source) &&
                        branchNodes.some((n) => n.id === edge.target),
                )
                .map((edge) => ({
                    id: edge.id || `${edge.source}-${edge.target}`,
                    sources: [edge.source],
                    targets: [edge.target],
                })),
        });
    });

    // Add main-level edges
    edges.forEach((edge) => {
        const sourceInGroup = Array.from(branchGroups.entries()).find(([, nodes]) =>
            nodes.some((n) => n.id === edge.source),
        );
        const targetInGroup = Array.from(branchGroups.entries()).find(([, nodes]) =>
            nodes.some((n) => n.id === edge.target),
        );

        if (sourceInGroup && targetInGroup && sourceInGroup[0] === targetInGroup[0]) {
            return;
        }

        const sourceId = sourceInGroup ? sourceInGroup[0] : edge.source;
        const targetId = targetInGroup ? targetInGroup[0] : edge.target;

        elkEdges.push({
            id: edge.id || `${sourceId}-${targetId}`,
            sources: [sourceId],
            targets: [targetId],
        });
    });

    return {
        id: "workflow",
        layoutOptions: {
            ...defaultElkOptions,
            "elk.hierarchyHandling": "INCLUDE_CHILDREN",
        },
        children: elkNodes,
        edges: elkEdges,
    };
}

function sortEdgesByConditionLogic(conditionalNode: UnlayoutedVulkanNode, edges: Edge[]): Edge[] {
    if (conditionalNode.type === "BRANCH" && conditionalNode.data?.metadata?.choices) {
        return edges.sort((a, b) => {
            const indexA = parseInt(a.sourceHandle || "999", 10);
            const indexB = parseInt(b.sourceHandle || "999", 10);

            if (indexA !== indexB) {
                return indexA - indexB;
            }

            return a.target.localeCompare(b.target);
        });
    }

    return edges.sort((a, b) => a.target.localeCompare(b.target));
}

function findBranchNodes(
    startNodeId: string,
    allNodes: UnlayoutedVulkanNode[],
    edges: Edge[],
    excludeNodes: Set<string>,
): UnlayoutedVulkanNode[] {
    const branchNodes: UnlayoutedVulkanNode[] = [];
    const visited = new Set<string>();
    const queue = [startNodeId];

    while (queue.length > 0) {
        const nodeId = queue.shift()!;

        if (visited.has(nodeId) || excludeNodes.has(nodeId)) {
            continue;
        }

        visited.add(nodeId);
        const node = allNodes.find((n) => n.id === nodeId);

        if (node) {
            branchNodes.push(node);

            const childEdges = edges.filter((edge) => edge.source === nodeId);

            childEdges.forEach((edge) => {
                const targetId = edge.target;

                if (excludeNodes.has(targetId)) return;

                const parentCount = edges.filter((e) => e.target === targetId).length;

                if (parentCount > 1) {
                    const parentSources = edges
                        .filter((e) => e.target === targetId)
                        .map((e) => e.source);

                    const hasParentInBranch = parentSources.some(
                        (parentId) => visited.has(parentId) || parentId === nodeId,
                    );

                    const isConditionalConvergence =
                        parentSources.length >= 2 &&
                        parentSources.every((parentId) => excludeNodes.has(parentId));

                    if (hasParentInBranch && !isConditionalConvergence) {
                        queue.push(targetId);
                    }
                } else {
                    queue.push(targetId);
                }
            });
        }
    }

    return branchNodes;
}

function flattenHierarchicalNodes(
    layoutedGraph: any,
    originalNodes: UnlayoutedVulkanNode[],
): VulkanNode[] {
    const result: VulkanNode[] = [];

    function processNode(elkNode: any, parentOffset = { x: 0, y: 0 }) {
        if (elkNode.children) {
            elkNode.children.forEach((child: any) => {
                processNode(child, {
                    x: parentOffset.x + (elkNode.x || 0),
                    y: parentOffset.y + (elkNode.y || 0),
                });
            });
        } else {
            const originalNode = originalNodes.find((n) => n.id === elkNode.id);
            if (originalNode) {
                result.push({
                    ...originalNode,
                    position: {
                        x: parentOffset.x + (elkNode.x || 0),
                        y: parentOffset.y + (elkNode.y || 0),
                    },
                } as VulkanNode);
            }
        }
    }

    if (layoutedGraph.children) {
        layoutedGraph.children.forEach((child: any) => processNode(child));
    }

    return result;
}

function getNodeWidth(node: UnlayoutedVulkanNode): number {
    return node.width || 450;
}

function simpleGridLayout(nodes: UnlayoutedVulkanNode[]): VulkanNode[] {
    const GRID_SPACING_X = 500;
    const GRID_SPACING_Y = 300;
    const START_X = 100;
    const START_Y = 100;

    return nodes.map((node, index) => ({
        ...node,
        position: {
            x: START_X + (index % 3) * GRID_SPACING_X,
            y: START_Y + Math.floor(index / 3) * GRID_SPACING_Y,
        },
    }));
}

export function shouldApplyAutoLayout(uiMetadata: any): boolean {
    return !uiMetadata || Object.keys(uiMetadata).length === 0;
}
