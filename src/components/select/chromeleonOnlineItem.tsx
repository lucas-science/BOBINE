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

  return (
    <div className="flex flex-col space-y-3 p-3 rounded-lg border hover:bg-gray-50 transition-colors">
      <div className="flex items-start space-x-3">
        <Checkbox
          id={metricKey}
          checked={selected}
          onCheckedChange={onToggle}
          disabled={!available}
          className="mt-0.5"
        />
        <div className="flex-1 min-w-0">
          <label
            htmlFor={metricKey}
            className={`block text-sm font-medium cursor-pointer ${
              available ? "text-gray-900" : "text-gray-500"
            }`}
          >
            {name}
            {!available && " (Indisponible)"}
          </label>
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
                  className="w-64 justify-between text-sm"
                >
                  Sélectionner éléments chimiques...
                  <ChevronDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-64 p-0">
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
            <div className="flex flex-wrap gap-1">
              {chosenElements.map((element) => (
                <Badge key={element} variant="secondary" className="text-xs">
                  {element}
                  <X
                    className="ml-1 h-3 w-3 cursor-pointer"
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