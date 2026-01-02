#!/usr/bin/env python3
import json
import os
from collections import defaultdict
import math

try:
    import matplotlib.pyplot as plt
except Exception:
    plt = None


def load_data(path="./relations/commit_path.json"):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Data file not found: {path}")
    with open(path, "r") as f:
        return json.load(f)


def build_fix_to_bic(data):
    fix_to_bic = defaultdict(list)
    fix_to_bic_filtered = defaultdict(list)
    for record in data:
        fix_commit = record.get("bug_causer")
        fixed_by = record.get("fixed_by") or []
        fix_to_bic[fix_commit].extend(fixed_by)
        if fixed_by:
            fix_to_bic_filtered[fix_commit].extend(fixed_by)
    return fix_to_bic, fix_to_bic_filtered

def count_propagation_bic_only(fix_commit, fix_to_bic_filtered, depth=1, propagation_count=None, visited=None):
    if propagation_count is None:
        propagation_count = defaultdict(int)
    if visited is None:
        visited = set()

    if fix_commit in visited:
        return propagation_count
    visited.add(fix_commit)

    bics = fix_to_bic_filtered.get(fix_commit, [])
    # Só conta quando há BICs (comportamento do get_depth_bic_qtd_level.py)
    if not bics:
        return propagation_count

    propagation_count[depth] += 1
    for bic in bics:
        count_propagation_bic_only(bic, fix_to_bic_filtered, depth + 1, propagation_count, visited)

    return propagation_count


def count_propagation_reverse(fix_to_bic, start_commit, depth=1, propagation_count=None, visited=None):
    if propagation_count is None:
        propagation_count = defaultdict(int)
    if visited is None:
        visited = set()

    if start_commit in visited:
        return propagation_count
    visited.add(start_commit)

    propagation_count[depth] += 1
    for bic in fix_to_bic.get(start_commit, []):
        count_propagation_reverse(fix_to_bic, bic, depth + 1, propagation_count, visited)

    return propagation_count


def trace_path(fix_to_bic, start_commit, path=None, all_paths=None, visited=None):
    if path is None:
        path = [start_commit]
    if all_paths is None:
        all_paths = []
    if visited is None:
        visited = set()

    if start_commit in visited:
        return all_paths
    visited.add(start_commit)

    bics = fix_to_bic.get(start_commit, [])
    if not bics:
        all_paths.append(path)
        return all_paths

    for bic in bics:
        trace_path(fix_to_bic, bic, path + [bic], all_paths, visited)

    return all_paths


def average_depth(paths):
    if not paths:
        return 0.0
    return sum(len(p) for p in paths) / len(paths)


def aggregate_basic(data, fix_to_bic):
    overall = defaultdict(int)
    for rec in data:
        fix = rec.get("bug_causer")
        count_propagation_reverse(fix_to_bic, fix, propagation_count=overall)

    # average
    total = sum(depth * cnt for depth, cnt in overall.items())
    total_count = sum(overall.values())
    avg = total / total_count if total_count else 0.0
    return overall, avg

def aggregate_basic_bics_only(data, fix_to_bic_filtered):
    overall = defaultdict(int)
    for rec in data:
        fix = rec.get("bug_causer")
        if fix_to_bic_filtered.get(fix):
            count_propagation_bic_only(fix, fix_to_bic_filtered, propagation_count=overall)

    # average
    total = sum(depth * cnt for depth, cnt in overall.items())
    total_count = sum(overall.values())
    avg = total / total_count if total_count else 0.0
    return overall, avg


def aggregate_by_experience(data, fix_to_bic, threshold=50):
    expert_paths = []
    non_expert_paths = []
    for rec in data:
        fix = rec.get("bug_causer")
        activity = rec.get("contributor_activity") or 0
        paths = trace_path(fix_to_bic, fix)
        if activity > threshold:
            expert_paths.extend(paths)
        else:
            non_expert_paths.extend(paths)

    return average_depth(expert_paths), average_depth(non_expert_paths)


def aggregate_by_experience_and_tests(data, fix_to_bic, threshold=50):
    groups = {
        "expert_with_tests": [],
        "expert_without_tests": [],
        "non_expert_with_tests": [],
        "non_expert_without_tests": []
    }
    for rec in data:
        fix = rec.get("bug_causer")
        activity = rec.get("contributor_activity") or 0
        has_tests = (rec.get("has_tests") == "Yes")
        paths = trace_path(fix_to_bic, fix)
        if activity > threshold:
            if has_tests:
                groups["expert_with_tests"].extend(paths)
            else:
                groups["expert_without_tests"].extend(paths)
        else:
            if has_tests:
                groups["non_expert_with_tests"].extend(paths)
            else:
                groups["non_expert_without_tests"].extend(paths)

    return {k: average_depth(v) for k, v in groups.items()}


def aggregate_tests_vs_no_tests(data, fix_to_bic):
    # count propagation where any commit in the path has tests vs none
    propagation_with_tests = defaultdict(int)
    propagation_without_tests = defaultdict(int)

    has_tests_map = {rec.get("bug_causer"): (rec.get("has_tests") == "Yes") for rec in data}

    def rec_count(commit, depth=1, visited=None, has_tests_in_path=False):
        if visited is None:
            visited = set()
        if commit in visited:
            return
        visited.add(commit)
        if has_tests_map.get(commit, False):
            has_tests_in_path = True
        if has_tests_in_path:
            propagation_with_tests[depth] += 1
        else:
            propagation_without_tests[depth] += 1
        for bic in fix_to_bic.get(commit, []):
            rec_count(bic, depth + 1, visited, has_tests_in_path)

    for rec in data:
        rec_count(rec.get("bug_causer"))

    return propagation_with_tests, propagation_without_tests


def tests_location(data, fix_to_bic):
    has_tests_map = {rec.get("bug_causer"): (rec.get("has_tests") == "Yes") for rec in data}
    all_depths = []

    def rec_collect(commit, depth=1, visited=None):
        if visited is None:
            visited = set()
        if commit in visited:
            return []
        visited.add(commit)
        paths = []
        if has_tests_map.get(commit, False):
            paths.append(depth)
        for bic in fix_to_bic.get(commit, []):
            paths.extend(rec_collect(bic, depth + 1, visited))
        return paths

    for rec in data:
        dlist = rec_collect(rec.get("bug_causer"))
        all_depths.extend(dlist)

    if not all_depths:
        return {"inicio": 0, "meio": 0, "fim": 0}

    mn = min(all_depths)
    mx = max(all_depths)
    if mx == mn:
        return {"inicio": len(all_depths), "meio": 0, "fim": 0}

    t1 = mn + (mx - mn) * 0.33
    t2 = mn + (mx - mn) * 0.66
    counts = {"inicio": 0, "meio": 0, "fim": 0}
    for d in all_depths:
        if d <= t1:
            counts["inicio"] += 1
        elif d <= t2:
            counts["meio"] += 1
        else:
            counts["fim"] += 1
    return counts


def metrics_by_level(data, fix_to_bic):
    commit_metrics = {}
    for rec in data:
        fix = rec.get("bug_causer")
        commit_metrics[fix] = {
            "dmm_unit_size": rec.get("dmm_unit_size"),
            "dmm_unit_complexity": rec.get("dmm_unit_complexity"),
            "dmm_unit_interfacing": rec.get("dmm_unit_interfacing"),
        }

    overall_propagation = defaultdict(int)
    metrics_sum = defaultdict(lambda: {"dmm_unit_size": 0.0, "dmm_unit_complexity": 0.0, "dmm_unit_interfacing": 0.0})
    metrics_count = defaultdict(lambda: {"dmm_unit_size": 0, "dmm_unit_complexity": 0, "dmm_unit_interfacing": 0})

    def rec_metrics(commit, depth=1, visited=None):
        if visited is None:
            visited = set()
        if commit in visited:
            return
        visited.add(commit)
        overall_propagation[depth] += 1
        metrics = commit_metrics.get(commit) or {}
        for key in ["dmm_unit_size", "dmm_unit_complexity", "dmm_unit_interfacing"]:
            v = metrics.get(key)
            if v is not None:
                metrics_sum[depth][key] += v
                metrics_count[depth][key] += 1
        for bic in fix_to_bic.get(commit, []):
            rec_metrics(bic, depth + 1, visited)

    for rec in data:
        rec_metrics(rec.get("bug_causer"))

    averages = {}
    for depth in sorted(overall_propagation.keys()):
        averages[depth] = {}
        for key in ["dmm_unit_size", "dmm_unit_complexity", "dmm_unit_interfacing"]:
            cnt = metrics_count[depth][key]
            if cnt:
                averages[depth][key] = metrics_sum[depth][key] / cnt
            else:
                averages[depth][key] = None
    return averages


def save_histogram(counts, filename, title="Histogram", xlabel="Level", ylabel="Count"):
    if plt is None:
        print("matplotlib not available, skipping plot:", filename)
        return
    levels = sorted(counts.keys())
    vals = [counts[l] for l in levels]
    plt.figure(figsize=(8, 4))
    plt.bar(levels, vals, color="tab:blue", alpha=0.7)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.xticks(levels)
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()


def write_summary_text(output_path, sections):
    with open(output_path, "w") as f:
        for title, body in sections:
            f.write(title + "\n")
            f.write("-" * len(title) + "\n")
            f.write(body + "\n\n")


def main():
    try:
        data = load_data()
    except Exception as e:
        print("Erro ao carregar dados:", e)
        return

    fix_to_bic, fix_to_bic_filtered = build_fix_to_bic(data)

    sections = []

    # Basic propagation
    basic_counts, basic_avg = aggregate_basic(data, fix_to_bic)
    sections.append(("Basic propagation (counts by level)", "\n".join(f"Level {d}: {c}" for d, c in sorted(basic_counts.items())) + f"\nAverage depth: {basic_avg:.4f}"))
    save_histogram(basic_counts, "./charts/histograma_general.png", title="General Propagation Histogram")

    basic_counts, basic_avg = aggregate_basic_bics_only(data, fix_to_bic_filtered)
    sections.append(("Basic propagation (counts by level)", "\n".join(f"Level {d}: {c}" for d, c in sorted(basic_counts.items())) + f"\nAverage depth: {basic_avg:.4f}"))
    save_histogram(basic_counts, "./charts/histograma_bics.png", title="BICs per Propagation Level")

    # Experience comparison
    avg_exp, avg_non = aggregate_by_experience(data, fix_to_bic)
    sections.append(("Experience comparison (avg depth)", f"Experienced (>50): {avg_exp:.4f}\nNon-experienced: {avg_non:.4f}"))
    if plt is not None:
        plt.figure()
        plt.bar(["Experienced", "Non-experienced"], [avg_exp, avg_non], color=("#2ca02c", "#d62728"))
        plt.title("Average chain depth by contributor experience")
        plt.ylabel("Average depth")
        plt.savefig("./charts/exp_vs_no_exp.png")
        plt.close()

    # Experience + tests
    groups = aggregate_by_experience_and_tests(data, fix_to_bic)
    sections.append(("Experience and tests (avg depth)", "\n".join(f"{k}: {v:.4f}" for k, v in groups.items())))
    if plt is not None:
        plt.figure(figsize=(7, 4))
        plt.bar(list(groups.keys()), list(groups.values()), color="#1f77b4")
        plt.xticks(rotation=20)
        plt.tight_layout()
        plt.title("Avg depth: experience vs tests")
        plt.savefig("./charts/exp_vs_no_exp_and_tests.png")
        plt.close()

    # Tests vs no tests propagation
    with_tests, without_tests = aggregate_tests_vs_no_tests(data, fix_to_bic)
    sections.append(("Propagation counts: paths with tests", "\n".join(f"Level {d}: {c}" for d, c in sorted(with_tests.items()))))
    sections.append(("Propagation counts: paths without tests", "\n".join(f"Level {d}: {c}" for d, c in sorted(without_tests.items()))))
    save_histogram(with_tests, "./charts/propagation_with_tests.png", title="Propagation (paths with tests)")
    save_histogram(without_tests, "./charts/propagation_without_tests.png", title="Propagation (paths without tests)")

    # Tests location
    location_tests = tests_location(data, fix_to_bic)
    print("Tests location (v2 - dynamic thirds):", location_tests)
    sections.append(("Tests location (v2 - dynamic thirds)", "\n".join(f"{k}: {v}" for k, v in location_tests.items())))

    # Metrics by level
    metrics_avg = metrics_by_level(data, fix_to_bic)
    lines = []
    for depth in sorted(metrics_avg.keys()):
        vals = metrics_avg[depth]
        lines.append(f"Level {depth}:")
        for k, v in vals.items():
            print(f"  {k}: {v if v is not None else 'N/A'}")
            lines.append(f"  {k}: {v if v is not None else 'N/A'}")
    sections.append(("Metrics averages per level", "\n".join(lines)))

    # Write summary
    write_summary_text("analyses_summary.txt", sections)
    print("Analyses complete. Summary: analyses_summary.txt and PNGs saved in current folder.")


if __name__ == "__main__":
    main()
