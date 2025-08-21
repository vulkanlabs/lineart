import {
    ComponentsApi,
    PoliciesApi,
    PolicyVersionsApi,
    RunsApi,
    DataSourcesApi,
    type Policy,
    type PolicyVersion,
    type PolicyBase,
    type PolicyCreate,
    type PolicyVersionCreate,
    type PolicyVersionBase,
    type Run,
    type RunData,
    type RunLogs,
    type DataSource,
    type DataSourceSpec,
    type DataSourceEnvVarBase,
    type PolicyAllocationStrategy,
    type ConfigurationVariablesBase,
    type ComponentBase,
    type Component,
} from "@vulkanlabs/client-open";
import { createApiConfig, withErrorHandling } from "@vulkanlabs/api-utils";

// Configure API clients with shared configuration
const apiConfig = createApiConfig({
    baseUrl: process.env.NEXT_PUBLIC_VULKAN_SERVER_URL!,
    headers: {
        "Content-Type": "application/json",
    },
});

// Create API client instances
const policiesApi = new PoliciesApi(apiConfig);
const policyVersionsApi = new PolicyVersionsApi(apiConfig);
const runsApi = new RunsApi(apiConfig);
const dataSourcesApi = new DataSourcesApi(apiConfig);
const componentsApi = new ComponentsApi(apiConfig);

// Policy API methods with error handling
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

// Policy Version API methods
export const createPolicyVersion = async (data: PolicyVersionCreate): Promise<PolicyVersion> => {
    return withErrorHandling(
        policyVersionsApi.createPolicyVersion({ policyVersionCreate: data }),
        "create policy version",
    );
};

export const updatePolicyVersion = async (
    policyVersionId: string,
    data: PolicyVersionBase,
): Promise<PolicyVersion> => {
    return withErrorHandling(
        policyVersionsApi.updatePolicyVersion({ policyVersionId, policyVersionBase: data }),
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

// Run API methods
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

export const fetchRun = async (runId: string): Promise<Run> => {
    return withErrorHandling(runsApi.getRun({ runId }), `fetch run ${runId}`);
};

export const fetchRunData = async (runId: string): Promise<RunData> => {
    return withErrorHandling(runsApi.getRunData({ runId }), `fetch data for run ${runId}`);
};

export const fetchRunLogs = async (runId: string): Promise<RunLogs> => {
    return withErrorHandling(runsApi.getRunLogs({ runId }), `fetch logs for run ${runId}`);
};

// Data Source API methods
export const fetchDataSources = async (): Promise<DataSource[]> => {
    return withErrorHandling(dataSourcesApi.listDataSources(), "fetch data sources");
};

export const fetchDataSource = async (dataSourceId: string): Promise<DataSource> => {
    return withErrorHandling(
        dataSourcesApi.getDataSource({ dataSourceId }),
        `fetch data source ${dataSourceId}`,
    );
};

export const createDataSource = async (data: DataSourceSpec) => {
    return withErrorHandling(
        dataSourcesApi.createDataSource({ dataSourceSpec: data }),
        "create data source",
    );
};

export const deleteDataSource = async (dataSourceId: string) => {
    return withErrorHandling(
        dataSourcesApi.deleteDataSource({ dataSourceId }),
        `delete data source ${dataSourceId}`,
    );
};

export const fetchDataSourceEnvVars = async (dataSourceId: string) => {
    return withErrorHandling(
        dataSourcesApi.getDataSourceEnvVariables({ dataSourceId }),
        `fetch environment variables for data source ${dataSourceId}`,
    );
};

export const setDataSourceEnvVars = async (
    dataSourceId: string,
    variables: DataSourceEnvVarBase[],
) => {
    return withErrorHandling(
        dataSourcesApi.setDataSourceEnvVariables({
            dataSourceId,
            dataSourceEnvVarBase: variables,
        }),
        `set environment variables for data source ${dataSourceId}`,
    );
};

// Component API functions
export async function fetchComponents(includeArchived: boolean = false): Promise<Component[]> {
    return withErrorHandling(
        componentsApi.listComponents({ includeArchived: includeArchived }),
        `fetch components`,
    );
}

export async function fetchComponent(componentId: string): Promise<Component> {
    return withErrorHandling(
        componentsApi.getComponent({ componentId }),
        `fetch component ${componentId}`,
    );
}

export async function createComponent(data: ComponentBase): Promise<Component> {
    return withErrorHandling(
        componentsApi.createComponent({ componentBase: data }),
        `create component`,
    );
}

export async function updateComponent(
    componentName: string,
    data: ComponentBase,
): Promise<Component> {
    return withErrorHandling(
        componentsApi.updateComponent({ componentName, componentBase: data }),
        `update component ${componentName}`,
    );
}

export async function deleteComponent(componentName: string): Promise<void> {
    return withErrorHandling(
        componentsApi.deleteComponent({ componentName }),
        `delete component ${componentName}`,
    );
}

// Data Source Usage API method
export const fetchDataSourceUsage = async (
    dataSourceId: string,
    startDate: Date,
    endDate: Date,
): Promise<any> => {
    return withErrorHandling(
        dataSourcesApi.getDataSourceUsage({
            dataSourceId,
            startDate,
            endDate,
        }),
        `fetch usage for data source ${dataSourceId}`,
    );
};

// Data Source Metrics API method
export const fetchDataSourceMetrics = async (
    dataSourceId: string,
    startDate: Date,
    endDate: Date,
): Promise<any> => {
    return withErrorHandling(
        dataSourcesApi.getDataSourceMetrics({
            dataSourceId,
            startDate,
            endDate,
        }),
        `fetch metrics for data source ${dataSourceId}`,
    );
};

// Data Source Cache Stats API method
export const fetchDataSourceCacheStats = async (
    dataSourceId: string,
    startDate: Date,
    endDate: Date,
): Promise<any> => {
    return withErrorHandling(
        dataSourcesApi.getCacheStatistics({
            dataSourceId,
            startDate,
            endDate,
        }),
        `fetch cache statistics for data source ${dataSourceId}`,
    );
};

// Additional API methods for metrics and analytics using auto-generated clients
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

// Export API client instances for direct use if needed
export { policiesApi, policyVersionsApi, runsApi, dataSourcesApi };

// Re-export additional types for convenience
export type {
    Run,
    RunData,
    RunLogs,
    Policy,
    PolicyVersion,
    PolicyBase,
    PolicyCreate,
    PolicyVersionCreate,
    PolicyVersionBase,
    DataSource,
    DataSourceSpec,
    DataSourceEnvVarBase,
    PolicyAllocationStrategy,
    ConfigurationVariablesBase,
} from "@vulkanlabs/client-open";
