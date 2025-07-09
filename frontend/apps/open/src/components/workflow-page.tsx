"use client";

import type { PolicyVersion } from "@vulkan/client-open";
import { AppWorkflowFrame } from "./workflow-frame";

/**
 * Simple wrapper component for the workflow page
 */
export default function WorkflowPage({ policyVersion }: { policyVersion: PolicyVersion }) {
    return <AppWorkflowFrame policyVersion={policyVersion} />;
}
