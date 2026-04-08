#!/usr/bin/env python3
"""
Skill: generate_dataset
Genera el dataset de entrenamiento con 9 tipos MITRE ATT&CK
Uso: python skills/generate_dataset.py [--size 5000] [--output datasets/kalpixk_train.json]
"""
import sys, os, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("--size",   type=int, default=5000)
    parser.add_argument("--output", default="datasets/kalpixk_train.json")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)

    # Importar el generador del datasets/
    import importlib.util, types
    spec = importlib.util.spec_from_file_location("gen", "datasets/generate_dataset.py")
    if spec:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if hasattr(mod, "generate_dataset"):
            events = mod.generate_dataset(args.size)
        else:
            print("Generando con lógica interna...")
            events = _generate(args.size)
    else:
        events = _generate(args.size)

    import json
    with open(args.output, "w") as f:
        json.dump(events, f)

    attacks = sum(1 for e in events if e.get("label")==1)
    normal  = len(events) - attacks
    print(f"✅ Dataset generado: {len(events)} eventos")
    print(f"   Ataques: {attacks} ({attacks/len(events)*100:.1f}%)")
    print(f"   Normales: {normal} ({normal/len(events)*100:.1f}%)")
    print(f"   Output: {args.output}")
    return {"size": len(events), "attacks": attacks, "path": args.output}

def _generate(size):
    import random, datetime
    random.seed(42)
    events = []
    IPS = ["45.33.32.156","203.0.113.45","185.220.101.35"]
    for _ in range(int(size * 0.85)):
        events.append({"raw": "normal login syslog", "source_type":"syslog","label":0,"score":round(random.uniform(0.05,0.20),3),"event_type":"login_success"})
    for _ in range(int(size * 0.15)):
        ip = random.choice(IPS)
        types = [("brute_force","T1110",0.85),("data_destruction","T1485",0.92),("data_exfiltration","T1005",0.80)]
        et, mitre, sc = random.choice(types)
        events.append({"raw": f"attack from {ip}", "source_type":"syslog","label":1,"score":round(sc+random.uniform(0,0.10),3),"event_type":et,"mitre":mitre})
    random.shuffle(events)
    return events

if __name__ == "__main__":
    run()
