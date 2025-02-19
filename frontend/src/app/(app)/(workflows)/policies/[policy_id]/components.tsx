"use client";
import { GitCompare, ChartColumnStacked, Settings2, Layers } from "lucide-react";

import { SidebarSectionProps, PageLayout } from "@/components/page-layout";
import { InnerNavbarSectionProps, InnerNavbar } from "@/components/inner-navbar";

export function RouteLayout({ policy, children }) {
    const sections: SidebarSectionProps[] = [
        {
            name: "Overview",
            icon: ChartColumnStacked,
            path: `/policies/${policy.policy_id}/overview`,
        },
        {
            name: "Allocation",
            icon: Settings2,
            path: `/policies/${policy.policy_id}/allocation`,
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
            disabled: true,
        },
    ];
    const innerNavbarSections: InnerNavbarSectionProps[] = [{ key: "Policy:", value: policy.name }];
    return (
        <div className="flex flex-col w-full h-full">
            <InnerNavbar backRoute="/policies" sections={innerNavbarSections} />
            <PageLayout sidebar={{ sections, retractable: true }} content={{ scrollable: true }}>
                {children}
            </PageLayout>
        </div>
    );
}
