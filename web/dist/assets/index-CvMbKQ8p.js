(async ()=>{
    (function() {
        const t = document.createElement("link").relList;
        if (t && t.supports && t.supports("modulepreload")) return;
        for (const r of document.querySelectorAll('link[rel="modulepreload"]'))i(r);
        new MutationObserver((r)=>{
            for (const c of r)if (c.type === "childList") for (const o of c.addedNodes)o.tagName === "LINK" && o.rel === "modulepreload" && i(o);
        }).observe(document, {
            childList: !0,
            subtree: !0
        });
        function n(r) {
            const c = {};
            return r.integrity && (c.integrity = r.integrity), r.referrerPolicy && (c.referrerPolicy = r.referrerPolicy), r.crossOrigin === "use-credentials" ? c.credentials = "include" : r.crossOrigin === "anonymous" ? c.credentials = "omit" : c.credentials = "same-origin", c;
        }
        function i(r) {
            if (r.ep) return;
            r.ep = !0;
            const c = n(r);
            fetch(r.href, c);
        }
    })();
    const L = "modulepreload", k = function(e) {
        return "/" + e;
    }, m = {}, h = function(t, n, i) {
        let r = Promise.resolve();
        if (n && n.length > 0) {
            document.getElementsByTagName("link");
            const o = document.querySelector("meta[property=csp-nonce]"), s = o?.nonce || o?.getAttribute("nonce");
            r = Promise.allSettled(n.map((f)=>{
                if (f = k(f), f in m) return;
                m[f] = !0;
                const _ = f.endsWith(".css"), x = _ ? '[rel="stylesheet"]' : "";
                if (document.querySelector(`link[href="${f}"]${x}`)) return;
                const l = document.createElement("link");
                if (l.rel = _ ? "stylesheet" : L, _ || (l.as = "script"), l.crossOrigin = "", l.href = f, s && l.setAttribute("nonce", s), document.head.appendChild(l), _) return new Promise((O, T)=>{
                    l.addEventListener("load", O), l.addEventListener("error", ()=>T(new Error(`Unable to preload CSS for ${f}`)));
                });
            }));
        }
        function c(o) {
            const s = new Event("vite:preloadError", {
                cancelable: !0
            });
            if (s.payload = o, window.dispatchEvent(s), !s.defaultPrevented) throw o;
        }
        return r.then((o)=>{
            for (const s of o || [])s.status === "rejected" && c(s.reason);
            return t().catch(c);
        });
    };
    function M(e, t) {
        const n = v(e, a.__wbindgen_malloc, a.__wbindgen_realloc), i = g, r = v(t, a.__wbindgen_malloc, a.__wbindgen_realloc), c = g, o = a.parse_log_line(n, i, r, c);
        let s;
        return o[0] !== 0 && (s = y(o[0], o[1]).slice(), a.__wbindgen_free(o[0], o[1] * 1, 1)), s;
    }
    function S() {
        let e, t;
        try {
            const n = a.version();
            return e = n[0], t = n[1], y(n[0], n[1]);
        } finally{
            a.__wbindgen_free(e, t, 1);
        }
    }
    function R() {
        return {
            __proto__: null,
            "./kalpixk_core_bg.js": {
                __proto__: null,
                __wbg___wbindgen_throw_81fc77679af83bc6: function(t, n) {
                    throw new Error(y(t, n));
                },
                __wbg_getTime_f6ac312467f7cf09: function(t) {
                    return t.getTime();
                },
                __wbg_new_0_bfa2ef4bc447daa2: function() {
                    return new Date;
                },
                __wbindgen_cast_0000000000000001: function(t, n) {
                    return y(t, n);
                },
                __wbindgen_init_externref_table: function() {
                    const t = a.__wbindgen_externrefs, n = t.grow(4);
                    t.set(0, void 0), t.set(n + 0, void 0), t.set(n + 1, null), t.set(n + 2, !0), t.set(n + 3, !1);
                }
            }
        };
    }
    function y(e, t) {
        return e = e >>> 0, P(e, t);
    }
    let u = null;
    function p() {
        return (u === null || u.byteLength === 0) && (u = new Uint8Array(a.memory.buffer)), u;
    }
    function v(e, t, n) {
        if (n === void 0) {
            const s = d.encode(e), f = t(s.length, 1) >>> 0;
            return p().subarray(f, f + s.length).set(s), g = s.length, f;
        }
        let i = e.length, r = t(i, 1) >>> 0;
        const c = p();
        let o = 0;
        for(; o < i; o++){
            const s = e.charCodeAt(o);
            if (s > 127) break;
            c[r + o] = s;
        }
        if (o !== i) {
            o !== 0 && (e = e.slice(o)), r = n(r, i, i = o + e.length * 3, 1) >>> 0;
            const s = p().subarray(r + o, r + i), f = d.encodeInto(e, s);
            o += f.written, r = n(r, i, o, 1) >>> 0;
        }
        return g = o, r;
    }
    let b = new TextDecoder("utf-8", {
        ignoreBOM: !0,
        fatal: !0
    });
    b.decode();
    const W = 2146435072;
    let w = 0;
    function P(e, t) {
        return w += t, w >= W && (b = new TextDecoder("utf-8", {
            ignoreBOM: !0,
            fatal: !0
        }), b.decode(), w = t), b.decode(p().subarray(e, e + t));
    }
    const d = new TextEncoder;
    "encodeInto" in d || (d.encodeInto = function(e, t) {
        const n = d.encode(e);
        return t.set(n), {
            read: e.length,
            written: n.length
        };
    });
    let g = 0, a;
    function I(e, t) {
        return a = e.exports, u = null, a.__wbindgen_start(), a;
    }
    async function B(e, t) {
        if (typeof Response == "function" && e instanceof Response) {
            if (typeof WebAssembly.instantiateStreaming == "function") try {
                return await WebAssembly.instantiateStreaming(e, t);
            } catch (r) {
                if (e.ok && n(e.type) && e.headers.get("Content-Type") !== "application/wasm") console.warn("`WebAssembly.instantiateStreaming` failed because your server does not serve Wasm with `application/wasm` MIME type. Falling back to `WebAssembly.instantiate` which is slower. Original error:\n", r);
                else throw r;
            }
            const i = await e.arrayBuffer();
            return await WebAssembly.instantiate(i, t);
        } else {
            const i = await WebAssembly.instantiate(e, t);
            return i instanceof WebAssembly.Instance ? {
                instance: i,
                module: e
            } : i;
        }
        function n(i) {
            switch(i){
                case "basic":
                case "cors":
                case "default":
                    return !0;
            }
            return !1;
        }
    }
    async function E(e) {
        if (a !== void 0) return a;
        e !== void 0 && (Object.getPrototypeOf(e) === Object.prototype ? { module_or_path: e } = e : console.warn("using deprecated parameters for the initialization function; pass a single object instead")), e === void 0 && (e = new URL("/assets/kalpixk_core_bg-B8mrazkj.wasm", import.meta.url));
        const t = R();
        (typeof e == "string" || typeof Request == "function" && e instanceof Request || typeof URL == "function" && e instanceof URL) && (e = fetch(e));
        const { instance: n, module: i } = await B(await e, t);
        return I(n);
    }
    let A = !1;
    async function D() {
        if (!A) {
            if (typeof window > "u" || typeof process < "u" && !1) {
                const e = await h(()=>import("./__vite-browser-external-BIHI7g3E.js"), []), n = (await h(()=>import("./__vite-browser-external-BIHI7g3E.js"), [])).resolve(__dirname, "../../../crates/kalpixk-core/pkg/kalpixk_core_bg.wasm"), i = e.readFileSync(n), r = i.buffer.slice(i.byteOffset, i.byteOffset + i.byteLength);
                await E(r);
            } else await E();
            A = !0, console.log(`[Kalpixk] WASM motor v${S()} listo`);
        }
    }
    async function F() {
        await D();
        const e = M("Apr 5 02:14:22 server sshd[123]: Failed password for root from 45.33.32.156 port 22", "syslog");
        if (e) {
            const t = JSON.parse(e);
            console.log("[Kalpixk] Test WASM OK:", t.event_type, "score:", t.local_severity), document.getElementById("app").innerHTML = `
      <div style="font-family:monospace;padding:20px;background:#0d0f14;color:#14b8a6;min-height:100vh">
        <h1>Kalpixk SIEM v${S()}</h1>
        <p>Motor WASM: ✅ Funcionando</p>
        <p>Evento detectado: ${t.event_type}</p>
        <p>Severidad: ${(t.local_severity * 100).toFixed(0)}%</p>
        <p><a href="/dashboard/index.html" style="color:#f59e0b">→ Abrir dashboard completo</a></p>
      </div>
    `;
        }
    }
    F().catch(console.error);
})();
