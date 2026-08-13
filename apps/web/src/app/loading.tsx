export default function Loading() {
  return (
    <div style={{ minHeight: "60vh", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: "1rem" }}>
      <div
        style={{
          width: "48px",
          height: "48px",
          border: "3px solid rgba(99, 102, 241, 0.2)",
          borderTopColor: "#6366f1",
          borderRadius: "50%",
          animation: "spin 0.8s linear infinite",
        }}
      />
      <span style={{ color: "#94a3b8", fontSize: "0.875rem", fontWeight: "500", letterSpacing: "0.05em" }}>
        LOADING CIVITAS CONTEXT...
      </span>
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
