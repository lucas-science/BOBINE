"use client";

import React, { useState } from "react";
import { Checkbox } from "@/src/components/ui/checkbox";
import { Button } from "@/src/ui/button";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/src/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/src/components/ui/popover";
import { Badge } from "@/src/components/ui/badge";
import { Check, ChevronDown, X } from "lucide-react";
import { cn } from "@/src/lib/utils";

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

  const handleClick = (e: React.MouseEvent) => {
    // Empêcher le toggle si on clique sur la checkbox, popover ou badges
    if (e.target !== e.currentTarget &&
      ((e.target as Element).closest('[role="checkbox"]') ||
        (e.target as Element).closest('[role="combobox"]') ||
        (e.target as Element).closest('.badge-remove') ||
        (e.target as Element).closest('[data-radix-popper-content-wrapper]'))) {
      return;
    }
    if (available) {
      onToggle();
    }
  };

  return (
    <div className={`flex flex-col space-y-3 p-3 rounded-lg border transition-colors ${available ? "cursor-pointer" : "cursor-not-allowed"
      } ${selected ? "bg-blue-50 hover:bg-blue-100" : "hover:bg-gray-50"}`}
    >
      <div className="flex items-start space-x-3" onClick={handleClick}>
        <Checkbox
          id={metricKey}
          checked={selected}
          onCheckedChange={onToggle}
          disabled={!available}
          className="mt-0.5 pointer-events-none"
        />
        <div className="flex-1 min-w-0">
          <div
            className={`block text-sm font-medium ${available ? "text-gray-900" : "text-gray-500"
              }`}
          >
            {name}
            {!available && " (Indisponible)"}
          </div>
        </div>
      </div>

      {selected && chimicalElements.length > 0 && (
        <div className="ml-6 space-y-2">
          <div className="flex items-center space-x-2">
            <Popover open={open} onOpenChange={setOpen}>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  role="combobox"
                  aria-expanded={open}
                  className="justify-between text-sm"
                >
                  Sélectionner éléments chimiques...
                  <ChevronDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-64 p-0 bg-card">
                <Command>
                  <CommandInput placeholder="Rechercher..." />
                  <CommandList>
                    <CommandEmpty>Aucun élément trouvé.</CommandEmpty>
                    <CommandGroup>
                      {chimicalElements
                        .filter((element) => !chosenElements.includes(element))
                        .map((element) => (
                          <CommandItem
                            key={element}
                            value={element}
                            onSelect={() => {
                              onAddElement(element);
                              setOpen(false);
                            }}
                          >
                            <Check
                              className={cn(
                                "mr-2 h-4 w-4",
                                "opacity-0"
                              )}
                            />
                            {element}
                          </CommandItem>
                        ))}
                    </CommandGroup>
                  </CommandList>
                </Command>
              </PopoverContent>
            </Popover>
          </div>

          {chosenElements.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {chosenElements.map((element) => (
                <Badge key={element} variant="secondary" className="text-sm font-normal px-2 py-1 flex items-center">
                  <span className="mr-2">{element}</span>
                  <X
                    className="h-4 w-4 cursor-pointer badge-remove hover:text-red-500 transition-colors"
                    onClick={() => onRemoveElement(element)}
                  />
                </Badge>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};