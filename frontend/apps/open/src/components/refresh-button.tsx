import { useRouter } from "next/navigation";
import { RotateCw } from "lucide-react";
import { Button } from "@vulkanlabs/base/ui";

export function RefreshButton() {
    const router = useRouter();

    return (
        <Button variant="outline" onClick={() => router.refresh()}>
            <RotateCw className="mr-4" />
            Refresh
        </Button>
    );
}
