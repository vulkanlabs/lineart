"use client";

import { useEffect } from "react";
import { PolicyVersion } from "@vulkan-server/PolicyVersion";
import { useWorkflowStore } from "@/workflow/store";
import { updateContextData } from "@/lib/context";
import { useShallow } from "zustand/react/shallow";

interface WorkflowContextManagerProps {
    policyVersion: PolicyVersion;
}

export function WorkflowContextManager({ policyVersion }: WorkflowContextManagerProps) {
    const { getSpec } = useWorkflowStore(
        useShallow((state) => ({
            getSpec: state.getSpec,
        })),
    );

    // Update context when component mounts and when workflow changes
    useEffect(() => {
        const currentWorkflowSpec = getSpec();

        updateContextData({
            policyVersion,
            currentWorkflowSpec,
        });
    }, [policyVersion, getSpec]);

    // Update context when workflow spec changes
    useEffect(() => {
        const currentWorkflowSpec = getSpec();

        updateContextData({
            currentWorkflowSpec,
        });
    }, [getSpec]);

    return null; // This component doesn't render anything
}
