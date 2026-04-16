import React from 'react';
import { useAlertStore } from '../stores/alertStore';

const sevColor = (s: number) => {
  if (s >= 0.8) return "#ff1a1a";
  if (s >= 0.5) return "#ff6400";
  return "#32ff32";
};

// ⚡ Bolt: Optimización de renderizado para no re-renderizar todas las filas cuando se añade un nuevo evento
const AlertRow = React.memo(({ ev }: { ev: any }) => (
  <tr style={{ borderBottom: "1px solid #111" }}>
    <td style={cellStyle}>{new Date(ev.timestamp_ms).toLocaleTimeString("es-MX")}</td>
    <td style={cellStyle}>{ev.source}</td>
    <td style={cellStyle}>{ev.event_type}</td>
    <td style={{ ...cellStyle, color: sevColor(ev.local_severity), fontWeight: "bold" }}>
      {(ev.local_severity * 100).toFixed(0)}%
    </td>
    <td style={{ ...cellStyle, color: "#555", fontSize: "10px" }}>
      {ev.raw.substring(0, 80)}{ev.raw.length > 80 ? "..." : ""}
    </td>
  </tr>
));

export const AlertFeed: React.FC = () => {
  const events = useAlertStore((state) => state.events);

  return (
    <div style={{ background: "#0a0c10", border: "1px solid #1a1a1a", borderRadius: "6px", overflow: "hidden" }}>
      <div style={{ padding: "12px 16px", borderBottom: "1px solid #1a1a1a", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <span style={{ color: "#e2e8f0", fontSize: "12px", fontWeight: "bold" }}>🔴 EVENTOS EN TIEMPO REAL</span>
      </div>
      <div style={{ overflowX: "auto", maxHeight: "340px", overflowY: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead style={{ position: "sticky", top: 0, background: "#0d0f14", zIndex: 1 }}>
            <tr>
              <th style={headerStyle}>HORA</th>
              <th style={headerStyle}>FUENTE</th>
              <th style={headerStyle}>TIPO</th>
              <th style={headerStyle}>SEVERIDAD</th>
              <th style={headerStyle}>LOG ORIGINAL</th>
            </tr>
          </thead>
          <tbody>
            {events.length === 0 ? (
              <tr>
                <td colSpan={5} style={{ padding: "32px", textAlign: "center", color: "#444", fontSize: "11px" }}>
                  Esperando eventos...
                </td>
              </tr>
            ) : (
              events.map((ev) => (
                <AlertRow key={`${ev.timestamp_ms}-${ev.raw.substring(0, 20)}`} ev={ev} />
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

const headerStyle: React.CSSProperties = {
  padding: "8px 12px",
  color: "#444",
  fontSize: "9px",
  textAlign: "left",
  fontWeight: "normal",
  whiteSpace: "nowrap"
};

const cellStyle: React.CSSProperties = {
  padding: "8px 12px",
  fontSize: "11px",
  color: "#ccc"
};
