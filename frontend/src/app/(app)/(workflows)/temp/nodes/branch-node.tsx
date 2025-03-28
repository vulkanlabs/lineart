import { useCallback } from "react";
import { useShallow } from "zustand/react/shallow";

import { Input } from "@/components/ui/input";

import { useWorkflowStore } from "../store";
import { WorkflowNode } from "./base";


export function BranchNode({ id, data, selected, height, width }) {
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