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
export const fetchPolicies = async (includeArchived = false): Promise<Policy[]> => {
    return withErrorHandling(policiesApi.listPolicies({ includeArchived }), "fetch policies");
};

export const fetchPolicy = async (policyId: string): Promise<Policy> => {
    return withErrorHandling(policiesApi.getPolicy({ policyId }), `fetch policy ${policyId}`);
};

export const createPolicy = async (data: PolicyCreate): Promise<Policy> => {
    return withErrorHandling(policiesApi.createPolicy({ policyCreate: data }), "create policy");
};

export const deletePolicy = async (policyId: string): Promise<void> => {
    return withErrorHandling(policiesApi.deletePolicy({ policyId }), `delete policy ${policyId}`);
};

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
export const createPolicyVersion = async (data: PolicyVersionBase): Promise<PolicyVersion> => {
    return withErrorHandling(
        policyVersionsApi.createPolicyVersion({ policyVersionBase: data }),
        "create policy version",
    );
};

export const updatePolicyVersion = async (
    policyVersionId: string,
    data: PolicyVersionUpdate,
): Promise<PolicyVersion> => {
    return withErrorHandling(
        policyVersionsApi.updatePolicyVersion({ policyVersionId, policyVersionUpdate: data }),
        `update policy version ${policyVersionId}`,
    );
};

export const deletePolicyVersion = async (policyVersionId: string): Promise<void> => {
    return withErrorHandling(
        policyVersionsApi.deletePolicyVersion({ policyVersionId }),
        `delete policy version ${policyVersionId}`,
    );
};

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
export async function fetchPolicyMetrics({
    policyId,
    dateRange,
    versions,
}: {
    policyId: string;
    dateRange: DateRange;
    versions: string[];
}): Promise<MetricsData> {
    try {
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
        const runs = await fetchPolicyVersionRuns(resourceId, dateRange.from, dateRange.to);
        return { runs: runs || null };
    } catch (error) {
        console.error("Failed to load policy version runs:", error);
        return { runs: null };
    }
}
