"use client";

import { cn } from "@/lib/utils";
import React from "react";

export interface LoaderProps {
  variant?:
    | "circular"
    | "classic"
    | "pulse"
    | "pulse-dot"
    | "dots"
    | "typing"
    | "wave"
    | "bars"
    | "terminal"
    | "text-blink"
    | "text-shimmer"
    | "loading-dots";
  size?: "sm" | "md" | "lg";
  text?: string;
  className?: string;
}

export function CircularLoader({
  className,
  size = "md",
}: {
  className?: string;
  size?: "sm" | "md" | "lg";
}) {
  const sizeClasses = {
    sm: "size-4",
    md: "size-5",
    lg: "size-6",
  };

  return (
    <div
      className={cn(
        "border-primary animate-spin rounded-full border-2 border-t-transparent",
        sizeClasses[size],
        className
      )}
    >
      <span className="sr-only">Loading</span>
    </div>
  );
}

export function TerminalLoader({
  className,
  size = "md",
}: {
  className?: string;
  size?: "sm" | "md" | "lg";
}) {
  const cursorSizes = {
    sm: "h-3 w-1.5",
    md: "h-4 w-2",
    lg: "h-5 w-2.5",
  };

  const textSizes = {
    sm: "text-xs",
    md: "text-sm",
    lg: "text-base",
  };

  const containerSizes = {
    sm: "h-4",
    md: "h-5",
    lg: "h-6",
  };

  return (
    <div
      className={cn(
        "flex items-center space-x-1",
        containerSizes[size],
        className
      )}
    >
      <span className={cn("text-primary font-mono", textSizes[size])}>
        {">"}
      </span>
      <div
        className={cn(
          "bg-primary animate-[blink_1s_step-end_infinite]",
          cursorSizes[size]
        )}
      />
      <span className="sr-only">Loading</span>
    </div>
  );
}

export function TextDotsLoader({
  className,
  text = "Thinking",
  size = "md",
}: {
  text?: string;
  className?: string;
  size?: "sm" | "md" | "lg";
}) {
  const textSizes = {
    sm: "text-xs",
    md: "text-sm",
    lg: "text-base",
  };

  return (
    <div className={cn("inline-flex items-center", className)}>
      <span className={cn("text-primary font-medium", textSizes[size])}>
        {text}
      </span>
      <span className="inline-flex">
        <span className="text-primary animate-[loading-dots_1.4s_infinite_0.2s]">.</span>
        <span className="text-primary animate-[loading-dots_1.4s_infinite_0.4s]">.</span>
        <span className="text-primary animate-[loading-dots_1.4s_infinite_0.6s]">.</span>
      </span>
    </div>
  );
}

export function Loader({
  variant = "circular",
  size = "md",
  text,
  className,
}: LoaderProps) {
  switch (variant) {
    case "terminal":
      return <TerminalLoader size={size} className={className} />;
    case "loading-dots":
      return <TextDotsLoader text={text} size={size} className={className} />;
    case "circular":
      return <CircularLoader size={size} className={className} />;
    default:
      return <TextDotsLoader text={text ?? "Processing"} size={size} className={className} />;
  }
}
