"use client";
import React from "react";
import { Button } from "@/src/ui/button";

type RestartButtonProps = {
    onClick: () => void;
    disable?: boolean;
};


export default function RestartButton({ onClick, disable }: RestartButtonProps) {
    if(disable) return null;
    return (
        <Button className="cursor-pointer ml-auto" onClick={onClick}>
            Recommencer
        </Button>
    );
}