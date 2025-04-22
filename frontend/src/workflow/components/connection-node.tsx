import { useCallback } from "react";
import { useShallow } from "zustand/react/shallow";

import { Input } from "@/components/ui/input";

import { useWorkflowStore } from "../store";
import { WorkflowNode } from "./base";
import { NodeProps } from "@xyflow/react";
import { VulkanNode } from "../types";

export function ConnectionNode({ id, data, selected, height, width }: NodeProps<VulkanNode>) {
    return (
        <WorkflowNode
            id={id}
            selected={selected}
            data={data}
            height={height}
            width={width}
        ></WorkflowNode>
    );
}
