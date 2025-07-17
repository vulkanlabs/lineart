"use client";

import React, { useCallback, useState, useMemo } from "react";
import { useShallow } from "zustand/react/shallow";

import { AssetCombobox, AssetOption } from "@/components/combobox";

import { useWorkflowStore } from "@/workflow/store";
import { useWorkflowData } from "@/workflow/context";
import { StandardWorkflowNode } from "./base";
import type { VulkanNodeProps } from "@/workflow/types/workflow";
import { WorkflowStatus } from "@vulkanlabs/client-open";

/**
 * Policy node component - executes sub-policies within workflow
 */
export function PolicyNode({ id, data, selected, height, width }: VulkanNodeProps) {
    const { updateNodeData } = useWorkflowStore(
        useShallow((state) => ({
            updateNodeData: state.updateNodeData,
        })),
    );

    // Get policy data from WorkflowDataProvider
    const { policyVersions, isPoliciesLoading, policiesError } = useWorkflowData();

    const setPolicyVersionID = useCallback(
        (policy_id: string) => {
            updateNodeData(id, { ...(data || {}), metadata: { policy_id: policy_id } });
        },
        [id, data, updateNodeData],
    );

    const [selectedPolicy, setSelectedPolicy] = useState(data.metadata?.policy_id || "");

    // Transform policy versions into AssetOption format
    const policyOptions = useMemo<AssetOption[]>(() => {
        return policyVersions
            .filter((version) => version.workflow?.status === WorkflowStatus.Valid)
            .map((version) => ({
                value: version.policy_version_id,
                label: `${version.alias} (${version.policy_version_id.substring(0, 8)})`,
            }));
    }, [policyVersions]);

    return (
        <StandardWorkflowNode id={id} selected={selected} data={data} height={height} width={width}>
            <div className="flex flex-col gap-4 p-4">
                <span>Policy Version:</span>
                {policiesError ? (
                    <div className="text-sm text-red-600 p-2 bg-red-50 rounded">
                        Error loading policies: {policiesError}
                    </div>
                ) : (
                    <AssetCombobox
                        options={policyOptions}
                        value={selectedPolicy}
                        onChange={(value: string) => {
                            setSelectedPolicy(value);
                            setPolicyVersionID(value);
                            updateNodeData(id, { ...(data || {}), metadata: { policy_id: value } });
                        }}
                        placeholder="Select a policy..."
                        searchPlaceholder="Search policies..."
                        isLoading={isPoliciesLoading}
                        emptyMessage={
                            isPoliciesLoading ? "Loading policies..." : "No valid policies found."
                        }
                    />
                )}
            </div>
        </StandardWorkflowNode>
    );
}
