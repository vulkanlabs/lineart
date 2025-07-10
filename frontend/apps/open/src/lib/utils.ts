import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { format } from "date-fns";

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

export function parseDate(date: string) {
    // Use date-fns format for consistent server/client rendering
    // This avoids hydration mismatches caused by locale differences
    try {
        return format(new Date(date), "MMM d, yyyy 'at' HH:mm");
    } catch (error) {
        // Fallback for invalid dates
        return "Invalid Date";
    }
}
