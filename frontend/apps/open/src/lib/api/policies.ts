"use server";

import {
    type Policy,
    type PolicyVersion,
    type PolicyBase,
    type PolicyCreate,
    type PolicyVersionBase,
    type PolicyVersionUpdate,
    type PolicyAllocationStrategy,
    type ConfigurationVariablesBase,
    type Run,
} from "@vulkanlabs/client-open";

import { policiesApi, policyVersionsApi, withErrorHandling } from "./client";
import type { DateRange, MetricsData, RunsResponse } from "./types";

// Policy CRUD operations

/**
 * Fetch all policies with optional archived filter
 * @param {boolean} [includeArchived=false] - Whether to include archived policies in results
 * @returns {Promise<Policy[]>} Array of policy objects
 */
export const fetchPolicies = async (includeArchived = false): Promise<Policy[]> => {
    return withErrorHandling(policiesApi.listPolicies({ includeArchived }), "fetch policies");
};

/**
 * Fetch a single policy by ID
 * @param {string} policyId - The unique identifier of the policy
 * @returns {Promise<Policy>} Single policy object with all details
 */
export const fetchPolicy = async (policyId: string): Promise<Policy> => {
    return withErrorHandling(policiesApi.getPolicy({ policyId }), `fetch policy ${policyId}`);
};

/**
 * Create a new policy
 * @param {PolicyCreate} data - Policy creation data (name, description, etc.)
 * @returns {Promise<Policy>} The newly created policy with generated ID and timestamps
 */
export const createPolicy = async (data: PolicyCreate): Promise<Policy> => {
    return withErrorHandling(policiesApi.createPolicy({ policyCreate: data }), "create policy");
};

/**
 * Delete a policy (usually marks as archived)
 * @param {string} policyId - ID of the policy to delete
 * @returns {Promise<void>} Nothing on success
 */
export const deletePolicy = async (policyId: string): Promise<void> => {
    return withErrorHandling(policiesApi.deletePolicy({ policyId }), `delete policy ${policyId}`);
};

/**
 * Update policy allocation strategy (how resources are distributed)
 * @param {string} policyId - Target policy ID
 * @param {PolicyAllocationStrategy} data - New allocation strategy configuration
 * @returns {Promise<Policy>} Updated policy object
 */
export const updatePolicyAllocationStrategy = async (
    policyId: string,
    data: PolicyAllocationStrategy,
): Promise<Policy> => {
    const policyBase: PolicyBase = {
        allocation_strategy: data,
    };
    return withErrorHandling(
        policiesApi.updatePolicy({ policyId, policyBase }),
        `update allocation strategy for policy ${policyId}`,
    );
};

// Policy Version operations

/**
 * Create a new version of an existing policy
 * @param {PolicyVersionBase} data - Version data including policy_id, version number, config
 * @returns {Promise<PolicyVersion>} The newly created policy version
 */
export const createPolicyVersion = async (data: PolicyVersionBase): Promise<PolicyVersion> => {
    return withErrorHandling(
        policyVersionsApi.createPolicyVersion({ policyVersionBase: data }),
        "create policy version",
    );
};

/**
 * Update an existing policy version
 * @param {string} policyVersionId - Version ID to update
 * @param {PolicyVersionUpdate} data - Updated version data (config, workflow, etc.)
 * @returns {Promise<PolicyVersion>} Updated policy version object
 */
export const updatePolicyVersion = async (
    policyVersionId: string,
    data: PolicyVersionUpdate,
): Promise<PolicyVersion> => {
    return withErrorHandling(
        policyVersionsApi.updatePolicyVersion({ policyVersionId, policyVersionUpdate: data }),
        `update policy version ${policyVersionId}`,
    );
};

/**
 * Delete a policy version
 * @param {string} policyVersionId - Version ID to delete
 * @returns {Promise<void>} Success or throws error
 */
export const deletePolicyVersion = async (policyVersionId: string): Promise<void> => {
    return withErrorHandling(
        policyVersionsApi.deletePolicyVersion({ policyVersionId }),
        `delete policy version ${policyVersionId}`,
    );
};

/**
 * Fetch policy versions with filtering options
 * @param {string|null} [policyId=null] - Filter by specific policy ID, or null for all
 * @param {boolean} [includeArchived=false] - Include archived/deleted versions
 * @returns {Promise<PolicyVersion[]>} Array of policy versions
 *
 * Pass policyId to get versions for one policy, null for all versions
 */
export const fetchPolicyVersions = async (
    policyId: string | null = null,
    includeArchived = false,
): Promise<PolicyVersion[]> => {
    return withErrorHandling(
        policyVersionsApi.listPolicyVersions({
            policyId: policyId || undefined,
            includeArchived: includeArchived,
        }),
        "fetch policy versions",
    );
};

/**
 * Get detailed info for a specific policy version
 * @param {string} policyVersionId - Unique version identifier
 * @returns {Promise<PolicyVersion>} Complete version details with workflow, config, metadata
 *
 * Workflow definition, deployment info, run history, configuration
 */
export const fetchPolicyVersion = async (policyVersionId: string): Promise<PolicyVersion> => {
    return withErrorHandling(
        policyVersionsApi.getPolicyVersion({ policyVersionId }),
        `fetch policy version ${policyVersionId}`,
    );
};

export const fetchPolicyVersionVariables = async (policyVersionId: string) => {
    return withErrorHandling(
        policyVersionsApi.listConfigVariables({ policyVersionId }),
        `fetch variables for policy version ${policyVersionId}`,
    );
};

export const fetchPolicyVersionDataSources = async (policyVersionId: string) => {
    return withErrorHandling(
        policyVersionsApi.listDataSourcesByPolicyVersion({ policyVersionId }),
        `fetch data sources for policy version ${policyVersionId}`,
    );
};

export const setPolicyVersionVariables = async (
    policyVersionId: string,
    variables: ConfigurationVariablesBase[],
) => {
    return withErrorHandling(
        policyVersionsApi.setConfigVariables({
            policyVersionId,
            configurationVariablesBase: variables,
        }),
        `set variables for policy version ${policyVersionId}`,
    );
};

// Runs operations (from api.ts)
export const fetchPolicyRuns = async (
    policyId: string,
    startDate: Date,
    endDate: Date,
): Promise<Run[]> => {
    return withErrorHandling(
        policiesApi.listRunsByPolicy({ policyId, startDate, endDate }),
        `fetch runs for policy ${policyId}`,
    );
};

export const fetchPolicyVersionRuns = async (
    policyVersionId: string,
    startDate: Date,
    endDate: Date,
): Promise<Run[]> => {
    return withErrorHandling(
        policyVersionsApi.listRunsByPolicyVersion({
            policyVersionId,
            startDate,
            endDate,
        }),
        `fetch runs for policy version ${policyVersionId}`,
    );
};

// Metrics operations (from api.ts)
export const fetchRunsCount = async (
    policyId: string,
    startDate: Date,
    endDate: Date,
    versions: string[] = [],
): Promise<any> => {
    return withErrorHandling(
        policiesApi.runsByPolicy({
            policyId,
            startDate,
            endDate,
            bodyRunsByPolicy: { versions },
        }),
        `fetch runs count for policy ${policyId}`,
    );
};

export const fetchRunOutcomes = async (
    policyId: string,
    startDate: Date,
    endDate: Date,
    versions: string[] = [],
): Promise<any> => {
    return withErrorHandling(
        policiesApi.runsOutcomesByPolicy({
            policyId,
            startDate,
            endDate,
            bodyRunsOutcomesByPolicy: { versions },
        }),
        `fetch run outcomes for policy ${policyId}`,
    );
};

// Updated version for policy metrics component
export const fetchRunOutcomesForMetrics = async ({
    policyId,
    dateRange,
    versions,
    projectId,
}: {
    policyId: string;
    dateRange: DateRange;
    versions: string[];
    projectId?: string;
}): Promise<{ runOutcomes: any[] }> => {
    try {
        // Handle potentially undefined dates
        if (!dateRange.from || !dateRange.to) {
            return { runOutcomes: [] };
        }

        const outcomes = await fetchRunOutcomes(policyId, dateRange.from, dateRange.to, versions);
        return { runOutcomes: Array.isArray(outcomes) ? outcomes : [] };
    } catch (error) {
        console.error("Failed to load policy run outcomes:", error);
        return { runOutcomes: [] };
    }
};

export const fetchRunDurationStats = async (
    policyId: string,
    startDate: Date,
    endDate: Date,
    versions: string[] = [],
): Promise<any> => {
    return withErrorHandling(
        policiesApi.runDurationStatsByPolicy({
            policyId,
            startDate,
            endDate,
            bodyRunDurationStatsByPolicy: { versions },
        }),
        `fetch run duration stats for policy ${policyId}`,
    );
};

export const fetchRunDurationByStatus = async (
    policyId: string,
    startDate: Date,
    endDate: Date,
    versions: string[] = [],
): Promise<any> => {
    return withErrorHandling(
        policiesApi.runDurationStatsByPolicyStatus({
            policyId,
            startDate,
            endDate,
            bodyRunDurationStatsByPolicyStatus: { versions },
        }),
        `fetch run duration by status for policy ${policyId}`,
    );
};

// Additional wrapper functions matching api-client.ts interface (only the unique ones)

/**
 * Fetch comprehensive metrics for a policy
 * @param {Object} params - Metrics configuration
 * @param {string} params.policyId - Which policy you want metrics for
 * @param {DateRange} params.dateRange - Time period with from/to dates
 * @param {string[]} params.versions - Specific versions to include (empty = all versions)
 * @returns {Promise<MetricsData>} Object containing run counts, error rates, duration stats
 */
export async function fetchPolicyMetrics({
    policyId,
    dateRange,
    versions,
    projectId,
}: {
    policyId: string;
    dateRange: DateRange;
    versions: string[];
    projectId?: string;
}): Promise<MetricsData> {
    try {
        // Handle potentially undefined dates
        if (!dateRange.from || !dateRange.to) {
            return {
                runsCount: [],
                errorRate: [],
                runDurationStats: [],
                runDurationByStatus: [],
            };
        }

        const [runsCount, errorRate, runDurationStats, runDurationByStatus] = await Promise.all([
            fetchRunsCount(policyId, dateRange.from, dateRange.to, versions),
            fetchRunOutcomes(policyId, dateRange.from, dateRange.to, versions), // Use for error rate calculation
            fetchRunDurationStats(policyId, dateRange.from, dateRange.to, versions),
            fetchRunDurationByStatus(policyId, dateRange.from, dateRange.to, versions),
        ]);

        return {
            runsCount: Array.isArray(runsCount) ? runsCount : [],
            errorRate: Array.isArray(errorRate) ? errorRate : [],
            runDurationStats: Array.isArray(runDurationStats) ? runDurationStats : [],
            runDurationByStatus: Array.isArray(runDurationByStatus) ? runDurationByStatus : [],
        };
    } catch (error) {
        console.error("Failed to load policy metrics:", error);
        return {
            runsCount: [],
            errorRate: [],
            runDurationStats: [],
            runDurationByStatus: [],
        };
    }
}

export async function fetchRunsByPolicy({
    resourceId,
    dateRange,
}: {
    resourceId: string;
    dateRange: DateRange;
}): Promise<RunsResponse> {
    try {
        // Handle potentially undefined dates
        if (!dateRange.from || !dateRange.to) {
            return { runs: [] };
        }

        const runs = await fetchPolicyRuns(resourceId, dateRange.from, dateRange.to);
        return { runs: runs || null };
    } catch (error) {
        console.error("Failed to load policy runs:", error);
        return { runs: null };
    }
}

export async function fetchRunsByPolicyVersion({
    resourceId,
    dateRange,
}: {
    resourceId: string;
    dateRange: DateRange;
}): Promise<RunsResponse> {
    try {
        // Handle potentially undefined dates
        if (!dateRange.from || !dateRange.to) {
            return { runs: [] };
        }

        const runs = await fetchPolicyVersionRuns(resourceId, dateRange.from, dateRange.to);
        return { runs: runs || null };
    } catch (error) {
        console.error("Failed to load policy version runs:", error);
        return { runs: null };
    }
}
