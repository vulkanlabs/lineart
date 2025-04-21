"use client";
import { Cable, Webhook } from "lucide-react";

import { SidebarSectionProps, PageLayout } from "@/components/page-layout";

export default function Layout({ children }) {
    const sections: SidebarSectionProps[] = [
        {
            name: "Data Sources",
            icon: Cable,
            path: `/integrations/dataSources`,
        },
        {
            name: "Webhooks",
            icon: Webhook,
            path: `/integrations/webhooks`,
            disabled: true,
        },
    ];
    return (
        <PageLayout sidebar={{ sections, retractable: true }} content={{ scrollable: true }}>
            {children}
        </PageLayout>
    );
}
