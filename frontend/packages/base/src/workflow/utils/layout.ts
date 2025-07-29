import type { Edge } from "@xyflow/react";
import type { VulkanNode } from "../types/workflow";

/**
 * Default layout options (kept for compatibility)
 */
export const defaultElkOptions = {};

/**
 * Type for nodes before layout positioning
 */
export type UnlayoutedVulkanNode = VulkanNode;

/**
 * Beautiful workflow-specific layout algorithm
 * Creates intuitive left-to-right flow with proper spacing and alignment
 */
export async function getLayoutedNodes(
    nodes: UnlayoutedVulkanNode[],
    edges: Edge[]
): Promise<VulkanNode[]> {
    if (nodes.length === 0) return nodes as VulkanNode[];

    // Find INPUT node as starting point
    const inputNode = nodes.find(node => node.type === "INPUT");
    if (!inputNode) {
        console.warn("No INPUT node found, using fallback layout");
        return simpleGridLayout(nodes);
    }

    const levels = createWorkflowLevels(nodes, edges, inputNode);
    
    return positionNodesInWorkflow(levels);
}


/**
 * Create workflow levels (left-to-right layers) based on dependency depth
 */
function createWorkflowLevels(
    nodes: UnlayoutedVulkanNode[], 
    edges: Edge[], 
    inputNode: UnlayoutedVulkanNode
): UnlayoutedVulkanNode[][] {
    const levels: UnlayoutedVulkanNode[][] = [];
    const visited = new Set<string>();
    const nodeLevel = new Map<string, number>();
    
    // Start with INPUT node at level 0
    levels[0] = [inputNode];
    visited.add(inputNode.id);
    nodeLevel.set(inputNode.id, 0);
    
    // Build levels by following edges
    let currentLevel = 0;
    while (levels[currentLevel] && levels[currentLevel].length > 0) {
        const nextLevel: UnlayoutedVulkanNode[] = [];
        
        levels[currentLevel].forEach(node => {
            // Find all nodes that depend on this node
            const dependents = edges
                .filter(edge => edge.source === node.id)
                .map(edge => edge.target)
                .map(targetId => nodes.find(n => n.id === targetId))
                .filter(Boolean) as UnlayoutedVulkanNode[];
            
            dependents.forEach(dependent => {
                if (!visited.has(dependent.id)) {
                    // Check if all dependencies of this node are already placed
                    const allDeps = edges
                        .filter(edge => edge.target === dependent.id)
                        .map(edge => edge.source);
                    
                    const allDepsPlaced = allDeps.every(depId => visited.has(depId));
                    
                    if (allDepsPlaced) {
                        nextLevel.push(dependent);
                        visited.add(dependent.id);
                        nodeLevel.set(dependent.id, currentLevel + 1);
                    }
                }
            });
        });
        
        if (nextLevel.length > 0) {
            levels[currentLevel + 1] = nextLevel;
        }
        currentLevel++;
    }
    
    // Add any remaining unplaced nodes to the end
    const unplacedNodes = nodes.filter(node => !visited.has(node.id));
    if (unplacedNodes.length > 0) {
        levels.push(unplacedNodes);
    }
    
    return levels.filter(level => level.length > 0);
}

/**
 * Position nodes in workflow levels with proper spacing
 */
function positionNodesInWorkflow(
    levels: UnlayoutedVulkanNode[][]
): VulkanNode[] {
    const positionedNodes: VulkanNode[] = [];
    const HORIZONTAL_SPACING = 650;
    const VERTICAL_MARGIN = 60;
    const START_X = 200;
    const START_Y = 200;
    
    levels.forEach((level, levelIndex) => {
        const levelX = START_X + (levelIndex * HORIZONTAL_SPACING);
        const nodeHeights = level.map(node => getNodeHeight(node));
        const totalLevelHeight = nodeHeights.reduce((sum, height) => sum + height, 0) + 
                                (level.length - 1) * VERTICAL_MARGIN;
        
        let currentY = START_Y - (totalLevelHeight / 2);
        
        level.forEach((node, nodeIndex) => {
            positionedNodes.push({
                ...node,
                position: { x: levelX, y: currentY }
            } as VulkanNode);
            
            currentY += nodeHeights[nodeIndex] + VERTICAL_MARGIN;
        });
    });
    
    return positionedNodes;
}

/**
 * Calculate node height for layout positioning
 */
function getNodeHeight(node: UnlayoutedVulkanNode): number {
    if (node.height && node.height > 0 && node.type !== 'CONNECTION') {
        return node.height + 50; 
    }
    
    // Special calculation for CONNECTION nodes (they expand with content)
    if (node.type === 'CONNECTION') {
        return calculateConnectionHeight(node);
    }
    
    // Default heights for other node types
    const heights: Record<string, number> = {
        INPUT: 275,
        DATA_INPUT: 275,
        TRANSFORM: 350,
        BRANCH: 550,
        DECISION: 400,
        TERMINATE: 450,
        POLICY: 250,
    };
    
    return heights[node.type] || 300;
}

/**
 * Calculate height for CONNECTION nodes based on their content
 */
function calculateConnectionHeight(node: UnlayoutedVulkanNode): number {
    let height = 225; 
    
    if (node.data?.metadata) {
        const metadata = node.data.metadata;
        
        if (metadata.headers && typeof metadata.headers === 'object') {
            height += Object.keys(metadata.headers).length * 60;
        }
        
        if (metadata.params && typeof metadata.params === 'object') {
            height += Math.max(Object.keys(metadata.params).length * 80, 200);
        } else {
            height += 150;
        }
        
        if (metadata.body && typeof metadata.body === 'object') {
            const bodySize = JSON.stringify(metadata.body).length;
            height += Math.max(80, Math.min(bodySize / 8, 250));
        }
        
        height += 250;
    } else {
        height += 400; 
    }
    
    return height;
}


/**
 * Fallback simple grid layout for when no INPUT node is found
 */
function simpleGridLayout(nodes: UnlayoutedVulkanNode[]): VulkanNode[] {
    const GRID_SPACING_X = 650;
    const GRID_SPACING_Y = 400;
    const START_X = 200;
    const START_Y = 200;
    
    return nodes.map((node, index) => ({
        ...node,
        position: {
            x: START_X + (index % 3) * GRID_SPACING_X,
            y: START_Y + Math.floor(index / 3) * GRID_SPACING_Y
        }
    }));
}

/**
 * Check if automatic layout should be applied
 * Returns true if nodes don't have ui_metadata (indicating they need positioning)
 */
export function shouldApplyAutoLayout(uiMetadata: any): boolean {
    return !uiMetadata || Object.keys(uiMetadata).length === 0;
}
