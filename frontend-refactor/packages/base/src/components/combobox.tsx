"use client";

import * as React from "react";
import { Check, ChevronsUpDown } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "./ui/button";
import {
    Command,
    CommandEmpty,
    CommandGroup,
    CommandInput,
    CommandItem,
} from "./ui/command";
import { Popover, PopoverContent, PopoverTrigger } from "./ui/popover";

export interface AssetOption {
    value: string;
    label: string;
}

interface AssetComboboxProps {
    options: AssetOption[];
    value: string;
    onChange: (value: string) => void;
    placeholder?: string;
    searchPlaceholder?: string;
    isLoading?: boolean;
    className?: string;
    emptyMessage?: string;
}

export function AssetCombobox({
    options = [],
    value,
    onChange,
    placeholder = "Select an option...",
    searchPlaceholder = "Search...",
    isLoading = false,
    className,
    emptyMessage = "No options found.",
}: AssetComboboxProps) {
    const [open, setOpen] = React.useState(false);
    const [searchQuery, setSearchQuery] = React.useState("");

    // Filter options based on search query
    const filteredOptions = React.useMemo(() => {
        if (!searchQuery) return options;
        const lowerCaseQuery = searchQuery.toLowerCase();
        return options.filter((option) => option.label.toLowerCase().includes(lowerCaseQuery));
    }, [options, searchQuery]);

    // Find the selected option's label
    const selectedOptionLabel = React.useMemo(() => {
        if (!value) return "";
        const option = options.find((option) => option.value === value);
        return option?.label || value;
    }, [options, value]);

    return (
        <Popover open={open} onOpenChange={setOpen}>
            <PopoverTrigger asChild>
                <Button
                    variant="outline"
                    role="combobox"
                    aria-expanded={open}
                    className={cn("w-full justify-between", className)}
                >
                    {value ? selectedOptionLabel : placeholder}
                    <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                </Button>
            </PopoverTrigger>
            <PopoverContent className="w-[300px] p-0">
                <Command>
                    <CommandInput
                        placeholder={searchPlaceholder}
                        value={searchQuery}
                        onValueChange={setSearchQuery}
                    />
                    <CommandEmpty>{isLoading ? "Loading..." : emptyMessage}</CommandEmpty>
                    <CommandGroup>
                        {filteredOptions.map((option) => (
                            <CommandItem
                                key={option.value}
                                value={option.value}
                                onSelect={(currentValue) => {
                                    onChange(currentValue === value ? "" : currentValue);
                                    setOpen(false);
                                    setSearchQuery("");
                                }}
                            >
                                <Check
                                    className={cn(
                                        "mr-2 h-4 w-4",
                                        value === option.value ? "opacity-100" : "opacity-0",
                                    )}
                                />
                                {option.label}
                            </CommandItem>
                        ))}
                    </CommandGroup>
                </Command>
            </PopoverContent>
        </Popover>
    );
}
