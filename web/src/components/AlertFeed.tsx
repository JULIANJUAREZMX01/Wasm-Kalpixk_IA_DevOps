import React from "react";
import { useAlertStore, KalpixkAlert } from "../stores/alertStore";

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

      <div className="flex-1 overflow-y-auto scrollbar-hide">
        {alerts.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-white/20 gap-3 py-10">
            <div className="text-2xl">📡</div>
            <p className="text-[10px] tracking-widest">ESPERANDO SEÑALES...</p>
          </div>
        ) : (
          <div className="divide-y divide-white/5">
            {alerts.map((alert: KalpixkAlert) => (
              <div
                key={alert.id}
                className="p-4 hover:bg-white/[0.02] transition-colors group"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span
                      className={`px-1.5 py-0.5 rounded text-[8px] font-bold tracking-tighter ${
                        alert.score >= 0.85
                          ? "bg-red-500/10 text-red-500 border border-red-500/20"
                          : alert.score >= 0.5
                          ? "bg-orange-500/10 text-orange-500 border border-orange-500/20"
                          : "bg-emerald-500/10 text-emerald-500 border border-emerald-500/20"
                      }`}
                    >
                      SEV {(alert.score * 10).toFixed(1)}
                    </span>
                    <span className="text-[10px] text-white/70 font-bold uppercase truncate max-w-[120px]">
                      {alert.eventType}
                    </span>
                  </div>
                  <span className="text-[9px] text-white/20 font-mono">
                    {alert.ts.toLocaleTimeString()}
                  </span>
                </div>
                <p className="text-[11px] text-white/40 mb-2 line-clamp-2 leading-relaxed">
                  {alert.msg}
                </p>
                <div className="flex items-center justify-between">
                  <span className="text-[9px] text-white/30 font-mono group-hover:text-blue-400 transition-colors">
                    {alert.ip}
                  </span>
                  <span className="text-[9px] text-white/20 uppercase tracking-widest">
                    {alert.src}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
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
