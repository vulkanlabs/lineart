"use client";

import {
    PolicyLauncherPage,
    PolicyLauncherButton,
} from "@vulkanlabs/base/components/policy-versions";
import { policyVersionsApi } from "@/lib/api";

type LauncherPageProps = {
    policyVersionId: string;
    inputSchema: Record<string, string>;
    configVariables?: string[];
};

export function LauncherPage({ policyVersionId, inputSchema, configVariables }: LauncherPageProps) {
    return (
        <PolicyLauncherPage
            config={{
                policyVersionId,
                inputSchema,
                configVariables,
                createRunByPolicyVersion: policyVersionsApi.createRunByPolicyVersion,
            }}
        />
    );
}

export function LauncherButton({
    policyVersionId,
    inputSchema,
    configVariables,
}: LauncherPageProps) {
    return (
        <PolicyLauncherButton
            config={{
                policyVersionId,
                inputSchema,
                configVariables,
                createRunByPolicyVersion: policyVersionsApi.createRunByPolicyVersion,
            }}
        />
    );
}
