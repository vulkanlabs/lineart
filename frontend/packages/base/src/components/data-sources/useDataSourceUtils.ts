import { useState } from "react";
import type { DataSource } from "@vulkanlabs/client-open";

export function useDataSourceUtils() {
    const [copiedField, setCopiedField] = useState<string | null>(null);

    const copyToClipboard = (text: string, field: string) => {
        navigator.clipboard.writeText(text);
        setCopiedField(field);
        setTimeout(() => setCopiedField(null), 2000);
    };

    const getFullDataSourceJson = (dataSource: DataSource) => {
        return JSON.stringify(dataSource, null, 2);
    };

    const formatDate = (date: Date) => {
        return new Date(date).toLocaleDateString(undefined, {
            year: "numeric",
            month: "long",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        });
    };

    const formatTimeFromSeconds = (totalSeconds: number) => {
        const days = Math.floor(totalSeconds / 86400);
        const hours = Math.floor((totalSeconds % 86400) / 3600);
        const minutes = Math.floor((totalSeconds % 3600) / 60);
        const seconds = totalSeconds % 60;

        const parts = [];
        if (days > 0) parts.push(`${days} day${days !== 1 ? "s" : ""}`);
        if (hours > 0) parts.push(`${hours} hour${hours !== 1 ? "s" : ""}`);
        if (minutes > 0) parts.push(`${minutes} minute${minutes !== 1 ? "s" : ""}`);
        if (seconds > 0 || parts.length === 0)
            parts.push(`${seconds} second${seconds !== 1 ? "s" : ""}`);

        return parts.join(", ");
    };

    const formatJson = (json: any) => {
        if (!json) return null;
        return JSON.stringify(json, null, 2);
    };

    return {
        copiedField,
        copyToClipboard,
        getFullDataSourceJson,
        formatDate,
        formatTimeFromSeconds,
        formatJson,
    };
}
