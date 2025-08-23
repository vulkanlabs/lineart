"use client";

// External libraries
import { ChartColumnStacked, Settings2, Layers } from "lucide-react";

// Local imports
import { InnerNavbar, type InnerNavbarSectionProps } from "@vulkanlabs/base";
import { PageLayout, SidebarSectionProps } from "@/components/page-layout";
import { Policy } from "@vulkanlabs/client-open";

export function RouteLayout({ policy, children }: { policy: Policy; children: React.ReactNode }) {
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
    ];
    const innerNavbarSections: InnerNavbarSectionProps[] = [
        { key: "Policy:", value: policy.name || "" },
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
