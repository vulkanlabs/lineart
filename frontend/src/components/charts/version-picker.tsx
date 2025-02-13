"use client";

import * as React from "react";
import { MenuIcon } from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Card } from "@/components/ui/card";
import { PolicyVersion } from "@vulkan-server/PolicyVersion";
import { ShortenedID } from "@/components/shortened-id";
import { Checkbox } from "@/components/ui/checkbox";

export function VersionPicker({
    versions,
    selectedVersions,
    setSelectedVersions,
}: {
    versions: PolicyVersion[];
    selectedVersions: string[];
    setSelectedVersions: any;
}) {
    return (
        <div className={"grid gap-2"}>
            <Popover>
                <PopoverTrigger asChild>
                    <Button
                        id="date"
                        variant={"outline"}
                        className={cn(
                            "w-[300px] justify-start text-left font-normal",
                            !selectedVersions && "text-muted-foreground",
                        )}
                    >
                        <MenuIcon className="mr-2 h-4 w-4" />
                        {selectedVersions?.length > 0 ? (
                            <span>
                                {selectedVersions.length} version
                                {selectedVersions.length > 1 ? "s" : ""} selected
                            </span>
                        ) : (
                            <span>No version selected</span>
                        )}
                    </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                    <Card>
                        <div className="flex flex-col gap-2 p-4">
                            <h3 className="text-lg font-semibold">Select versions</h3>
                            <div className="flex flex-col gap-2">
                                {versions.map((version) => (
                                    <div key={version.policy_version_id}>
                                        <div className="flex items-center justify-start gap-2">
                                            <Checkbox
                                                checked={selectedVersions.includes(
                                                    version.policy_version_id,
                                                )}
                                                className={cn(
                                                    "justify-start text-left font-normal",
                                                    selectedVersions.includes(
                                                        version.policy_version_id,
                                                    ) && "bg-primary-foreground",
                                                )}
                                                onClick={() => {
                                                    setSelectedVersions(
                                                        selectedVersions.includes(
                                                            version.policy_version_id,
                                                        )
                                                            ? selectedVersions.filter(
                                                                  (v) =>
                                                                      v !==
                                                                      version.policy_version_id,
                                                              )
                                                            : [
                                                                  ...selectedVersions,
                                                                  version.policy_version_id,
                                                              ],
                                                    );
                                                }}
                                            />
                                            <div className="flex gap-1">
                                                {version.alias} (
                                                <ShortenedID
                                                    id={version.policy_version_id}
                                                    hover={false}
                                                />
                                                )
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </Card>
                </PopoverContent>
            </Popover>
        </div>
    );
}
