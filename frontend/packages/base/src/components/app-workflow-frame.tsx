"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import "@xyflow/react/dist/style.css";

import {
    WorkflowFrame,
    WorkflowApiProvider,
    WorkflowDataProvider,
    createWorkflowApiClient,
    type Workflow,
} from "../workflow";

/**
 * Configuration for app-specific workflow frame behavior
 */
export interface AppWorkflowFrameConfig {
    /** Whether policyId is required for multi-tenant environments */
    requirePolicyId?: boolean;
    /** Whether to pass projectId to WorkflowFrame component */
    passProjectIdToFrame?: boolean;
}

/**
 * Base props that both apps use
 */
interface BaseAppWorkflowFrameProps {
    workflowData: Workflow;
    onNodeClick?: (e: React.MouseEvent, node: any) => void;
    onPaneClick?: (e: React.MouseEvent) => void;
    config?: AppWorkflowFrameConfig;
}

/**
 * Basic workflow frame props (projectId optional, no policyId)
 */
export interface BasicWorkflowFrameProps extends BaseAppWorkflowFrameProps {
    projectId?: string;
}

/**
 * Enterprise workflow frame props (projectId and policyId required)
 */
export interface EnterpriseWorkflowFrameProps extends BaseAppWorkflowFrameProps {
    projectId: string;
    policyId: string;
}

/**
 * Union type for all possible props
 */
export type AppWorkflowFrameProps = BasicWorkflowFrameProps | EnterpriseWorkflowFrameProps;

/**
 * Type guard to check if props include policyId (enterprise mode)
 */
function isEnterpriseProps(props: AppWorkflowFrameProps): props is EnterpriseWorkflowFrameProps {
    return 'policyId' in props && typeof props.policyId === 'string';
}

/**
 * Configurable application workflow frame that adapts to different deployment modes
 */
export function AppWorkflowFrame(props: AppWorkflowFrameProps) {
    const {
        workflowData,
        onNodeClick = () => {},
        onPaneClick = () => {},
        config = {},
    } = props;
    
    const { requirePolicyId = false, passProjectIdToFrame = false } = config;
    
    const router = useRouter();
    const apiClient = createWorkflowApiClient();
    const handleRefresh = () => router.refresh();
    const handleToast = (message: string, options?: any) => toast(message, options);

    // Extract projectId and policyId based on props type
    const projectId = 'projectId' in props ? props.projectId : undefined;
    const policyId = isEnterpriseProps(props) ? props.policyId : undefined;

    // Validate required fields based on config
    if (requirePolicyId && !policyId) {
        console.error('AppWorkflowFrame: policyId is required when requirePolicyId is true');
    }

    return (
        <WorkflowApiProvider client={apiClient} config={{}}>
            <WorkflowDataProvider
                autoFetch={true}
                includeArchived={false}
                projectId={projectId}
                {...(policyId && { policyId })}
            >
                <WorkflowFrame
                    workflow={workflowData}
                    onNodeClick={onNodeClick}
                    onPaneClick={onPaneClick}
                    toast={handleToast}
                    onRefresh={handleRefresh}
                    {...(passProjectIdToFrame && projectId && { projectId })}
                />
            </WorkflowDataProvider>
        </WorkflowApiProvider>
    );
}