"use client";

import { useRouter } from "next/navigation";
import { Undo2 } from "lucide-react";

export type InnerNavbarSectionProps = {
    key?: string;
    value?: string;
    element?: React.ReactNode;
};

export function InnerNavbar({
    backRoute,
    sections,
    rightSections,
}: {
    backRoute?: string;
    sections: InnerNavbarSectionProps[];
    rightSections?: InnerNavbarSectionProps[];
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
        <div className="flex flex-row border-b-2 justify-between">
            <div className="flex flex-row gap-4 h-full">
                <div
                    onClick={handleBackClick}
                    className="flex flex-row px-6 border-r-2 items-center cursor-pointer"
                >
                    <Undo2 />
                </div>
                {sections.map((section) => renderSection(section))}
            </div>
            <div className="px-6">{rightSections?.map((section) => renderSection(section))}</div>
        </div>
    );
}

function renderSection(section: InnerNavbarSectionProps) {
    return (
        <div className="flex py-4 gap-2 items-center" key={section.key}>
            {section.key && <h1 className="text-base text-wrap font-semibold">{section.key}</h1>}
            {section.element ? <div className="flex items-center">{section.element}</div> : null}
            {section.value && section.value.length > 0 && (
                <h1 className="text-base text-wrap font-normal">{section.value}</h1>
            )}
        </div>
    );
}
