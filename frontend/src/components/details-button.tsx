import Link from "next/link";

import { Button } from "@/components/ui/button";
import { LucideMousePointerClick } from "lucide-react";

export function DetailsButton({ href }: {href: string}) {
    return (
        <Button variant="ghost" className="h-8 w-8 p-0">
            <Link href={href}>
                <LucideMousePointerClick />
            </Link>
        </Button>
    )
}