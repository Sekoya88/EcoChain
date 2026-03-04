"use client";

import React, { useState, useEffect } from "react";
import { PlusIcon } from "lucide-react";

interface PrismFluxLoaderProps {
  size?: number;
  speed?: number;
  textSize?: number;
  statuses?: string[];
  currentStatus?: string;
  compact?: boolean;
}

export function PrismFluxLoader({
  size = 30,
  speed = 5,
  textSize = 14,
  statuses = [
    "Extracting",
    "Validating",
    "Calculating",
    "Recommending",
    "Syncing",
    "Processing",
  ],
  currentStatus: controlledStatus,
  compact = false,
}: PrismFluxLoaderProps) {
  const [time, setTime] = useState(0);
  const [statusIndex, setStatusIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setTime((prev) => prev + 0.02 * speed);
    }, 16);
    return () => clearInterval(interval);
  }, [speed]);

  useEffect(() => {
    if (controlledStatus !== undefined) return;
    const statusInterval = setInterval(() => {
      setStatusIndex((prev) => (prev + 1) % statuses.length);
    }, 600);
    return () => clearInterval(statusInterval);
  }, [statuses.length, controlledStatus]);

  const half = size / 2;
  const status = controlledStatus ?? statuses[statusIndex];

  const faceTransforms = [
    `rotateY(0deg) translateZ(${half}px)`,
    `rotateY(180deg) translateZ(${half}px)`,
    `rotateY(90deg) translateZ(${half}px)`,
    `rotateY(-90deg) translateZ(${half}px)`,
    `rotateX(90deg) translateZ(${half}px)`,
    `rotateX(-90deg) translateZ(${half}px)`,
  ];

  return (
    <div className={`flex flex-col items-center justify-center gap-4 ${compact ? "min-h-0" : "min-h-[220px]"}`}>
      <div
        className="relative"
        style={{
          width: size,
          height: size,
          transformStyle: "preserve-3d",
          transform: `rotateY(${time * 30}deg) rotateX(${time * 30}deg)`,
        }}
      >
        {faceTransforms.map((transform, i) => (
          <div
            key={i}
            className="absolute flex items-center justify-center border border-primary bg-card/50 rounded-sm"
            style={{
              width: size,
              height: size,
              transform,
              backfaceVisibility: "hidden",
            }}
          >
            <PlusIcon className="w-3.5 h-3.5 text-primary" />
          </div>
        ))}
      </div>
      <div
        className="text-sm font-semibold text-primary tracking-wide"
        style={{ fontSize: textSize }}
      >
        {status}...
      </div>
    </div>
  );
}
