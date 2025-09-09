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
      <div className="ml-6 mt-3 p-4 bg-amber-50 border border-amber-200 rounded-xl">
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 bg-amber-400 rounded-full"></div>
          <span className="text-sm text-amber-700 font-medium">
            Aucune donnée temporelle disponible
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="ml-6 mt-3 p-4 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl border border-blue-100 shadow-sm">
      <div className="flex items-center space-x-2 mb-4">
        <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center">
          <div className="w-2 h-2 bg-white rounded-full"></div>
        </div>
        <h3 className="text-sm font-semibold text-gray-800">
          Plage temporelle
        </h3>
      </div>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <div className="w-1.5 h-1.5 bg-green-500 rounded-full"></div>
            <label className="text-xs font-semibold text-gray-700 uppercase tracking-wide">
              Heure de début
            </label>
          </div>
          <select
            value={selectedRange?.startTime || ""}
            onChange={(e) => handleStartTimeChange(e.target.value)}
            disabled={disabled}
            className="cursor-pointer w-full text-sm border-0 rounded-lg px-3 py-2.5 bg-white/80 backdrop-blur-sm shadow-sm ring-1 ring-gray-200 
                     focus:outline-none focus:bg-white transition-all duration-200
                     disabled:bg-gray-100 disabled:cursor-not-allowed disabled:ring-gray-100
                     hover:shadow-md hover:ring-gray-300"
          >
            <option value="">Tout depuis le début</option>
            {availableTimes.map((time) => (
              <option key={time} value={time}>
                {time}
              </option>
            ))}
          </select>
        </div>

        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <div className="w-1.5 h-1.5 bg-red-500 rounded-full"></div>
            <label className="text-xs font-semibold text-gray-700 uppercase tracking-wide">
              Heure de fin
            </label>
          </div>
          <select
            value={selectedRange?.endTime || ""}
            onChange={(e) => handleEndTimeChange(e.target.value)}
            disabled={disabled}
            className="cursor-pointer w-full text-sm border-0 rounded-lg px-3 py-2.5 bg-white/80 backdrop-blur-sm shadow-sm ring-1 ring-gray-200 
                     focus:outline-none focus:bg-white transition-all duration-200
                     disabled:bg-gray-100 disabled:cursor-not-allowed disabled:ring-gray-100
                     hover:shadow-md hover:ring-gray-300"
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
        <div className="text-xs px-2 rounded">
          Plage sélectionnée : {selectedRange.startTime} → {selectedRange.endTime}
        </div>
      )}
      
      {selectedRange?.startTime && !selectedRange?.endTime && (
        <div className="text-xs text-blue-600 px-2  rounded">
          Depuis {selectedRange.startTime} jusqu&apos;à la fin
        </div>
      )}

      {!selectedRange?.startTime && selectedRange?.endTime && (
        <div className="text-xs text-blue-600 px-2 rounded">
          Depuis le début, jusqu&apos;à {selectedRange.endTime}
        </div>
      )}
    </div>
  );
};