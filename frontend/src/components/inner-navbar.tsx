"use client";
import { useRouter } from "next/navigation";
import { Undo2 } from "lucide-react";

export type InnerNavbarSectionProps = {
    key: string;
    value: string;
};

export function InnerNavbar({
    backRoute,
    sections,
}: {
    backRoute?: string;
    sections: InnerNavbarSectionProps[];
}) {
    const router = useRouter();

    function handleBackClick() {
        if (backRoute) {
            router.push(backRoute);
        } else {
            router.back();
        }
    }

    return (
        <div className="border-b-2">
            <div className="flex flex-row gap-4 h-[3.75rem]">
                <div
                    onClick={handleBackClick}
                    className="flex flex-row px-6 border-r-2 items-center cursor-pointer"
                >
                    <Undo2 />
                </div>
                {sections.map((section) => (
                    <div className="flex py-4 gap-2 items-center" key={section.key}>
                        <h1 className="text-base text-wrap font-semibold">{section.key}</h1>
                        <h1 className="text-base text-wrap font-normal">{section.value}</h1>
                    </div>
                ))}
            </div>
        </div>
    );
}
