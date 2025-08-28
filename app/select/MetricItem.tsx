import React from "react";
import { Checkbox } from "@/src/components/ui/checkbox";

interface MetricItemProps {
  metricKey: string;
  name: string;
  available: boolean;
  selected: boolean;
  subText?: string;
  onToggle: () => void;
}

export const MetricItem: React.FC<MetricItemProps> = ({
  metricKey,
  name,
  available,
  selected,
  subText,
  onToggle,
}) => {
  return (
    <div
      key={metricKey}
      className={`flex items-start space-x-3 p-3 rounded-lg border transition-colors ${
        available
          ? selected
            ? "bg-blue-50 border-blue-200"
            : "bg-white border-gray-200 hover:bg-gray-50"
          : "bg-gray-50 border-gray-200"
      } ${available ? "cursor-pointer" : "cursor-not-allowed"}`}
      onClick={onToggle}
    >
      <Checkbox
        checked={selected}
        disabled={!available}
        className={`mt-0.5 ${!available ? "opacity-50" : ""}`}
        onCheckedChange={onToggle}
      />
      <div className="flex-1 min-w-0">
        <p className={`text-sm leading-5 ${available ? "text-gray-900" : "text-gray-400"}`}>{name}</p>
        {subText && (
          <p className={`text-xs mt-1 ${available ? "text-gray-500" : "text-gray-300"}`}>{subText}</p>
        )}
      </div>
    </div>
  );
};
