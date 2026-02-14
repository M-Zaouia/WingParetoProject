import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


DATA = Path("data/raw/abiba/polars")
CL_TGT, E = 0.6, 0.85
RHO, V = 1.225, 60.0
N = 5000
B_RANGE, S_RANGE = (1.2, 3.2), (0.25, 1.2)
TAPER_RANGE, TWIST_RANGE = (0.2, 1.0), (-3.0, 3.0)

def load_polar_simple(folder):
    import re
    files = sorted([p for p in folder.glob("polar*") if p.is_file()]) if folder.exists() else []
    if not files:
        cl = np.linspace(-0.2, 1.5, 200)
        return cl, 0.008 + 0.02*cl**2

    pairs = []
    for ln in files[0].read_text(errors="ignore").splitlines():
        ln = ln.replace(",", ".")  # au cas où
        nums = re.findall(r"[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eEdD][-+]?\d+)?", ln)
        if len(nums) < 2:
            continue
        row = [float(x.replace("D","E").replace("d","e")) for x in nums]
        if len(row) >= 3:   # alpha, CL, CD, ...
            pairs.append((row[1], row[2]))
        else:               # CL, CD
            pairs.append((row[0], row[1]))

    a = np.array(pairs)
    if a.shape[0] < 5:
        cl = np.linspace(-0.2, 1.5, 200)
        return cl, 0.008 + 0.02*cl**2

    a = a[np.argsort(a[:, 0])]
    return a[:, 0], a[:, 1]


def pareto_idx(cd, m):
    o = np.argsort(cd)
    m_sorted = m[o]
    keep = m_sorted <= np.minimum.accumulate(m_sorted)
    return o[keep]

CL, CD = load_polar_simple(DATA)
rng = np.random.default_rng(0)

b = rng.uniform(*B_RANGE, N)
S = rng.uniform(*S_RANGE, N)
taper = rng.uniform(*TAPER_RANGE, N)
twist = rng.uniform(*TWIST_RANGE, N)

AR = b**2 / S
CL_eff = np.clip(CL_TGT + 0.01*twist, CL.min(), CL.max())
CD_prof = np.interp(CL_eff, CL, CD)
CDi = CL_eff**2 / (np.pi * AR * E)
CD_tot = CD_prof + CDi

q = 0.5 * RHO * V**2
M_root = (q * S * CL_eff) * b / 4

pf = pareto_idx(CD_tot, M_root)
cd_pf, m_pf = CD_tot[pf], M_root[pf]
cd_u, m_u = cd_pf.min(), m_pf.min()  # "utopia" = meilleur CD et meilleur M

cd_n = (cd_pf - cd_u) / (cd_pf.max() - cd_u + 1e-12)  # normalisation 0..1
m_n  = (m_pf  - m_u ) / (m_pf.max()  - m_u  + 1e-12)

chosen = pf[np.argmin(cd_n**2 + m_n**2)]  # plus proche du coin "idéal"
# --- plots ---
plt.figure()
plt.scatter(CD_tot, M_root, s=10, alpha=0.25)
plt.scatter(CD_tot[pf], M_root[pf], s=18)              # Pareto
plt.scatter(CD_tot[chosen], M_root[chosen], s=160, marker="*", edgecolors="k")  # chosen

txt = f"chosen: b={b[chosen]:.2f} S={S[chosen]:.2f} t={taper[chosen]:.2f} tw={twist[chosen]:+.2f}"
plt.annotate(txt, (CD_tot[chosen], M_root[chosen]), xytext=(12,12),
             textcoords="offset points")

plt.xlabel("CD_total"); plt.ylabel("Root bending proxy")
plt.title("Pareto front + chosen wing (*)")
plt.show()

plt.figure()
plt.scatter(AR, CDi, s=10, alpha=0.2)
plt.xlabel("AR = b^2/S"); plt.ylabel("CDi")
plt.title("Induced drag vs Aspect Ratio")
plt.show()
