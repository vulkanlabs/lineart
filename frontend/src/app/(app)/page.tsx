"use client";
import { SidebarSectionProps, PageLayout } from "@/components/page-layout";
import { Network, CreditCard, Shield } from "lucide-react";

export default function Page() {
    const sections: SidebarSectionProps[] = [
        {
            name: "Billing",
            icon: CreditCard,
            path: "/billing",
            disabled: true,
        },
        {
            name: "IAM",
            icon: Shield,
            path: "/iam",
            disabled: true,
        },
        {
            name: "Workflows",
            icon: Network,
            path: "/policies",
        }
    ];
    return (
        <PageLayout sidebarSections={sections}>
            <div>
                <h1>Home</h1>
                <p>Welcome to the Home page</p>
            </div>
        </PageLayout>
    );
}
