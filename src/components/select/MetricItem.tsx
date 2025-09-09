"use client";

import React from "react";
import { Checkbox } from "@/src/components/ui/checkbox";

interface MetricItemProps {
  metricKey: string;
  name: string;
  available: boolean;
  selected: boolean;
  onToggle: () => void;
  subText?: string;
}

export const MetricItem: React.FC<MetricItemProps> = ({
  metricKey,
  name,
  available,
  selected,
  onToggle,
  subText,
}) => {
  const handleClick = (e: React.MouseEvent) => {
    // Empêcher la double sélection si on clique sur la checkbox
    if (e.target !== e.currentTarget && (e.target as Element).closest('[role="checkbox"]')) {
      return;
    }
    if (available) {
      onToggle();
    }
  };

  return (
    <div 
      className={`flex items-start space-x-3 p-3 rounded-lg border transition-colors ${
        available ? "cursor-pointer" : "cursor-not-allowed"
      } ${selected ? "bg-blue-50 hover:bg-blue-200" : "hover:bg-gray-50"}`}
      onClick={handleClick}
    >
      <Checkbox
        id={metricKey}
        checked={selected}
        onCheckedChange={onToggle}
        disabled={!available}
        className="mt-0.5 pointer-events-none"
      />
      <div className="flex-1 min-w-0">
        <div
          className={`block text-sm font-medium ${
            available ? "text-gray-900" : "text-gray-500"
          }`}
        >
          {name}
          {!available && " (Indisponible)"}
        </div>
        {subText && (
          <p className="text-xs text-gray-600 mt-1">{subText}</p>
        )}
      </div>
    </div>
  );
};