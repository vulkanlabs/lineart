import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function parseDate(dateString: string): Date {
  return new Date(dateString)
}

export function formatDate(date: Date): string {
  return date.toLocaleDateString()
}

export function formatDateTime(date: Date): string {
  return date.toLocaleString()
}