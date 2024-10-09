import * as React from "react";
import CircularProgress from "@mui/material/CircularProgress";
import Box from "@mui/material/Box";

export default function Loader() {
    return (
        <div
            style={{
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                height: "100vh",
            }}
        >
            <div className="flex flex-col gap-6">
                <div className="text-lg font-medium text-center">Loading...</div>
                <Box sx={{ display: "flex" }}>
                    <CircularProgress size={100} thickness={2} color="inherit" />
                </Box>
            </div>
        </div>
    );
}
