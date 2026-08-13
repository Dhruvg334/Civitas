"use client";

import React, { Component, ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("Civitas UI ErrorBoundary caught an exception:", error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div style={{ padding: "2rem", textAlign: "center", background: "#121826", borderRadius: "12px", border: "1px solid rgba(239, 68, 68, 0.3)", color: "#f87171", margin: "2rem 0" }}>
          <h3 style={{ margin: "0 0 0.5rem", fontSize: "1.25rem" }}>Something went wrong</h3>
          <p style={{ color: "#94a3b8", fontSize: "0.875rem", marginBottom: "1rem" }}>
            {this.state.error?.message || "An unexpected error occurred while rendering this section."}
          </p>
          <button
            onClick={() => this.setState({ hasError: false, error: undefined })}
            style={{ padding: "0.5rem 1rem", background: "#3b82f6", color: "#fff", border: "none", borderRadius: "6px", cursor: "pointer" }}
          >
            Retry
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
