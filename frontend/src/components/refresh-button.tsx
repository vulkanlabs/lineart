import { useRouter } from "next/navigation";

import { RotateCw } from "lucide-react";
import { Button } from "@/components/ui/button";
export function RefreshButton() {
    const router = useRouter();

    return (
        <Button onClick={() => router.refresh()}>
            <RotateCw className="mr-2" />
            Refresh
        </Button>
    );
}
