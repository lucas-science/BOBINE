"use client";
import React from "react";
import { Button } from "@/src/ui/button";
import { ArrowRight } from "lucide-react";


type NextButtonProps = {
    onClick?: React.MouseEventHandler<HTMLButtonElement>;
    disable: boolean;
};

export default function NextButton({ onClick, disable }: NextButtonProps) {
    if(disable) return null;
    return (
        <Button className="cursor-pointer ml-auto" onClick={onClick}>
            Suivant <ArrowRight />
        </Button>
    );
}