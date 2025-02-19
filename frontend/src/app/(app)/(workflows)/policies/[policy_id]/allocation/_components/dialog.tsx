"use client";

import { useRouter } from "next/navigation";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useStackApp } from "@stackframe/stack";
import { useForm } from "react-hook-form";
import { useState } from "react";
import { toast } from "sonner";

import { PolicyVersion } from "@vulkan-server/PolicyVersion";

import { Button } from "@/components/ui/button";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
    DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import {
    Form,
    FormField,
    FormControl,
    FormDescription,
    FormItem,
    FormLabel,
    FormMessage,
} from "@/components/ui/form";
import { Textarea } from "@/components/ui/textarea";
import { createPolicy } from "@/lib/api";

const formSchema = z.object({
    strategy: z.string().min(1),
    description: z.string().min(0),
});

enum AllocationStrategy {
    SINGLE = "single",
    RANDOM = "random",
    SHADOW = "shadow",
    MULTI = "multi",
}

export function UpdateAllocationsDialog({ policyVersions }: { policyVersions: PolicyVersion[] }) {
    const stackApp = useStackApp();
    const user = stackApp.getUser();
    const [open, setOpen] = useState(false);
    const [strategy, setStrategy] = useState(null);
    const router = useRouter();

    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            strategy: "",
            description: "",
        },
    });

    function handleStrategyChange(value: string) {
        setStrategy(value as AllocationStrategy);
    }

    function handleSingleDeployment(value: string) {
        console.log(strategy, value);
    }

    const onSubmit = async (data: any) => {
        await createPolicy(user, data)
            .then(() => {
                setOpen(false);
                form.reset();
                toast("Policy Created", {
                    description: `Policy ${data.name} has been created.`,
                    dismissible: true,
                });
                router.refresh();
            })
            .catch((error) => {
                console.error(error);
            });
    };

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <Form {...form}>
                <DialogTrigger asChild>
                    <Button variant="outline">Update Allocation Strategy</Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-[425px]">
                    <DialogHeader>
                        <DialogTitle>Configuration</DialogTitle>
                    </DialogHeader>
                    <form
                        className="flex flex-col gap-4 py-4"
                        onSubmit={form.handleSubmit(onSubmit)}
                    >
                        <div>
                            <FormItem>
                                <FormLabel>Strategy</FormLabel>
                                <Select
                                    onValueChange={handleStrategyChange}
                                    defaultValue={strategy}
                                >
                                    <FormControl>
                                        <SelectTrigger>
                                            <SelectValue placeholder="Select the allocation strategy" />
                                        </SelectTrigger>
                                    </FormControl>
                                    <SelectContent>
                                        <SelectItem key="single" value="single">
                                            SINGLE
                                        </SelectItem>
                                        <SelectItem key="random" value="random">
                                            RANDOM
                                        </SelectItem>
                                        <SelectItem key="shadow" value="shadow">
                                            SHADOW
                                        </SelectItem>
                                        <SelectItem key="multi" value="multi">
                                            MULTI
                                        </SelectItem>
                                    </SelectContent>
                                </Select>
                                <FormDescription>
                                    The strategy to trigger policy executions.
                                </FormDescription>
                                <FormMessage />
                            </FormItem>
                        </div>
                        {strategy === AllocationStrategy.SINGLE && (
                            <div>
                                <FormItem>
                                    <FormLabel>Policy Version</FormLabel>
                                    <Select
                                        onValueChange={handleSingleDeployment}
                                        defaultValue={""}
                                    >
                                        <FormControl>
                                            <SelectTrigger>
                                                <SelectValue placeholder="Select a policy version" />
                                            </SelectTrigger>
                                        </FormControl>
                                        <SelectContent>
                                            {policyVersions.map((version) => (
                                                <SelectItem
                                                    key={version.policy_version_id}
                                                    value={version.policy_version_id}
                                                >
                                                    {version.alias}
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                    <FormDescription>
                                        The policy version to be deployed.
                                    </FormDescription>
                                    <FormMessage />
                                </FormItem>
                            </div>
                        )}
                        {strategy === AllocationStrategy.RANDOM && (
                            <div className="flex flex-col gap-4">
                                <div className="text-base font-medium">Allocation</div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="flex flex-col gap-4">
                                        <div className="text-small font-normal">Version</div>
                                        <FormItem>
                                            <Select
                                            // onValueChange={handleSingleDeployment}
                                            // defaultValue={""}
                                            >
                                                <FormControl>
                                                    <SelectTrigger>
                                                        <SelectValue placeholder="Select a policy version" />
                                                    </SelectTrigger>
                                                </FormControl>
                                                <SelectContent>
                                                    {policyVersions.map((version) => (
                                                        <SelectItem
                                                            key={version.policy_version_id}
                                                            value={version.policy_version_id}
                                                        >
                                                            {version.alias}
                                                        </SelectItem>
                                                    ))}
                                                </SelectContent>
                                            </Select>
                                            <FormMessage />
                                        </FormItem>
                                        <FormItem>
                                            <Select
                                            // onValueChange={handleSingleDeployment}
                                            // defaultValue={""}
                                            >
                                                <FormControl>
                                                    <SelectTrigger>
                                                        <SelectValue placeholder="Select a policy version" />
                                                    </SelectTrigger>
                                                </FormControl>
                                                <SelectContent>
                                                    {policyVersions.map((version) => (
                                                        <SelectItem
                                                            key={version.policy_version_id}
                                                            value={version.policy_version_id}
                                                        >
                                                            {version.alias}
                                                        </SelectItem>
                                                    ))}
                                                </SelectContent>
                                            </Select>
                                            <FormMessage />
                                        </FormItem>
                                    </div>
                                    <div className="flex flex-col gap-4">
                                        <div className="text-small font-normal">Frequency</div>
                                        <FormItem>
                                            <Input type="number" />
                                        </FormItem>
                                        <FormItem>
                                            <Input type="number" />
                                        </FormItem>
                                    </div>
                                </div>
                            </div>
                        )}
                        <DialogFooter>
                            <Button type="submit">Deploy</Button>
                        </DialogFooter>
                    </form>
                </DialogContent>
            </Form>
        </Dialog>
    );
}
