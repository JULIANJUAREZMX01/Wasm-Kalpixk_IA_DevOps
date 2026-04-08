(function(){const t=document.createElement("link").relList;if(t&&t.supports&&t.supports("modulepreload"))return;for(const r of document.querySelectorAll('link[rel="modulepreload"]'))o(r);new MutationObserver(r=>{for(const i of r)if(i.type==="childList")for(const s of i.addedNodes)s.tagName==="LINK"&&s.rel==="modulepreload"&&o(s)}).observe(document,{childList:!0,subtree:!0});function n(r){const i={};return r.integrity&&(i.integrity=r.integrity),r.referrerPolicy&&(i.referrerPolicy=r.referrerPolicy),r.crossOrigin==="use-credentials"?i.credentials="include":r.crossOrigin==="anonymous"?i.credentials="omit":i.credentials="same-origin",i}function o(r){if(r.ep)return;r.ep=!0;const i=n(r);fetch(r.href,i)}})();function v(){let e,t;try{const n=a.health_check();return e=n[0],t=n[1],f(n[0],n[1])}finally{a.__wbindgen_free(e,t,1)}}function m(e,t){const n=b(e,a.__wbindgen_malloc,a.__wbindgen_realloc),o=u,r=b(t,a.__wbindgen_malloc,a.__wbindgen_realloc),i=u,s=a.parse_log_line(n,o,r,i);let l;return s[0]!==0&&(l=f(s[0],s[1]).slice(),a.__wbindgen_free(s[0],s[1]*1,1)),l}function x(e,t){let n,o;try{const r=b(e,a.__wbindgen_malloc,a.__wbindgen_realloc),i=u,s=b(t,a.__wbindgen_malloc,a.__wbindgen_realloc),l=u,d=a.process_batch(r,i,s,l);return n=d[0],o=d[1],f(d[0],d[1])}finally{a.__wbindgen_free(n,o,1)}}function A(){let e,t;try{const n=a.version();return e=n[0],t=n[1],f(n[0],n[1])}finally{a.__wbindgen_free(e,t,1)}}function S(){return{__proto__:null,"./kalpixk_core_bg.js":{__proto__:null,__wbg___wbindgen_throw_81fc77679af83bc6:function(t,n){throw new Error(f(t,n))},__wbg_getTime_f6ac312467f7cf09:function(t){return t.getTime()},__wbg_new_0_bfa2ef4bc447daa2:function(){return new Date},__wbindgen_cast_0000000000000001:function(t,n){return f(t,n)},__wbindgen_init_externref_table:function(){const t=a.__wbindgen_externrefs,n=t.grow(4);t.set(0,void 0),t.set(n+0,void 0),t.set(n+1,null),t.set(n+2,!0),t.set(n+3,!1)}}}}function f(e,t){return e=e>>>0,M(e,t)}let p=null;function y(){return(p===null||p.byteLength===0)&&(p=new Uint8Array(a.memory.buffer)),p}function b(e,t,n){if(n===void 0){const l=_.encode(e),d=t(l.length,1)>>>0;return y().subarray(d,d+l.length).set(l),u=l.length,d}let o=e.length,r=t(o,1)>>>0;const i=y();let s=0;for(;s<o;s++){const l=e.charCodeAt(s);if(l>127)break;i[r+s]=l}if(s!==o){s!==0&&(e=e.slice(s)),r=n(r,o,o=s+e.length*3,1)>>>0;const l=y().subarray(r+s,r+o),d=_.encodeInto(e,l);s+=d.written,r=n(r,o,s,1)>>>0}return u=s,r}let g=new TextDecoder("utf-8",{ignoreBOM:!0,fatal:!0});g.decode();const T=2146435072;let w=0;function M(e,t){return w+=t,w>=T&&(g=new TextDecoder("utf-8",{ignoreBOM:!0,fatal:!0}),g.decode(),w=t),g.decode(y().subarray(e,e+t))}const _=new TextEncoder;"encodeInto"in _||(_.encodeInto=function(e,t){const n=_.encode(e);return t.set(n),{read:e.length,written:n.length}});let u=0,a;function O(e,t){return a=e.exports,p=null,a.__wbindgen_start(),a}async function E(e,t){if(typeof Response=="function"&&e instanceof Response){if(typeof WebAssembly.instantiateStreaming=="function")try{return await WebAssembly.instantiateStreaming(e,t)}catch(r){if(e.ok&&n(e.type)&&e.headers.get("Content-Type")!=="application/wasm")console.warn("`WebAssembly.instantiateStreaming` failed because your server does not serve Wasm with `application/wasm` MIME type. Falling back to `WebAssembly.instantiate` which is slower. Original error:\n",r);else throw r}const o=await e.arrayBuffer();return await WebAssembly.instantiate(o,t)}else{const o=await WebAssembly.instantiate(e,t);return o instanceof WebAssembly.Instance?{instance:o,module:e}:o}function n(o){switch(o){case"basic":case"cors":case"default":return!0}return!1}}async function D(e){if(a!==void 0)return a;e!==void 0&&(Object.getPrototypeOf(e)===Object.prototype?{module_or_path:e}=e:console.warn("using deprecated parameters for the initialization function; pass a single object instead")),e===void 0&&(e=new URL("/assets/kalpixk_core_bg-D2CSRkTn.wasm",import.meta.url));const t=S();(typeof e=="string"||typeof Request=="function"&&e instanceof Request||typeof URL=="function"&&e instanceof URL)&&(e=fetch(e));const{instance:n,module:o}=await E(await e,t);return O(n)}let $=!1;async function I(){$||(await D(),$=!0,console.log(`[Kalpixk] Motor WASM listo: ${A()}`))}const c={bg:"#080808",green:"#32ff32",red:"#ff1a1a",orange:"#ff6400",cyan:"#00c8ff",gray:"#646464"};function h(e){document.getElementById("app").innerHTML=e}async function N(){h(`<div style="padding:20px;color:${c.cyan}">⏳ Cargando motor WASM...</div>`);try{await I();const e=JSON.parse(v()),t=m("Apr  5 02:14:22 cancun-srv01 sshd[1234]: Failed password for root from 45.33.32.156 port 22","syslog"),n=t?JSON.parse(t):null,o=m("TIMESTAMP=2026-04-05-02.15.00 AUTHID=CEDIS_USR HOSTNAME=185.220.101.35 OPERATION=DDL STATEMENT=DROP TABLE NOMINAS","db2"),r=o?JSON.parse(o):null,i=JSON.parse(x(JSON.stringify(["Apr  5 10:00:00 server sshd[1]: Accepted publickey for jjuarez from 192.168.1.50","Apr  5 02:00:00 server sshd[2]: Failed password for root from 45.33.32.156","Apr  5 03:11:00 server sshd[3]: Failed password for admin from 203.0.113.45"]),"syslog"));h(`
      <div style="background:${c.bg};min-height:100vh;padding:24px;font-family:'Courier New',monospace">
        <h1 style="color:${c.red};letter-spacing:3px;text-shadow:0 0 12px ${c.red}">
          ██ KALPIXK SIEM
        </h1>
        <p style="color:${c.gray}">WASM-native Blue Team SIEM · AMD MI300X · Hackathon 2026</p>
        <hr style="border-color:#1a1a1a;margin:16px 0"/>

        <h2 style="color:${c.green}">✅ Motor WASM: ${A()}</h2>
        <p style="color:${c.gray}">Feature dim: ${e.feature_dim} · Contract: ${e.contract_version}</p>

        <hr style="border-color:#1a1a1a;margin:16px 0"/>
        <h3 style="color:${c.orange}">🧪 Test 1 — SSH Brute Force (syslog)</h3>
        ${n?`
          <p style="color:${c.green}">✅ Evento detectado:</p>
          <pre style="color:${c.cyan};background:#111;padding:12px;border-radius:4px">
event_type: ${n.event_type}
severity:   ${(n.local_severity*100).toFixed(0)}%
source:     ${n.source}
user:       ${n.user||"—"}
          </pre>
        `:`<p style="color:${c.red}">❌ No parseado</p>`}

        <h3 style="color:${c.orange}">🧪 Test 2 — DROP TABLE DB2</h3>
        ${r?`
          <p style="color:${c.green}">✅ Evento detectado:</p>
          <pre style="color:${c.cyan};background:#111;padding:12px;border-radius:4px">
event_type: ${r.event_type}
severity:   ${(r.local_severity*100).toFixed(0)}%
source:     ${r.source}
user:       ${r.user||"—"}
          </pre>
        `:`<p style="color:${c.red}">❌ No parseado</p>`}

        <h3 style="color:${c.orange}">🧪 Test 3 — Batch de ${i.parsed_count} logs</h3>
        <p style="color:${c.green}">
          ✅ ${i.parsed_count} parseados · 
          ${i.anomaly_count} anomalías · 
          ${i.feature_matrix[0]?.length||0} features/evento
        </p>

        <hr style="border-color:#1a1a1a;margin:16px 0"/>
        <p style="color:${c.gray}">
          <a href="/dashboard/index.html" style="color:${c.orange}">→ Dashboard completo</a>
        </p>
      </div>
    `)}catch(e){h(`<div style="padding:20px;color:#ff1a1a">
      ❌ Error cargando WASM: ${e}<br/>
      <small style="color:#646464">Asegúrate de haber compilado: cd crates/kalpixk-core && wasm-pack build --target web --release</small>
    </div>`),console.error(e)}}N();
