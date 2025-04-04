import { useCallback } from "react";
import { useShallow } from "zustand/react/shallow";

import { Input } from "@/components/ui/input";

import { useWorkflowStore } from "../store";
import { WorkflowNode } from "./base";

export function TerminateNode({ id, data, selected, height, width }) {
    const { updateNodeData } = useWorkflowStore(
        useShallow((state) => ({
            updateNodeData: state.updateNodeData,
        })),
    );

    const setReturnStatus = useCallback(
        (status: string) => {
            updateNodeData(id, { ...data, metadata: { return_status: status } });
        },
        [id, data, updateNodeData],
    );

    return (
        <WorkflowNode
            id={id}
            selected={selected}
            data={data}
            height={height}
            width={width}
            isOutput
            notPlayable
        >
            <div className="flex flex-col gap-1 space-y-2 p-3">
                <span>Return status:</span>
                <Input
                    type="text"
                    value={data.metadata?.return_status}
                    onChange={(e) => setReturnStatus(e.target.value)}
                />
            </div>
        </WorkflowNode>
    );
}
