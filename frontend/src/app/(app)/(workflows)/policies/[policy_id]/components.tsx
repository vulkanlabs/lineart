"use client";
import { GitCompare, FlaskConical, GitBranch, ChartColumnStacked, Layers } from "lucide-react";

import { SidebarSectionProps, PageLayout } from "@/components/page-layout";
import { InnerNavbarSectionProps, InnerNavbar } from "@/components/inner-navbar";

export function RouteLayout({ policy, children }) {
    const sections: SidebarSectionProps[] = [
        {
            name: "Versions",
            icon: GitBranch,
            path: `/policies/${policy.policy_id}/versions`,
        },
        {
            name: "Runs",
            icon: Layers,
            path: `/policies/${policy.policy_id}/runs`,
        },
        {
            name: "Backtests",
            icon: GitCompare,
            path: `/policies/${policy.policy_id}/backtests`,
        },
        {
            name: "Experiments",
            icon: FlaskConical,
            path: `/policies/${policy.policy_id}/experiments`,
            disabled: true,
        },
        {
            name: "Metrics",
            icon: ChartColumnStacked,
            path: `/policies/${policy.policy_id}/metrics`,
            disabled: true,
        },
    ];
    const innerNavbarSections: InnerNavbarSectionProps[] = [
        { key: "Policy:", value: policy.name },
    ];
    return (
        <div className="flex flex-col w-full h-full">
            <InnerNavbar backRoute="/policies" sections={innerNavbarSections} />
            <PageLayout sidebar={{ sections, retractable: true }} content={{ scrollable: true }}>
                {children}
            </PageLayout>
        </div>
    );
}
