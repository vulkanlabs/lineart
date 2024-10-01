"use client";

import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { Form, FormField, FormControl, FormDescription, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "./ui/card";

const formSchema = z.object({
    name: z.string(),
    description: z.string(),
    input_schema: z.string(),
    output_schema: z.string(),
});

export function PolicyForm({ display, closeFunc }) {
    const form = useForm({
        resolver: zodResolver(formSchema),
        defaultValues: {
            name: "",
            description: "",
            input_schema: "",
            output_schema: "",
        }
    });

    if (!display) {
        return null;
    }

    function onSubmit(values) {
        fetch("http://localhost:6001/policies", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(values),
            mode: "cors",
        }).then((response) => {
            console.log(response.json());
            closeFunc();
        }).catch((error) => {
            console.error(error);
        });
        form.reset();
    }

    return (
        // A very long classname that essentially says:
        // "Whole screen, black background, centered content, with a nice animation"
        <div className="fixed inset-0 z-50 bg-black/80 flex justify-center items-center align-center data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0">
            <Card>
                <CardHeader>
                    <Button variant="destructive" className="mt-0 mr-0 w-[2em] h-[2em]" onClick={closeFunc}>X</Button>
                    <CardTitle>Create a New Policy</CardTitle>
                    <CardDescription>Configure your new Policy</CardDescription>
                </CardHeader>
                <CardContent>
                    <Form {...form}>
                        <form onSubmit={form.handleSubmit(onSubmit)} className="grid grid-cols-2 gap-2">
                            <FormField control={form.control} name="name" render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Name</FormLabel>
                                    <FormControl>
                                        <Input placeholder="New Policy 1" {...field} />
                                    </FormControl>
                                    <FormDescription>
                                        Name of the Policy.
                                    </FormDescription>
                                    <FormMessage />
                                </FormItem>
                            )} />
                            <FormField control={form.control} name="description" render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Description</FormLabel>
                                    <FormControl>
                                        <Input placeholder="An interesting policy" {...field} />
                                    </FormControl>
                                    <FormDescription>
                                        A short description of the Policy.
                                    </FormDescription>
                                    <FormMessage />
                                </FormItem>
                            )} />
                            <Button type="submit" className="w-fit">Create Policy</Button>
                        </form>
                    </Form>
                </CardContent>
            </Card>
        </div>
    );
}