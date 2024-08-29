"use client"
import { useRouter } from "next/navigation"
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { z } from "zod"
import { Form, FormField, FormControl, FormDescription, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardHeader, CardContent, CardTitle, CardDescription } from "@/components/ui/card"
import { VulkanLogo } from "@/components/logo"
import { Separator } from "@/components/ui/separator"

export default function Page() {
    return (
        <div className="flex flex-col w-screen h-screen min-h-screen" >
            <div className="m-8">
                <VulkanLogo />
            </div>
            <div className="flex m-auto h-fit min-h-64">
                <LoginForm />
            </div>
        </div>
    )
}

const formSchema = z.object({
    email: z.string().email(),
    password: z.string(),
});

export function LoginForm() {
    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            email: "",
        }
    });

    const router = useRouter();
    function onSubmit(values: z.infer<typeof formSchema>) {
        console.log(values);
        router.push("/policies");
    }

    return (
        <Card >
            <CardHeader>
                <CardTitle className="text-3xl">Entrar no seu Workspace</CardTitle>
                <CardDescription className="text-lg">Login em Vulkan Engine</CardDescription>
            </CardHeader>
            <CardContent className="w-full">
                <Form {...form}>
                    <form onSubmit={form.handleSubmit(onSubmit)}>
                        <div className="flex flex-col gap-4">
                            <FormField control={form.control} name="email" render={({ field }) => (
                                <FormItem>
                                    <FormLabel className="text-xl">Email</FormLabel>
                                    <FormControl>
                                        <Input className="text-md lg:text-lg" placeholder="exemplo@email.com" {...field} />
                                    </FormControl>
                                    <FormDescription>
                                        Seu email corporativo.
                                    </FormDescription>
                                </FormItem>
                            )} />
                            <FormField control={form.control} name="password" render={({ field }) => (
                                <FormItem>
                                    <FormLabel className="text-xl">Senha</FormLabel>
                                    <FormControl>
                                        <Input className="text-md lg:text-lg" type="password" {...field} />
                                    </FormControl>
                                    <FormDescription>
                                        Sua senha.
                                    </FormDescription>
                                    <FormMessage />
                                </FormItem>
                            )} />

                            <Button type="submit" className="w-full">Entrar usando seu email</Button>
                            <Separator />
                            <div className="flex justify-center w-full"> ou </div>
                        </div>
                    </form>
                </Form>
                <Button className="w-full" variant="secondary">Entrar com uma conta Google</Button>
            </CardContent>
        </Card>

    );
}