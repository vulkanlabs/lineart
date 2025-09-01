"use server";

import { type RunData, type RunLogs } from "@vulkanlabs/client-open";
import { runsApi, withErrorHandling } from "./client";

export const fetchRunData = async (runId: string): Promise<RunData> => {
    return withErrorHandling(runsApi.getRunData({ runId }), `fetch data for run ${runId}`);
};

export const fetchRunLogs = async (runId: string): Promise<RunLogs> => {
    return withErrorHandling(runsApi.getRunLogs({ runId }), `fetch logs for run ${runId}`);
};
