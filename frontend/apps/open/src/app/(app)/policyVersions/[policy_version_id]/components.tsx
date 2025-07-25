"use client";

// External libraries
import { Layers, Network, FolderCog, Play } from "lucide-react";

// Local imports
import { InnerNavbar, InnerNavbarSectionProps } from "@/components/inner-navbar";
import { PageLayout, SidebarSectionProps } from "@/components/page-layout";
import { postLaunchFormAction } from "./launcher/actions";
import { LauncherButton } from "./launcher/components";
import { Policy, PolicyVersion } from "@vulkanlabs/client-open";

export function RouteLayout({
    policy,
    policyVersion,
    children,
}: {
    policy: Policy;
    policyVersion: PolicyVersion;
    children: React.ReactNode;
}) {
    const baseUrl = `/policyVersions/${policyVersion.policy_version_id}`;
    const sections: SidebarSectionProps[] = [
        {
            name: "Workflow",
            icon: Network,
            path: `${baseUrl}/workflow`,
        },
        {
            name: "Resources",
            icon: FolderCog,
            path: `${baseUrl}/resources`,
        },
        {
            name: "Runs",
            icon: Layers,
            path: `${baseUrl}/runs`,
        },
        {
            name: "Launcher",
            icon: Play,
            path: `${baseUrl}/launcher`,
        },
    ];

    const innerNavbarSections: InnerNavbarSectionProps[] = [
        { key: "Policy:", value: policy.name || "" },
        { key: "Version:", value: policyVersion.alias || "" },
        { key: "Status:", value: policyVersion.workflow?.status || "" },
    ];
    const rightSections: InnerNavbarSectionProps[] = [
        {
            element: (
                <LauncherButton
                    policyVersionId={policyVersion.policy_version_id}
                    inputSchema={new Map()}
                    launchFn={postLaunchFormAction}
                />
            ),
        },
    ];
    return (
        <div className="flex flex-col w-full h-full">
            <InnerNavbar
                backRoute={`/policies/${policy.policy_id}/overview`}
                sections={innerNavbarSections}
                rightSections={rightSections}
            />
            <PageLayout sidebar={{ sections, retractable: true }} content={{ scrollable: true }}>
                {children}
            </PageLayout>
        </div>
    );
}
