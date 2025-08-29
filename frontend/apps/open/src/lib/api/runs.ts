import { RunsApi, type Run, type RunData, type RunLogs } from "@vulkanlabs/client-open";
import { apiConfig, withErrorHandling } from "./client";

const runsApi = new RunsApi(apiConfig);

export const fetchRunData = async (runId: string): Promise<RunData> => {
    return withErrorHandling(runsApi.getRunData({ runId }), `fetch data for run ${runId}`);
};

export const fetchRunLogs = async (runId: string): Promise<RunLogs> => {
    return withErrorHandling(runsApi.getRunLogs({ runId }), `fetch logs for run ${runId}`);
};
