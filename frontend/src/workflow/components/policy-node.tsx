import { useCallback } from "react";
import { useShallow } from "zustand/react/shallow";

import { Input } from "@/components/ui/input";

import { useWorkflowStore } from "../store";
import { WorkflowNode } from "./base";
import { NodeProps } from "@xyflow/react";
import { VulkanNode } from "../types";

export function PolicyNode({ id, data, selected, height, width }: NodeProps<VulkanNode>) {
    const { updateNodeData } = useWorkflowStore(
        useShallow((state) => ({
            updateNodeData: state.updateNodeData,
        })),
    );

    const setPolicyVersionID = useCallback(
        (policy_id: string) => {
            updateNodeData(id, { ...data, metadata: { policy_id: policy_id } });
        },
        [id, data, updateNodeData],
    );

    return (
        <WorkflowNode id={id} selected={selected} data={data} height={height} width={width}>
            <div className="flex flex-col gap-1 space-y-2 p-3">
                <span>Policy Version ID:</span>
                <Input
                    type="text"
                    value={data.metadata?.policy_id}
                    onChange={(e) => setPolicyVersionID(e.target.value)}
                />
            </div>
        </WorkflowNode>
    );
}
