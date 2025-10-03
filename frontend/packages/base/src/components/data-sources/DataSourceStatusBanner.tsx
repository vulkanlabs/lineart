"use client";

import { AlertCircle, CheckCircle, XCircle } from "lucide-react";
import type { DataSource } from "@vulkanlabs/client-open";
import { Alert, AlertDescription, AlertTitle } from "../ui";

type DataSourceStatus = "not_ready" | "ready" | "ready_tested";

interface DataSourceStatusBannerProps {
    dataSource: DataSource;
}

/**
 * Determines the status of a data source based on its configuration
 * - not_ready: URL is placeholder or not configured
 * - ready: URL is configured but not tested
 * - ready_tested: URL is configured and has been tested (future enhancement)
 */
function getDataSourceStatus(dataSource: DataSource): DataSourceStatus {
    const url = dataSource.source?.url || "";
    const isPlaceholder =
        !url ||
        url === "https://placeholder.example.com" ||
        url.includes("placeholder") ||
        url.includes("example.com");

    if (isPlaceholder) return "not_ready";

    // TODO: Check if data source has been tested (requires backend)
    // For now, return 'ready' if URL is configured
    return "ready";
}

/**
 * Status banner component that displays the current state of a data source
 */
export function DataSourceStatusBanner({ dataSource }: DataSourceStatusBannerProps) {
    const status = getDataSourceStatus(dataSource);

    if (status === "not_ready")
        return (
            <Alert variant="destructive">
                <XCircle className="h-4 w-4" />
                <AlertTitle>Not Ready for Use</AlertTitle>
                <AlertDescription>
                    This data source is not ready for use. Please configure the URL and other
                    required settings in the HTTP Configuration section below.
                </AlertDescription>
            </Alert>
        );

    if (status === "ready") 
        return (
            <Alert variant="default" className="border-yellow-500 text-yellow-700">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Ready (Not Tested)</AlertTitle>
                <AlertDescription>
                    This data source is configured but has not been tested yet. Go to the Test tab
                    to verify it works correctly before using it in workflows.
                </AlertDescription>
            </Alert>
        );

    // status === "ready_tested"
    return (
        <Alert variant="default" className="border-green-500 text-green-700">
            <CheckCircle className="h-4 w-4" />
            <AlertTitle>Ready for Use</AlertTitle>
            <AlertDescription>
                This data source is configured and has been successfully tested. It&apos;s ready to
                be used in your workflows.
            </AlertDescription>
        </Alert>
    );
}
