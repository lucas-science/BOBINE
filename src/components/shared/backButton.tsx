"use client";

import React from "react";

import { Button } from "@/src/ui/button";
import { ArrowLeft } from "lucide-react";

type BackButtonProps = {
    onClick: React.MouseEventHandler<HTMLButtonElement>;
    disable: boolean;
};

export default function BackButton({ onClick, disable }: BackButtonProps) {
    if(disable) return null;
    return (
        <Button className="cursor-pointer" onClick={onClick}>
            <ArrowLeft /> Précedent
        </Button>
    );
}