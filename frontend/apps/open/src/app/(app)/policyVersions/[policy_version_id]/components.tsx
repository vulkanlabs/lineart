"use client";

// External libraries
import { Layers, Network, FolderCog, Play } from "lucide-react";
import { usePathname } from "next/navigation";

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
    const pathname = usePathname();
    const baseUrl = `/policyVersions/${policyVersion.policy_version_id}`;
    const isOnLauncherPage = pathname.endsWith('/launcher');
    const isOnWorkflowPage = pathname.endsWith('/workflow');
    
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
    
    // Only show LauncherButton when NOT on the launcher page
    const rightSections: InnerNavbarSectionProps[] = isOnLauncherPage ? [] : [
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
            <PageLayout sidebar={{ sections, retractable: true }} content={{ scrollable: !isOnWorkflowPage }}>
                {children}
            </PageLayout>
        </div>
    );
}
