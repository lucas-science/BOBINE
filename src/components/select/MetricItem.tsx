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
  return (
    <div className="flex items-start space-x-3 p-3 rounded-lg border hover:bg-gray-50 transition-colors">
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
        {subText && (
          <p className="text-xs text-gray-600 mt-1">{subText}</p>
        )}
      </div>
    </div>
  );
};