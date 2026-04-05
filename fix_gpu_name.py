import subprocess, torch

# Metodo 1: rocm-smi
try:
    out = subprocess.check_output(["rocm-smi", "--showproductname"], text=True, stderr=subprocess.DEVNULL)
    print("rocm-smi:", out.strip())
except: pass

# Metodo 2: /sys filesystem
try:
    import glob
    cards = glob.glob("/sys/class/drm/card*/device/product_name")
    for c in cards:
        print("sysfs:", open(c).read().strip())
except: pass

# Metodo 3: amd-smi
try:
    out = subprocess.check_output(["amd-smi", "static", "--asic"], text=True, stderr=subprocess.DEVNULL)
    for l in out.split("\n"):
        if "MARKET" in l.upper() or "NAME" in l.upper() or "MI300" in l.upper():
            print("amd-smi:", l.strip())
except: pass

# Metodo 4: torch props raw
props = torch.cuda.get_device_properties(0)
print(f"torch props: name={props.name}, total_memory={props.total_memory//1024**3}GB")
print(f"gcn_arch:", getattr(props, 'gcnArchName', 'N/A'))
