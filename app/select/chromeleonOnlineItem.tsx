import React, { useState } from "react";
import { Checkbox } from "@/src/components/ui/checkbox";
import { Badge } from "@/src/components/ui/badge";
import { Button } from "@/src/ui/button";
import { Popover, PopoverTrigger, PopoverContent } from "@/src/components/ui/popover";
import {
    Command,
    CommandEmpty,
    CommandGroup,
    CommandInput,
    CommandItem,
    CommandList,
} from "@/src/components/ui/command";
import { PlusIcon, XIcon, ChevronDown } from "lucide-react";

interface ChromeleonOnlineItemProps {
    metricKey: string;
    name: string;
    available: boolean;
    selected: boolean;
    chimicalElements: string[];
    chosenElements: string[];
    onToggle: () => void;
    onAddElement: (value: string) => void;
    onRemoveElement: (value: string) => void;
}

export const ChromeleonOnlineItem: React.FC<ChromeleonOnlineItemProps> = ({
    metricKey,
    name,
    available,
    selected,
    chimicalElements,
    chosenElements,
    onToggle,
    onAddElement,
    onRemoveElement,
}) => {
    const [open, setOpen] = useState(false);

    return (
        <div
            key={metricKey}
            className={`flex flex-col gap-2 p-3 rounded-lg border transition-colors ${available
                    ? selected
                        ? "bg-blue-50 border-blue-200"
                        : "bg-white border-gray-200 hover:bg-gray-50"
                    : "bg-gray-50 border-gray-200"
                } ${available ? "" : "cursor-not-allowed"}`}
        >
            {/* === ENTÊTE CLIQUABLE UNIQUEMENT === */}
            <button
                type="button"
                className={`flex items-start gap-3 text-left ${available ? "cursor-pointer" : ""}`}
                onClick={available ? onToggle : undefined}
            >
                <Checkbox
                    checked={selected}
                    disabled={!available}
                    className={`mt-0.5 ${!available ? "opacity-50" : ""}`}
                    onCheckedChange={onToggle}
                />
                <div className="flex-1 min-w-0">
                    <p className={`text-sm leading-5 ${available ? "text-gray-900" : "text-gray-400"}`}>
                        {name}
                    </p>
                </div>
            </button>

            {/* === ZONE AVANCÉE : PAS DE TOGGLE ICI === */}
            {selected && (
                <div className="pl-7 flex flex-col gap-2">
                    {/* Badges */}
                    {chosenElements.length > 0 && (
                        <div className="flex flex-wrap gap-2">
                            {chosenElements.map((el) => (
                                <Badge key={el} variant="secondary" className="gap-1">
                                    {el}
                                    <button
                                        type="button"
                                        className="cursor-pointer ml-1 inline-flex items-center justify-center"
                                        onClick={() => onRemoveElement(el)}
                                        title="Retirer"
                                    >
                                        <XIcon className="h-3.5 w-3.5" />
                                    </button>
                                </Badge>

                            ))}
                        </div>
                    )}

                    {/* Combobox */}
                    <div className="w-full max-w-sm">
                        <Popover open={open} onOpenChange={setOpen}>
                            <PopoverTrigger asChild>
                                <Button
                                    type="button"
                                    variant="outline"
                                    className="w-full justify-between"
                                    onClick={() => setOpen(!open)}
                                >
                                    <span className="inline-flex items-center gap-2">
                                        <PlusIcon className="h-4 w-4" />
                                        Ajouter un élément
                                    </span>
                                    <ChevronDown className="h-4 w-4 opacity-60" />
                                </Button>
                            </PopoverTrigger>
                            <PopoverContent
                                className="p-0 w-[280px]"
                                onMouseDown={(e) => e.stopPropagation()}
                                onClick={(e) => e.stopPropagation()}
                            >
                                <Command>
                                    <CommandInput placeholder="Rechercher un élément..." />
                                    <CommandList>
                                        <CommandEmpty>Aucun élément</CommandEmpty>
                                        <CommandGroup heading="Éléments disponibles">
                                            {chimicalElements.map((el) => {
                                                const disabled = chosenElements.includes(el);
                                                return (
                                                    <CommandItem
                                                        key={el}
                                                        value={el}
                                                        disabled={disabled}
                                                        onSelect={(value) => {
                                                            onAddElement(value);
                                                            setOpen(false); // 👉 ferme le popover après sélection
                                                        }}
                                                    >
                                                        {el}
                                                    </CommandItem>
                                                );
                                            })}
                                        </CommandGroup>
                                    </CommandList>
                                </Command>
                            </PopoverContent>
                        </Popover>
                    </div>
                </div>
            )}
        </div>
    );
};
