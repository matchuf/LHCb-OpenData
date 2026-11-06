#!/usr/bin/env python3
"""Read-only ROOT exploration. Run: python explore_root.py --help."""

import argparse
import csv
import glob
import json
import re
from collections import Counter
from pathlib import Path

import awkward as ak
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import uproot
import yaml


def write_csv(path, rows):
    if rows:
        fields = list(dict.fromkeys(key for row in rows for key in row))
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)


def category(name):
    if "ProbNN" in name or "PID" in name or "Rich" in name or "Muon" in name or "Calo" in name:
        return "identificacion"
    if any(tag in name for tag in ("_L0", "_Hlt")):
        return "trigger"
    if any(tag in name for tag in ("VERTEX", "OWNPV", "ORIVX", "_COV_")) or name.startswith("PV"):
        return "geometria"
    if "_TAU" in name:
        return "tiempo_propio"
    if re.search(r"_(P|PT|PE|PX|PY|PZ|M|MM|MMERR|ID)$", name):
        return "cinematica"
    return "evento"


def describe(values):
    """Stats count all finite values, including possible sentinel values."""
    flat = np.asarray(ak.to_numpy(ak.flatten(values, axis=None)))
    if flat.dtype.kind not in "biuf":
        return {"status": "non_numeric"}, None
    good = flat[np.isfinite(flat)]
    if good.dtype.kind == "b":
        good = good.astype(np.int8)
    result = {
        "status": "ok", "values": int(flat.size),
        "nonfinite": int(flat.size - good.size),
        "unique": int(np.unique(good).size),
        "minus_1000": int(np.count_nonzero(good == -1000)),
        "minus_999": int(np.count_nonzero(good == -999)),
        "minus_1": int(np.count_nonzero(good == -1)),
        "zero": int(np.count_nonzero(good == 0)),
    }
    if good.size:
        q = np.quantile(good, [0, .01, .25, .5, .75, .99, 1])
        result.update(zip(["min", "p01", "p25", "median", "p75", "p99", "max"], map(float, q)))
        result.update(mean=float(np.mean(good)), std=float(np.std(good)))
    return result, good


def plot_axis(ax, values, name):
    values = values[np.isfinite(values)]
    if not values.size:
        ax.text(.5, .5, "Sin valores finitos", ha="center")
    else:
        unique = np.unique(values)
        if unique.size <= 12:
            frequencies = [np.count_nonzero(values == v) for v in unique]
            ax.bar([str(v) for v in unique], frequencies, color="#287c9e")
            ax.tick_params(axis="x", labelrotation=30)
        else:
            ax.hist(values, bins=50, histtype="step", color="#287c9e", linewidth=1.5)
        if values.size >= 100:
            ax.set_yscale("symlog", linthresh=1)
    ax.set_title(name, fontsize=10)
    ax.set_xlabel("Valor almacenado" if name != "derived_m_mumu" else "Masa dimuon [unidades de PE, P]")
    ax.set_ylabel("Valores / bin")
    ax.grid(alpha=.15)


def preview(path, arrays, derived, n):
    preferred = ["B0_M", "derived_m_mumu", "Kst_892_0_M", "KS0_M", "B0_PT",
                 "B0_IPCHI2_OWNPV", "B0_DIRA_OWNPV", "B0_TAU", "muplus_PIDmu",
                 "Kplus_PIDK", "nPV", "totCandidates", "B0_Hlt2Phys_TOS"]
    selected = [key for key in preferred if key in arrays.fields or key in derived][:12]
    if not selected:
        return
    fig, axes = plt.subplots((len(selected) + 2) // 3, 3, figsize=(15, 3.5 * ((len(selected) + 2) // 3)), squeeze=False)
    for ax, name in zip(axes.flat, selected):
        vals = derived[name] if name in derived else ak.to_numpy(arrays[name])
        plot_axis(ax, vals, name)
    for ax in list(axes.flat)[len(selected):]:
        ax.set_visible(False)
    fig.suptitle(f"{path.parent.parent.name} / {path.parent.name} | {n:,} entradas | sin cortes adicionales", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, .97))
    fig.savefig(path, dpi=130)
    plt.close(fig)


def explore_tree(tree, folder, limit, all_plots):
    folder.mkdir(parents=True, exist_ok=True)
    stop = tree.num_entries if limit == 0 else min(limit, tree.num_entries)
    # Bound memory by entry cap; disable caches to avoid retaining whole files.
    arrays = tree.arrays(entry_stop=stop, library="ak", array_cache=None)
    schemas, stats, histograms = [], [], []
    for name, typename in tree.typenames().items():
        branch = tree[name]
        values = arrays[name]
        shape = "variable" if "[]" in typename else "fixed_array" if "[" in typename else "scalar"
        schemas.append({"branch": name, "typename": typename, "shape": shape,
                        "category": category(name), "title": branch.title,
                        "count_branch": branch.count_branch.name if branch.count_branch is not None else "",
                        "compressed_bytes": branch.compressed_bytes,
                        "uncompressed_bytes": branch.uncompressed_bytes,
                        "baskets": branch.num_baskets})
        row, good = describe(values)
        row.update(branch=name, shape=shape, sampled_entries=stop)
        stats.append(row)
        if good is not None and good.size:
            unique, counts = np.unique(good, return_counts=True)
            if len(unique) <= 12:
                histograms.extend({"branch": name, "kind": "discrete", "value": value.item(), "count": int(count)}
                                  for value, count in zip(unique, counts))
            else:
                counts, edges = np.histogram(good, bins=50)
                histograms.extend({"branch": name, "kind": "continuous", "bin_left": float(left), "bin_right": float(right), "count": int(count)}
                                  for left, right, count in zip(edges[:-1], edges[1:], counts))
            if all_plots:
                fig, ax = plt.subplots(figsize=(8, 5))
                plot_axis(ax, good, name)
                fig.tight_layout()
                fig.savefig(folder / (name + ".png"), dpi=110)
                plt.close(fig)
    write_csv(folder / "branches.csv", schemas)
    write_csv(folder / "statistics.csv", stats)
    write_csv(folder / "histograms.csv", histograms)
    with (folder / "first_entries.json").open("w", encoding="utf-8") as stream:
        json.dump(ak.to_list(arrays[:5]), stream, ensure_ascii=False, indent=2, allow_nan=True)
    result = {"entries": tree.num_entries, "sampled_entries": stop,
              "branches": len(schemas), "types": dict(Counter(tree.typenames().values())),
              "compressed_bytes": tree.compressed_bytes,
              "uncompressed_bytes": tree.uncompressed_bytes,
              "nonfinite_values": sum(s.get("nonfinite", 0) for s in stats),
              "constant_branches_in_sample": sum(s.get("unique") == 1 for s in stats)}
    derived = {}
    names = set(arrays.fields)
    four_vectors = [p + "_" + c for p in ("muplus", "muminus") for c in ("PE", "PX", "PY", "PZ")]
    if set(four_vectors) <= names:
        sums = {c: ak.to_numpy(arrays["muplus_" + c] + arrays["muminus_" + c]) for c in ("PE", "PX", "PY", "PZ")}
        mass2 = sums["PE"] ** 2 - sums["PX"] ** 2 - sums["PY"] ** 2 - sums["PZ"] ** 2
        # Retain negative m2 as NaN for diagnosis instead of silently clipping it.
        mass = np.sqrt(np.where(mass2 >= 0, mass2, np.nan))
        derived["derived_m_mumu"] = mass
        write_csv(folder / "derived_m_mumu.csv", [{"entry": i, "m_mumu": float(m), "m2_mumu": float(m2)}
                                                 for i, (m, m2) in enumerate(zip(mass, mass2))])
        result["negative_dimuon_m2"] = int(np.count_nonzero(mass2 < 0))
        if "KS0_M" in names and stop:
            result["max_abs_KS0_M_minus_m_mumu"] = float(np.nanmax(np.abs(ak.to_numpy(arrays["KS0_M"]) - mass)))
    if {"runNumber", "eventNumber"} <= names:
        # Preserve uint64 event numbers: no conversion to float or mixed column stack.
        ids = list(zip(ak.to_list(arrays["runNumber"]), ak.to_list(arrays["eventNumber"])))
        counts = Counter(ids)
        result.update(unique_events_in_sample=len(counts),
                      events_with_multiple_rows_in_sample=sum(n > 1 for n in counts.values()))
    if "Polarity" in names:
        result["polarity_counts"] = {str(k): v for k, v in Counter(ak.to_list(arrays["Polarity"])).items()}
    if "nPV" in names:
        result["pv_length_mismatches"] = {
            name: int(ak.sum(ak.num(arrays[name], axis=1) != arrays["nPV"]))
            for name in names if tree[name].count_branch is not None and tree[name].count_branch.name == "nPV"}
    if tree.name == "DecayTree":
        preview(folder / "overview.png", arrays, derived, stop)
    else:
        result["first_rows"] = ak.to_list(arrays[:5])
    with (folder / "summary.json").open("w", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*", default=["job*.root"], help="Files or quoted glob patterns")
    parser.add_argument("--output", type=Path, default=Path("exploration"))
    parser.add_argument("--max-entries", type=int, default=50000, help="First N entries per tree; 0 = all (memory permitting)")
    parser.add_argument("--all-plots", action="store_true", help="Also generate one PNG per numeric branch; can be slow")
    parser.add_argument("--config", type=Path, default=Path(__file__).resolve().with_name("info.yaml"))
    args = parser.parse_args()
    if args.max_entries < 0:
        parser.error("--max-entries must be >= 0")
    files = sorted({Path(p) for pattern in args.files for p in glob.glob(pattern)})
    if not files:
        parser.error("No ROOT files matched")
    if len({p.stem for p in files}) != len(files):
        parser.error("Input file stems must be unique; use separate output directories")
    args.output.mkdir(parents=True, exist_ok=True)
    config = yaml.safe_load(args.config.read_text(encoding="utf-8")) if args.config.exists() else {}
    inventory, objects, summaries, schemas = [], [], {}, {}
    for path in files:
        print(f"Reading {path} ...", flush=True)
        job = config.get(path.stem, {})
        # Explicit local-file source also works on hosts with restricted worker threads.
        with uproot.open(path, object_cache=None, array_cache=None,
                         handler=uproot.source.file.MemmapSource) as root_file:
            classes = root_file.classnames(recursive=True, cycle=False)
            for key, classname in classes.items():
                objects.append({"file": path.name, "path": key, "class": classname})
                if classname != "TTree":
                    continue
                tree = root_file[key]
                folder = args.output / path.stem / key.replace("/", "__")
                result = explore_tree(tree, folder, args.max_entries, args.all_plots)
                summaries[f"{path.name}:{key}"] = result
                schemas[f"{path.name}:{key}"] = tree.typenames()
                inventory.append({"file": path.name, "file_bytes": path.stat().st_size, "tree": key,
                                  "entries": result["entries"], "sampled_entries": result["sampled_entries"],
                                  "branches": result["branches"],
                                  "unique_events_in_sample": result.get("unique_events_in_sample", ""),
                                  "bk_query": job.get("input", {}).get("bk_query", ""),
                                  "options": ", ".join(job.get("options", []))})
            if not any(key.endswith("/DecayTree") for key in classes):
                print(f"  NOTE: {path.name} has no DecayTree", flush=True)
    write_csv(args.output / "inventory.csv", inventory)
    write_csv(args.output / "objects.csv", objects)
    (args.output / "schemas.json").write_text(json.dumps(schemas, indent=2), encoding="utf-8")
    (args.output / "summary.json").write_text(json.dumps(summaries, indent=2), encoding="utf-8")
    versions = {module.__name__: module.__version__ for module in (uproot, ak, np, matplotlib, yaml)}
    (args.output / "versions.json").write_text(json.dumps(versions, indent=2), encoding="utf-8")
    lines = ["# Inventario de archivos ROOT", "", "Generado por explore_root.py; los ROOT se abren solo en lectura.", "",
             "| Archivo | Árbol | Entradas | Variables | Eventos únicos leídos |",
             "|---|---|---:|---:|---:|"]
    for row in inventory:
        lines.append(f"| {row['file']} | {row['tree']} | {row['entries']} | {row['branches']} | {row['unique_events_in_sample']} |")
    lines += ["", "Las entradas de DecayTree son candidatos. Los eventos únicos se cuentan con (runNumber, eventNumber) dentro de cada archivo y muestra leída.",
              "", "Estadísticas e histogramas: primeras N entradas, sin cortes adicionales, sin pesos y sin excluir posibles centinelas.",
              "Los arrays se aplanan para estadísticas/histogramas: PV cuenta vértices y COV cuenta elementos de matriz, no candidatos.",
              "Los esquemas y números de entradas describen el árbol completo. first_entries.json contiene las primeras cinco filas.",
              "", "Cada carpeta de árbol contiene branches.csv, statistics.csv, histograms.csv, summary.json y first_entries.json.",
              "Los DecayTree incluyen overview.png y derived_m_mumu.csv, si están disponibles los cuadrimomentos."]
    (args.output / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Done: {args.output.resolve() / 'REPORT.md'}", flush=True)


if __name__ == "__main__":
    main()
