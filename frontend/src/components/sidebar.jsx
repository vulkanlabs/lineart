'use client';
import Link from "next/link";
import { ChevronRightIcon, ChevronLeftIcon, Users2, Code2, ListTree } from "lucide-react";

import { createContext, useContext, useEffect, useState } from 'react';
import { Button } from "@/components/ui/button";
import { usePathname } from "next/navigation";
import { fetchPolicies, fetchPolicy } from "@/lib/policies";


const SidebarContext = createContext();

export default function Sidebar() {
    const [isOpen, setIsOpen] = useState(false);
    const pathname = usePathname();

    return (
        <SidebarContext.Provider value={{ isOpen }}>
            <div className="flex flex-col border-r gap-4 w-fit max-w-64 h-full overflow-clip">
                <Button
                    onClick={() => setIsOpen(!isOpen)}
                    className="justify-start w-12 rounded-full"
                >
                    {isOpen ? <ChevronLeftIcon /> : <ChevronRightIcon />}
                </Button>
                {chooseNavBar(pathname)}
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
    let { isOpen } = useContext(SidebarContext);

    return (
        <div className="flex flex-col gap-4 mt-1 ">
            <Link href="/teams" className="flex mx-2 gap-2 hover:font-bold">
                <Users2 />
                <span className={isOpen ? "ease-in" : "hidden"}>Times</span>
            </Link>

            <Link href="/components" className="flex mx-2 gap-2 hover:font-bold">
                <Code2 />
                <span className={isOpen ? "ease-in" : "hidden"}>Componentes</span>
            </Link>

            <Link href="/policies" className="flex mx-2 gap-2 hover:font-bold">
                <ListTree />
                <span className={isOpen ? "ease-in" : "hidden"}>Políticas</span>
            </Link>
        </div>
    );
}

function PoliciesSidebarNav() {
    let { isOpen } = useContext(SidebarContext);
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

        console.log("Pathname", pathname);
        const policyId = extractPolicyId(pathname);

        if (policyId !== null) {
            fetchPolicy(serverUrl, policyId).then((data) => {
                setCurrentPolicy(data);
            });
        } else {
            setCurrentPolicy(null);
        }
    }, [pathname]);

    return (
        <div className="flex flex-col gap-4 mt-1">
            <h2 className="text-lg text-clip font-semibold">
                {currentPolicy == null ? "Políticas" : currentPolicy.name}
            </h2>
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