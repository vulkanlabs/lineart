'use client';
import Link from "next/link";
import { ChevronRightIcon, ChevronLeftIcon, Users2, Code2, ListTree } from "lucide-react";

import { createContext, useContext, useEffect, useState } from 'react';
import { Button } from "@/components/ui/button";
import { usePathname } from "next/navigation";
import { fetchPolicies, fetchPolicy } from "@/lib/api";


const SidebarContext = createContext();

export default function Sidebar() {
    const [isOpen, setIsOpen] = useState(true);
    const pathname = usePathname();

    return (
        <SidebarContext.Provider value={{ isOpen }}>
            <div className="flex flex-col border-r-2 gap-4 w-64 max-w-64 h-full overflow-auto">
                {/* <Button
                    onClick={() => setIsOpen(!isOpen)}
                    className="justify-start w-12 rounded-full"
                >
                    {isOpen ? <ChevronLeftIcon /> : <ChevronRightIcon />}
                </Button> */}
                <div className="mt-4 ml-2">
                    {chooseNavBar(pathname)}
                </div>
            </div>
        </SidebarContext.Provider>
    );
}

function chooseNavBar(pathname) {
    if (pathname.startsWith("/policies")) {
        return <PoliciesSidebarNav />;
    }
    return <SidebarNav />;
}

function SidebarNav() {
    const { isOpen } = useContext(SidebarContext);

    const sections = [
        { name: "Times", path: "/teams", icon: Users2 },
        { name: "Componentes", path: "/components", icon: Code2 },
        { name: "Políticas", path: "/policies", icon: ListTree },
    ];

    return (
        <div className="flex flex-col gap-4 mt-1">
            {sections.map((section) => (
                <Link
                    key={section.name}
                    href={section.path}
                    className="flex mx-2 gap-2 hover:font-semibold"
                >
                    <section.icon />
                    <span className={isOpen ? "ease-in" : "hidden"}>{section.name}</span>
                </Link>
            ))}
        </div>
    );
}

function PoliciesSidebarNav() {
    const { isOpen } = useContext(SidebarContext);
    const [policies, setPolicies] = useState([]);
    const [currentPolicy, setCurrentPolicy] = useState(null);

    const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
    const pathname = usePathname();

    useEffect(() => {
        // TODO: This will be used to construct the policies list in the
        // sidebar. We should evaluate whether to keep it there.
        fetchPolicies(serverUrl)
            .then((data) => {
                const policyData = data.map((policy) => {
                    return [policy.name, `/policies/${policy.policy_id}`];
                });
                setPolicies(policyData);
            })
            .catch((error) => { console.error("Error fetching policies", error); });

        const policyId = extractPolicyId(pathname);
        if (policyId !== null) {
            fetchPolicy(serverUrl, policyId).then((data) => {
                setCurrentPolicy(data);
            });
        } else {
            setCurrentPolicy(null);
        }
    }, [pathname, serverUrl]);

    const sections = [
        {
            "name": "Monitoramento",
            "children": [],
        },
        {
            "name": "Componentes",
            "children": [],
        },
    ];

    return (
        <div className="flex flex-col gap-4 mt-1">
            <div className="pb-4 border-b-2 ">
                <h1 className="text-xl text-wrap font-semibold ml-2">
                    {currentPolicy == null ? "Políticas" : currentPolicy.name}
                </h1>
            </div>
            {sections.map((section) => (
                <div>
                    <h2 className="text-base text-clip ml-4 hover:font-semibold">{section.name}</h2>
                </div>
            ))}
        </div>
    );
};

function extractPolicyId(path) {
    if (!path.startsWith("/policies/")) {
        return null;
    }
    const parts = path.split("/");
    if (parts.length < 3) {
        return null;
    }
    return parts[2];
}