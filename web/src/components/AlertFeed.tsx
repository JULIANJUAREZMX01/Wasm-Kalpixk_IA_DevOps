import React from "react";
import { useAlertStore, KalpixkAlert } from "../stores/alertStore";

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
      </div>
    </div>
  );
};
