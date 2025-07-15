"use client";

import type { PolicyVersion } from "@vulkanlabs/client-open";
import { WorkflowFrame } from "./workflow-frame";

/**
 * Simple wrapper component for the workflow page
 */
export default function WorkflowPage({ policyVersion }: { policyVersion: PolicyVersion }) {
    return <WorkflowFrame workflowData={policyVersion} />;
}
