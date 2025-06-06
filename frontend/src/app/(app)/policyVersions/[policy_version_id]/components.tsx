"use client";
import { Layers, Network, FolderCog, Play } from "lucide-react";

import { SidebarSectionProps, PageLayout } from "@/components/page-layout";
import { InnerNavbarSectionProps, InnerNavbar } from "@/components/inner-navbar";
import { LauncherButton } from "./launcher/components";
import { postLaunchFormAction } from "./launcher/actions";

export function RouteLayout({ policy, policyVersion, children }) {
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
        { key: "Policy:", value: policy.name },
        { key: "Version:", value: policyVersion.alias },
        { key: "Status:", value: policyVersion.status },
    ];
    const rightSections: InnerNavbarSectionProps[] = [
        {
            element: (
                <LauncherButton
                    policyVersionId={policyVersion.policy_version_id}
                    inputSchema={null}
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
