import React from "react";
import { useAlertStore, KalpixkAlert } from "../stores/alertStore";

const cellStyle: React.CSSProperties = {
  padding: "8px 12px",
  fontSize: "11px",
  fontFamily: "monospace",
  textAlign: "left",
};

const headerStyle: React.CSSProperties = {
  ...cellStyle,
  color: "#888",
  fontSize: "9px",
  borderBottom: "1px solid #222",
  letterSpacing: "1px",
};

const sevColor = (s: number) => {
  if (s >= 0.8) return "#ff1a1a";
  if (s >= 0.5) return "#ff8c00";
  return "#32ff32";
};

const AlertRow = React.memo(({ alert }: { alert: KalpixkAlert }) => (
  <tr style={{ borderBottom: "1px solid #111" }}>
    <td style={cellStyle}>{alert.ts.toLocaleTimeString("es-MX")}</td>
    <td style={cellStyle}>{alert.src}</td>
    <td style={cellStyle}>{alert.eventType}</td>
    <td style={{ ...cellStyle, color: sevColor(alert.score), fontWeight: "bold" }}>
      {(alert.score * 100).toFixed(0)}%
    </td>
    <td style={{ ...cellStyle, color: "#555", fontSize: "10px" }}>
      {alert.msg.substring(0, 80)}{alert.msg.length > 80 ? "..." : ""}
    </td>
  </tr>
));

export const AlertFeed: React.FC = () => {
  const alerts = useAlertStore((state) => state.alerts);

  return (
    <div className="bg-[#0f1115] border border-white/5 rounded-xl overflow-hidden flex flex-col h-full">
      <div className="px-5 py-4 border-b border-white/5 flex items-center justify-between">
        <h3 className="text-xs font-bold text-white tracking-widest flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
          DETECCIONES EN VIVO
        </h3>
        <span className="text-[10px] text-white/30 font-mono">
          {alerts.length} EVENTOS MOSTRADOS
        </span>
      </div>

      <div className="flex-1 overflow-x-auto overflow-y-auto scrollbar-hide">
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
          <tbody className="divide-y divide-white/5">
            {alerts.length === 0 ? (
              <tr>
                <td colSpan={5} className="h-full flex flex-col items-center justify-center text-white/20 gap-3 py-10" style={{ textAlign: "center" }}>
                   <div className="text-2xl">📡</div>
                   <p className="text-[10px] tracking-widest">ESPERANDO SEÑALES...</p>
                </td>
              </tr>
            ) : (
              alerts.map((alert: KalpixkAlert) => (
                <AlertRow key={alert.id} alert={alert} />
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
