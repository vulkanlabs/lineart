"use server";

import { type RunData, type RunLogs } from "@vulkanlabs/client-open";
import { runsApi, withErrorHandling } from "./client";

/**
 * Get detailed run data and results
 * @param {string} runId - Unique run identifier
 * @returns {Promise<RunData>} Complete run data including inputs, outputs, metrics, status
 *
 * Run status, input data, output results, execution metadata
 */
export const fetchRunData = async (runId: string): Promise<RunData> => {
    return withErrorHandling(runsApi.getRunData({ runId }), `fetch data for run ${runId}`);
};

/**
 * Get execution logs for a run
 * @param {string} runId - Run identifier to get logs for
 * @returns {Promise<RunLogs>} Log entries with timestamps, levels, and messages
 */
export const fetchRunLogs = async (runId: string): Promise<RunLogs> => {
    return withErrorHandling(runsApi.getRunLogs({ runId }), `fetch logs for run ${runId}`);
};
