"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { z } from "zod";
import "@xyflow/react/dist/style.css";

import {
    WorkflowFrame,
    WorkflowApiProvider,
    WorkflowDataProvider,
    createWorkflowApiClient,
    type Workflow,
} from "../workflow";

/**
 * Configuration schema for runtime validation
 */
const AppWorkflowFrameConfigSchema = z.object({
    /** Whether policyId is required for multi-tenant environments */
    requirePolicyId: z.boolean().optional().default(false),
    /** Whether to pass projectId to WorkflowFrame component */
    passProjectIdToFrame: z.boolean().optional().default(false),
});

/**
 * Global scope configuration - no policy isolation required
 */
export const GLOBAL_SCOPE_CONFIG: AppWorkflowFrameConfig = Object.freeze({
    requirePolicyId: false,
    passProjectIdToFrame: true,
});

/**
 * Project scope configuration - requires policy isolation  
 */
export const PROJECT_SCOPE_CONFIG: AppWorkflowFrameConfig = Object.freeze({
    requirePolicyId: true,
    passProjectIdToFrame: true,
});

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
 * Global scope workflow frame props (no policy isolation)
 */
export interface GlobalScopeWorkflowFrameProps extends BaseAppWorkflowFrameProps {
    projectId?: string;
}

/**
 * Project scope workflow frame props (requires policy isolation)
 */
export interface ProjectScopeWorkflowFrameProps extends BaseAppWorkflowFrameProps {
    projectId: string;
    policyId: string;
}

/**
 * Union type for all possible props
 */
export type AppWorkflowFrameProps = GlobalScopeWorkflowFrameProps | ProjectScopeWorkflowFrameProps;

/**
 * Type guard to check if props include policyId (project scope mode)
 */
function isProjectScopeProps(props: AppWorkflowFrameProps): props is ProjectScopeWorkflowFrameProps {
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
    
    // Validate and parse configuration
    const validatedConfig = AppWorkflowFrameConfigSchema.parse(config);
    const { requirePolicyId, passProjectIdToFrame } = validatedConfig;
    
    const router = useRouter();
    const apiClient = createWorkflowApiClient();
    const handleRefresh = () => router.refresh();
    const handleToast = (message: string, options?: any) => toast(message, options);

    // Extract projectId and policyId based on props type
    const projectId = 'projectId' in props ? props.projectId : undefined;
    const policyId = isProjectScopeProps(props) ? props.policyId : undefined;

    // Validate required fields based on config
    if (requirePolicyId && !policyId) {
        throw new Error('AppWorkflowFrame: policyId is required when requirePolicyId is true');
    }

    return (
        <WorkflowApiProvider client={apiClient} config={{}}>
            <WorkflowDataProvider
                autoFetch={true}
                includeArchived={false}
                projectId={projectId}
                policyId={policyId || undefined}
            >
                <WorkflowFrame
                    workflow={workflowData}
                    onNodeClick={onNodeClick}
                    onPaneClick={onPaneClick}
                    toast={handleToast}
                    onRefresh={handleRefresh}
                    projectId={passProjectIdToFrame && projectId ? projectId : undefined}
                />
            </WorkflowDataProvider>
        </WorkflowApiProvider>
    );
}