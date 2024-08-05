
"use client";

import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { Form, FormField, FormControl, FormDescription, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const formSchema = z.object({
    name: z.string(),
    description: z.string(),
    input_schema: z.string(),
    output_schema: z.string(),
});

export function PolicyForm() {
    const form = useForm({
        resolver: zodResolver(formSchema),
        defaultValues: {
            name: "",
            description: "",
            input_schema: "",
            output_schema: "",
        },
    });

    function onSubmit(values) {
        console.log(values);
        fetch("http://localhost:6001/policies/create", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(values),
            mode: "cors",
        }).then((response) => {
            console.log(response);
            console.log(response.json());
        }).catch((error) => {
            console.error(error);
        });
    }

    return (
        <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="grid grid-cols-2 gap-2">
                <FormField control={form.control} name="name" render={({ field }) => (
                    <FormItem>
                        <FormLabel>Nome</FormLabel>
                        <FormControl>
                            <Input placeholder="Nova Política 1" {...field} />
                        </FormControl>
                        <FormDescription>
                            O nome da política.
                        </FormDescription>
                        <FormMessage />
                    </FormItem>
                )} />
                <FormField control={form.control} name="description" render={({ field }) => (
                    <FormItem>
                        <FormLabel>Description</FormLabel>
                        <FormControl>
                            <Input placeholder="Uma política interessante" {...field} />
                        </FormControl>
                        <FormDescription>
                            Descrição sucinta da política.
                        </FormDescription>
                        <FormMessage />
                    </FormItem>
                )} />

                <Button type="submit" className="col-start-2">Criar Política</Button>
            </form>
        </Form>
    );
}