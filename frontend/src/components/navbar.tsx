"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { VulkanLogo } from "@/components/logo";
import { UserButton } from "@stackframe/stack";

export default function Navbar() {
    const pathname = usePathname();
    const isSubpathActive = (path: string) => pathname.startsWith(path);

    const sections = [
        // { name: "Dashboard", path: "/dashboard" },
        { name: "Policies", path: "/policies" },
        { name: "Components", path: "/components" },
        // { name: "Integrações", path: "/integrations" },
    ];

    return (
        <nav className="flex gap-4 text-lg font-medium md:items-center md:gap-5 md:text-sm lg:gap-6 overflow-clip">
            <VulkanLogo />
            {/* {sections.map((section) => (
                <Link key={section.name} href={section.path}
                    className={cn(
                        "flex items-center text-base gap-2 hover:font-bold",
                        isSubpathActive(section.path) ? "font-bold" : "text-muted-foreground"
                    )}>
                    <span>{section.name}</span>
                </Link>
            ))
            } */}
            {/* <div className="absolute right-0 m-8">
                <UserButton
                    showUserInfo={false} 
                />
            </div> */}
        </nav>
    );
}
