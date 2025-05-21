"use client";

import { useRouter } from "next/navigation";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm, useFieldArray } from "react-hook-form";
import React, { useState, useEffect } from "react";
import { toast } from "sonner";

import { PolicyVersion } from "@vulkan-server/PolicyVersion";
import { PolicyAllocationStrategy } from "@vulkan-server/PolicyAllocationStrategy";
import { PolicyRunPartition } from "@vulkan-server/PolicyRunPartition";
import { updatePolicyAllocationStrategy } from "@/lib/api";

import { Button } from "@/components/ui/button";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
    DialogFooter,
    DialogDescription,
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
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Checkbox } from "@/components/ui/checkbox";
import { Trash2 } from "lucide-react";

const allocationFormSchema = z
    .object({
        choiceType: z.enum(["single", "multiple"], { required_error: "Choice type is required." }),
        singleChoiceVersionId: z.string().optional(),
        multipleChoiceVersions: z
            .array(
                z.object({
                    policy_version_id: z.string().min(1, "Policy version is required."),
                    frequency: z.coerce
                        .number()
                        .min(0, "Frequency must be >= 0")
                        .max(100, "Frequency must be <= 100"),
                }),
            )
            .optional(),
        shadowVersionIds: z.array(z.string()).optional(),
    })
    .superRefine((data, ctx) => {
        if (data.choiceType === "single") {
            if (!data.singleChoiceVersionId) {
                ctx.addIssue({
                    code: z.ZodIssueCode.custom,
                    message: "A policy version must be selected for single choice.",
                    path: ["singleChoiceVersionId"],
                });
            }
        } else if (data.choiceType === "multiple") {
            if (!data.multipleChoiceVersions || data.multipleChoiceVersions.length === 0) {
                ctx.addIssue({
                    code: z.ZodIssueCode.custom,
                    message: "At least one policy version is required for multiple choice.",
                    path: ["multipleChoiceVersions"],
                });
            } else {
                const totalFrequency = data.multipleChoiceVersions.reduce(
                    (sum, v) => sum + (v.frequency || 0),
                    0,
                );
                if (totalFrequency !== 100) {
                    ctx.addIssue({
                        code: z.ZodIssueCode.custom,
                        message: `Total frequency must be 100%. Current: ${totalFrequency}%`,
                        path: ["multipleChoiceVersions"],
                    });
                }
                // Check for duplicate policy versions in multiple choice
                const versionIds = data.multipleChoiceVersions.map((v) => v.policy_version_id);
                if (new Set(versionIds).size !== versionIds.length) {
                    ctx.addIssue({
                        code: z.ZodIssueCode.custom,
                        message: "Duplicate policy versions are not allowed in multiple choice.",
                        path: ["multipleChoiceVersions"],
                    });
                }
            }
        }
    });

type AllocationFormValues = z.infer<typeof allocationFormSchema>;

export function UpdateAllocationsDialog({
    policyId,
    currentAllocation,
    policyVersions,
}: {
    policyId: string;
    currentAllocation: PolicyAllocationStrategy | null;
    policyVersions: PolicyVersion[];
}) {
    const [open, setOpen] = useState(false);
    const router = useRouter();

    const form = useForm<AllocationFormValues>({
        resolver: zodResolver(allocationFormSchema),
        defaultValues: {
            choiceType:
                (currentAllocation?.choice?.length ?? 0) > 1 ||
                (currentAllocation?.choice?.length === 1 &&
                    currentAllocation.choice[0].frequency < 1000)
                    ? "multiple"
                    : "single",
            singleChoiceVersionId:
                currentAllocation?.choice?.length === 1 &&
                currentAllocation.choice[0].frequency === 1000
                    ? currentAllocation.choice[0].policy_version_id
                    : "",
            multipleChoiceVersions: currentAllocation?.choice
                // ensure single 100% choice isn't prefilled here
                ?.filter((c) => currentAllocation.choice.length > 1 || c.frequency < 1000)
                .map((c) => ({
                    policy_version_id: c.policy_version_id,
                    frequency: c.frequency / 10,
                })) || [{ policy_version_id: "", frequency: 0 }],
            shadowVersionIds: currentAllocation?.shadow || [],
        },
    });

    const { fields, append, remove } = useFieldArray({
        control: form.control,
        name: "multipleChoiceVersions",
    });

    const choiceType = form.watch("choiceType");

    useEffect(() => {
        // Reset form when dialog opens/closes or currentAllocation changes
        form.reset({
            choiceType:
                (currentAllocation?.choice?.length ?? 0) > 1 ||
                (currentAllocation?.choice?.length === 1 &&
                    currentAllocation.choice[0].frequency < 1000)
                    ? "multiple"
                    : "single",
            singleChoiceVersionId:
                currentAllocation?.choice?.length === 1 &&
                currentAllocation.choice[0].frequency === 1000
                    ? currentAllocation.choice[0].policy_version_id
                    : policyVersions.length > 0
                      ? policyVersions[0].policy_version_id
                      : "",
            multipleChoiceVersions: currentAllocation?.choice
                ?.filter((c) => currentAllocation.choice.length > 1 || c.frequency < 1000)
                .map((c) => ({
                    policy_version_id: c.policy_version_id,
                    frequency: c.frequency / 10,
                })) || [
                {
                    policy_version_id:
                        policyVersions.length > 0 ? policyVersions[0].policy_version_id : "",
                    frequency: 100,
                },
            ],
            shadowVersionIds: currentAllocation?.shadow || [],
        });
    }, [currentAllocation, policyVersions, open, form]);

    const onSubmit = async (values: AllocationFormValues) => {
        let choice: PolicyRunPartition[];
        if (values.choiceType === "single") {
            if (!values.singleChoiceVersionId) {
                toast.error("Validation Error", {
                    description: "Single choice version ID is missing.",
                });
                return;
            }
            choice = [{ policy_version_id: values.singleChoiceVersionId, frequency: 1000 }];
        } else {
            if (!values.multipleChoiceVersions) {
                toast.error("Validation Error", {
                    description: "Multiple choice versions are missing.",
                });
                return;
            }
            choice = values.multipleChoiceVersions.map((v) => ({
                policy_version_id: v.policy_version_id,
                frequency: Math.round(v.frequency * 10), // Convert to 0-1000
            }));
        }

        const payload: PolicyAllocationStrategy = {
            choice,
            shadow:
                values.shadowVersionIds && values.shadowVersionIds.length > 0
                    ? values.shadowVersionIds
                    : undefined,
        };

        try {
            await updatePolicyAllocationStrategy(policyId, payload);
            toast.success("Allocation Updated", {
                description: "The policy allocation strategy has been successfully updated.",
            });
            setOpen(false);
            router.refresh(); // Refresh data on the page
        } catch (error: any) {
            console.error("Failed to update allocation strategy:", error);
            toast.error("Update Failed", {
                description: error.message || "An unexpected error occurred.",
            });
        }
    };

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                <Button variant="outline">Update Allocation Strategy</Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-lg max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>Update Allocation Strategy</DialogTitle>
                    <DialogDescription>
                        Configure how policy versions are selected for execution.
                    </DialogDescription>
                </DialogHeader>
                <Form {...form}>
                    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6 py-4">
                        <FormField
                            control={form.control}
                            name="choiceType"
                            render={({ field }) => (
                                <FormItem className="space-y-3">
                                    <FormLabel>Choice Allocation Type</FormLabel>
                                    <FormControl>
                                        <RadioGroup
                                            onValueChange={field.onChange}
                                            defaultValue={field.value}
                                            className="flex flex-col space-y-1"
                                        >
                                            <FormItem className="flex items-center space-x-3 space-y-0">
                                                <FormControl>
                                                    <RadioGroupItem value="single" />
                                                </FormControl>
                                                <FormLabel className="font-normal">
                                                    Single Active Version
                                                </FormLabel>
                                            </FormItem>
                                            <FormItem className="flex items-center space-x-3 space-y-0">
                                                <FormControl>
                                                    <RadioGroupItem value="multiple" />
                                                </FormControl>
                                                <FormLabel className="font-normal">
                                                    Multiple Active Versions (Weighted Random)
                                                </FormLabel>
                                            </FormItem>
                                        </RadioGroup>
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />

                        {choiceType === "single" && (
                            <FormField
                                control={form.control}
                                name="singleChoiceVersionId"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>Active Policy Version</FormLabel>
                                        <Select
                                            onValueChange={field.onChange}
                                            defaultValue={field.value}
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
                                                        {version.alias || version.policy_version_id}
                                                    </SelectItem>
                                                ))}
                                            </SelectContent>
                                        </Select>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                        )}

                        {choiceType === "multiple" && (
                            <div className="space-y-4">
                                <FormLabel>Multiple Active Versions</FormLabel>
                                {fields.map((item, index) => (
                                    <div
                                        key={item.id}
                                        className="flex items-end gap-2 p-3 border rounded-md"
                                    >
                                        <FormField
                                            control={form.control}
                                            name={`multipleChoiceVersions.${index}.policy_version_id`}
                                            render={({ field }) => (
                                                <FormItem className="flex-1">
                                                    <FormLabel>Version</FormLabel>
                                                    <Select
                                                        onValueChange={field.onChange}
                                                        defaultValue={field.value}
                                                    >
                                                        <FormControl>
                                                            <SelectTrigger>
                                                                <SelectValue placeholder="Select version" />
                                                            </SelectTrigger>
                                                        </FormControl>
                                                        <SelectContent>
                                                            {policyVersions.map((version) => (
                                                                <SelectItem
                                                                    key={version.policy_version_id}
                                                                    value={
                                                                        version.policy_version_id
                                                                    }
                                                                >
                                                                    {version.alias ||
                                                                        version.policy_version_id}
                                                                </SelectItem>
                                                            ))}
                                                        </SelectContent>
                                                    </Select>
                                                    <FormMessage />
                                                </FormItem>
                                            )}
                                        />
                                        <FormField
                                            control={form.control}
                                            name={`multipleChoiceVersions.${index}.frequency`}
                                            render={({ field }) => (
                                                <FormItem className="w-28">
                                                    <FormLabel>Freq. (%)</FormLabel>
                                                    <FormControl>
                                                        <Input
                                                            type="number"
                                                            placeholder="e.g. 70"
                                                            {...field}
                                                        />
                                                    </FormControl>
                                                    <FormMessage />
                                                </FormItem>
                                            )}
                                        />
                                        <Button
                                            type="button"
                                            variant="ghost"
                                            size="icon"
                                            onClick={() => remove(index)}
                                            disabled={fields.length <= 1}
                                        >
                                            <Trash2 className="h-4 w-4" />
                                        </Button>
                                    </div>
                                ))}
                                <Button
                                    type="button"
                                    variant="outline"
                                    size="sm"
                                    onClick={() =>
                                        append({
                                            policy_version_id:
                                                policyVersions.length > 0
                                                    ? policyVersions[0].policy_version_id
                                                    : "",
                                            frequency: 0,
                                        })
                                    }
                                >
                                    Add Version
                                </Button>
                                {form.formState.errors.multipleChoiceVersions &&
                                    !form.formState.errors.multipleChoiceVersions.root && (
                                        <p className="text-sm font-medium text-destructive">
                                            {form.formState.errors.multipleChoiceVersions.message}
                                        </p>
                                    )}
                                {form.formState.errors.multipleChoiceVersions?.root?.message && (
                                    <p className="text-sm font-medium text-destructive">
                                        {form.formState.errors.multipleChoiceVersions.root.message}
                                    </p>
                                )}
                            </div>
                        )}

                        <FormField
                            control={form.control}
                            name="shadowVersionIds"
                            render={() => (
                                <FormItem>
                                    <div className="mb-4">
                                        <FormLabel className="text-base">
                                            Shadow Versions (Optional)
                                        </FormLabel>
                                        <FormDescription>
                                            Selected versions will run in shadow mode alongside the
                                            choice allocation.
                                        </FormDescription>
                                    </div>
                                    {policyVersions.map((version) => (
                                        <FormField
                                            key={version.policy_version_id}
                                            control={form.control}
                                            name="shadowVersionIds"
                                            render={({ field }) => {
                                                return (
                                                    <FormItem
                                                        key={version.policy_version_id}
                                                        className="flex flex-row items-start space-x-3 space-y-0"
                                                    >
                                                        <FormControl>
                                                            <Checkbox
                                                                checked={field.value?.includes(
                                                                    version.policy_version_id,
                                                                )}
                                                                onCheckedChange={(checked) => {
                                                                    return checked
                                                                        ? field.onChange([
                                                                              ...(field.value ||
                                                                                  []),
                                                                              version.policy_version_id,
                                                                          ])
                                                                        : field.onChange(
                                                                              field.value?.filter(
                                                                                  (value) =>
                                                                                      value !==
                                                                                      version.policy_version_id,
                                                                              ),
                                                                          );
                                                                }}
                                                            />
                                                        </FormControl>
                                                        <FormLabel className="font-normal">
                                                            {version.alias ||
                                                                version.policy_version_id}
                                                        </FormLabel>
                                                    </FormItem>
                                                );
                                            }}
                                        />
                                    ))}
                                    <FormMessage />
                                </FormItem>
                            )}
                        />

                        <DialogFooter>
                            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
                                Cancel
                            </Button>
                            <Button type="submit" disabled={form.formState.isSubmitting}>
                                {form.formState.isSubmitting ? "Saving..." : "Save Allocation"}
                            </Button>
                        </DialogFooter>
                    </form>
                </Form>
            </DialogContent>
        </Dialog>
    );
}
