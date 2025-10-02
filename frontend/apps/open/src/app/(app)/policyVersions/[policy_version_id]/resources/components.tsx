"use client";

import {
    PolicyResourcesEnvironmentVariables,
    PolicyResourcesDataSourcesTable,
    PolicyResourcesRequirementsEditor,
} from "@vulkanlabs/base/components/policy-versions";
import type { DataSourceReference, PolicyVersion } from "@vulkanlabs/client-open";
import type { EnvironmentVariablesEditorProps } from "@vulkanlabs/base";

// Local imports
import { updatePolicyVersion, setPolicyVersionVariables } from "@/lib/api";

interface EnvironmentVariablesProps {
    policyVersion: PolicyVersion;
    variables: EnvironmentVariablesEditorProps["variables"];
}

export function EnvironmentVariables({ policyVersion, variables }: EnvironmentVariablesProps) {
    return (
        <PolicyResourcesEnvironmentVariables
            config={{
                policyVersion,
                variables,
                setPolicyVersionVariables,
            }}
        />
    );
}

export function DataSourcesTable({ sources }: { sources: DataSourceReference[] }) {
    return (
        <PolicyResourcesDataSourcesTable
            config={{
                sources,
            }}
        />
    );
}

export function RequirementsEditor({ policyVersion }: { policyVersion: PolicyVersion }) {
    return (
        <PolicyResourcesRequirementsEditor
            config={{
                policyVersion,
                updatePolicyVersion,
            }}
        />
    );
}
