"use client";

import React, { useState, useEffect } from "react";
import { useUser } from "@stackframe/stack";

export default function Page({ params }) {
    const [data, setData] = useState(null);
    const user = useUser();

    function loadUserData() {
        getUserData(user).then((data) => {
            setData(data);
        });
    }

    return (
        <div className="flex flex-col w-screen h-screen min-h-screen">
            <button onClick={loadUserData}>Load Data</button>
            <div className="m-8">
                <h1>My Profile</h1>
            </div>
            <div className="flex m-auto h-fit min-h-64">
                <pre>{JSON.stringify(data, null, 2)}</pre>
            </div>
        </div>
    );
}

async function getUserData(user) {
    const { accessToken, refreshToken } = await user.getAuthJson();
    const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
    const response = await fetch(new URL(`/users/me`, serverUrl), {
        headers: {
            "x-stack-access-token": accessToken,
            "x-stack-refresh-token": refreshToken,
        },
    });
    const data = await response.json();
    return data;
}
