"use client";

import { useRouter } from "next/navigation";
import { Undo2 } from "lucide-react";

export function LocalNavbar({ policyData }) {
    const router = useRouter();

    function handleBackClick() {
        router.back();
    }

    return (
        <div className="border-b-2">
            <div className="flex flex-row gap-4">
                <div
                    onClick={handleBackClick}
                    className="flex flex-row px-6 border-r-2 items-center cursor-pointer"
                >
                    <Undo2 />
                </div>
                <div className="flex py-4 gap-2 items-center">
                    <h1 className="text-xl text-wrap font-semibold">Policy:</h1>
                    <h1 className="text-base text-wrap font-normal">{policyData.name}</h1>
                </div>
            </div>
        </div>
    );
}
