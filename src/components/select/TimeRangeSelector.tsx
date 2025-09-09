"use client";

import React from "react";
import { TimeRangeSelection } from "@/src/lib/utils/type";

interface TimeRangeSelectorProps {
  availableTimes: string[];
  selectedRange?: TimeRangeSelection;
  onRangeChange: (range: TimeRangeSelection) => void;
  disabled?: boolean;
}

export const TimeRangeSelector: React.FC<TimeRangeSelectorProps> = ({
  availableTimes,
  selectedRange,
  onRangeChange,
  disabled = false,
}) => {
  const handleStartTimeChange = (startTime: string) => {
    const newRange = { ...selectedRange, startTime: startTime || undefined };
    
    // If end time is selected and is before start time, clear end time
    if (newRange.endTime && newRange.startTime) {
      const startIndex = availableTimes.indexOf(newRange.startTime);
      const endIndex = availableTimes.indexOf(newRange.endTime);
      if (endIndex < startIndex) {
        newRange.endTime = undefined;
      }
    }
    
    onRangeChange(newRange);
  };

  const handleEndTimeChange = (endTime: string) => {
    const newRange = { ...selectedRange, endTime: endTime || undefined };
    onRangeChange(newRange);
  };

  // Get available end times (only times after or equal to start time)
  const getAvailableEndTimes = () => {
    if (!selectedRange?.startTime) return availableTimes;
    
    const startIndex = availableTimes.indexOf(selectedRange.startTime);
    if (startIndex === -1) return availableTimes;
    
    return availableTimes.slice(startIndex);
  };

  if (availableTimes.length === 0) {
    return (
      <div className="text-sm text-gray-500 italic ml-6 mt-2">
        Aucune donnée temporelle disponible
      </div>
    );
  }

  return (
    <div className="ml-6 mt-3 space-y-3 p-3 bg-gray-50 rounded-lg border">
      <div className="text-sm font-medium text-gray-700">
        Sélection de plage temporelle:
      </div>
      
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">
            Début:
          </label>
          <select
            value={selectedRange?.startTime || ""}
            onChange={(e) => handleStartTimeChange(e.target.value)}
            disabled={disabled}
            className="w-full text-sm border rounded px-2 py-1 bg-white disabled:bg-gray-100 disabled:cursor-not-allowed"
          >
            <option value="">Tout depuis le début</option>
            {availableTimes.map((time) => (
              <option key={time} value={time}>
                {time}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">
            Fin:
          </label>
          <select
            value={selectedRange?.endTime || ""}
            onChange={(e) => handleEndTimeChange(e.target.value)}
            disabled={disabled}
            className="w-full text-sm border rounded px-2 py-1 bg-white disabled:bg-gray-100 disabled:cursor-not-allowed"
          >
            <option value="">Jusqu&apos;à la fin</option>
            {getAvailableEndTimes().map((time) => (
              <option key={time} value={time}>
                {time}
              </option>
            ))}
          </select>
        </div>
      </div>

      {selectedRange?.startTime && selectedRange?.endTime && (
        <div className="text-xs text-green-600 bg-green-50 px-2 py-1 rounded">
          Plage sélectionnée: {selectedRange.startTime} → {selectedRange.endTime}
        </div>
      )}
      
      {selectedRange?.startTime && !selectedRange?.endTime && (
        <div className="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded">
          Depuis: {selectedRange.startTime} (jusqu&apos;à la fin)
        </div>
      )}
    </div>
  );
};