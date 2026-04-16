# Kalpixk — Sandbox de Demostración

## Arquitectura

```
┌─────────────────────────────────────────────────────┐
│          Red: kalpixk-sandbox (aislada)              │
│                                                     │
│  ┌──────────┐    eventos.jsonl    ┌──────────────┐  │
│  │ attacker │──────────────────▶ │    sensor    │  │
│  │          │                    │ (32 features)│  │
│  └──────────┘                    └──────┬───────┘  │
│                                         │ HTTP POST │
│  ┌──────────┐                    ┌──────▼───────┐  │
│  │ honeypot │──── SSH attempts ▶ │   defender   │  │
│  │ :2222    │                    │  FastAPI     │  │
│  └──────────┘                    │  IF+AE model │  │
│                                  └──────┬───────┘  │
└─────────────────────────────────────────┼───────────┘
                                          │ WS :8000
                                   ┌──────▼───────┐
                                   │  Dashboard   │
                                   │  (browser)   │
                                   └──────────────┘
```

## Levantar el entorno

```bash
# Modo completo (ataques automáticos)
docker compose -f sandbox/docker-compose.sandbox.yml up --build

# Dashboard → abrir en browser:
open http://localhost:8000/docs    # API docs
# Abrir dashboard/index.html en browser (se conecta a ws://localhost:8000/stream)

# Lanzar un ataque específico manualmente:
docker compose -f sandbox/docker-compose.sandbox.yml exec attacker python sandbox/attacker.py ransomware
docker compose -f sandbox/docker-compose.sandbox.yml exec attacker python sandbox/attacker.py ssh_brute
docker compose -f sandbox/docker-compose.sandbox.yml exec attacker python sandbox/attacker.py exfil
docker compose -f sandbox/docker-compose.sandbox.yml exec attacker python sandbox/attacker.py privesc

# Ver logs en tiempo real:
docker compose -f sandbox/docker-compose.sandbox.yml logs -f sensor

# Destruir el entorno (limpieza total):
docker compose -f sandbox/docker-compose.sandbox.yml down -v
```

## Ataques implementados

| ID    | Nombre                | Técnica MITRE | Descripción                                      |
|-------|-----------------------|---------------|--------------------------------------------------|
| T1486 | Ransomware            | Impact        | Cifra 30 archivos con XOR (alta entropía real)   |
| T1110 | SSH Brute Force       | Credential    | 20 intentos de autenticación al honeypot         |
| T1041 | Data Exfiltration     | Exfiltration  | Lee archivos sensibles y los empaqueta           |
| T1548 | Privilege Escalation  | Privilege     | Escribe /etc/passwd con usuario root fake        |

## Notas de seguridad

- La red Docker es `internal: true` — **sin acceso a internet**
- Los archivos "víctima" son sintéticos en `/sandbox/target/`
- El honeypot solo escucha en la red interna Docker
- Ejecutar con `--no-new-privileges` en producción
