"""Generate data, select models on validation and evaluate frozen policies."""
from dataclasses import asdict, dataclass
from pathlib import Path
import hashlib
import importlib.metadata
import json
import platform
import time
import joblib
import numpy as np
import pandas as pd
from .data import generate_data, chronological_split
from .features import build_features, build_history, FEATURE_COLUMNS
from .models import fit_models, probability_metrics, save_models
from .policies import ConstantPolicy, ValuePolicy, PPOAgent, train_bandit
from .environment import AuctionEnv
from .evaluation import attach_probabilities, evaluate, select_value_multiplier


@dataclass(frozen=True)
class ExperimentConfig:
    rows: int = 15000
    data_seed: int = 2026
    seeds: tuple = (42, 43, 44)
    ppo_steps: int = 30000
    budget_per_opportunity: float = .35
    max_bid: float = 5.
    conversion_value: float = 30.


def save_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def source_digest():
    hasher = hashlib.sha256()
    for path in sorted(Path(__file__).parent.glob("*.py")):
        hasher.update(path.name.encode())
        hasher.update(path.read_bytes())
    return hasher.hexdigest()


def reproduce(output="outputs", config=ExperimentConfig()):
    if not config.seeds or len(set(config.seeds)) != len(config.seeds):
        raise ValueError("Supply unique training seeds.")
    if config.ppo_steps < 512:
        raise ValueError("PPO needs at least one 512-step rollout.")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    model_dir = output / "models"
    started = time.perf_counter()
    data = generate_data(config.rows, config.data_seed)
    features = build_features(data.opportunities, data.activity)
    overlap = list(set(features.columns) & set(data.opportunities.columns))
    frame = data.opportunities.drop(columns=overlap).join(features)
    train, validation, test = chronological_split(frame)
    print(f"Chronological split: {len(train)} train / {len(validation)} validation / {len(test)} test", flush=True)
    models, supervised_metrics = fit_models(train, validation)
    for target, label in [("ctr", "clicked"), ("cvr", "converted")]:
        subset = test if target == "ctr" else test[test.clicked == 1]
        supervised_metrics.append({"target": target, "model": models[target].kind,
                                   "split": "test", **probability_metrics(subset[label], models[target].predict(subset))})
    train, validation, test = [attach_probabilities(part, models) for part in [train, validation, test]]
    env_kwargs = {"budget_per_opportunity": config.budget_per_opportunity,
                  "max_bid": config.max_bid, "conversion_value": config.conversion_value}
    multiplier, validation_scores = select_value_multiplier(validation, [0., .5, 1., 1.5, 2.], env_kwargs)
    policy_metadata = {**asdict(config), "value_multiplier": multiplier, "ppo_seed": config.seeds[0],
                       "source_sha256": source_digest()}
    save_models(models, model_dir, policy_metadata)
    records, traces = [], {}
    for name, policy in [("Constant bid", ConstantPolicy(1.)), ("Value-based", ValuePolicy(multiplier))]:
        metrics, trace = evaluate(policy, test, **env_kwargs)
        records.append({"policy": name, "seed": None, **metrics})
        traces[name] = trace
    for seed in config.seeds:
        print(f"Training LinUCB and PPO, seed {seed}...", flush=True)
        env = AuctionEnv(train, episode_size=500, random_start=True, **env_kwargs)
        bandit = train_bandit(env, seed=seed, episodes=max(1, config.ppo_steps // 500))
        ppo = PPOAgent.train(env, seed=seed, timesteps=config.ppo_steps)
        for name, policy in [("LinUCB", bandit), ("PPO", ppo)]:
            metrics, trace = evaluate(policy, test, **env_kwargs)
            records.append({"policy": name, "seed": seed, **metrics})
            if seed == config.seeds[0]:
                traces[name] = trace
        if seed == config.seeds[0]:
            ppo.save(str(model_dir / "ppo.zip"))
            joblib.dump(bandit, model_dir / "linucb.joblib")
    results = pd.DataFrame(records)
    results.to_csv(output / "policy_results.csv", index=False)
    save_json(output / "supervised_metrics.json", supervised_metrics)
    save_json(output / "validation_selection.json", {"value_multiplier": multiplier,
              "scores": [{"multiplier": m, "profit": p} for p, m in validation_scores]})
    for name, trace in traces.items():
        trace.to_csv(output / f"trace_{name.lower().replace(' ', '_').replace('-', '_')}.csv", index=False)
    sample = data.opportunities.loc[[test.index[0]]].copy()
    history = build_history(sample, data.activity)
    sample = sample.join(history).iloc[0]
    payload = {key: int(sample[key]) for key in ["age", "segment", "adslot_id"]}
    payload.update({key: float(sample[key]) for key in ["floor_price", *history.columns]})
    payload.update({"request_id": sample.request_id, "timestamp": sample.timestamp.isoformat(),
                    "remaining_budget": 100., "initial_budget": 100., "time_remaining": 1., "strategy": "value"})
    save_json(output / "example_request.json", payload)
    metadata = {
        "config": asdict(config), "source_sha256": source_digest(), "python": platform.python_version(),
        "versions": {p: importlib.metadata.version(p) for p in ["numpy", "pandas", "scikit-learn", "torch", "stable-baselines3", "gymnasium"]},
        "data_sha256": hashlib.sha256(pd.util.hash_pandas_object(data.opportunities, index=False).values.tobytes()).hexdigest(),
        "activity_sha256": hashlib.sha256(pd.util.hash_pandas_object(data.activity, index=False).values.tobytes()).hexdigest(),
        "split": {name: {"n": len(part), "start": part.timestamp.min().isoformat(), "end": part.timestamp.max().isoformat()}
                  for name, part in [("train", train), ("validation", validation), ("test", test)]},
        "ppo_actual_steps_per_seed": int(np.ceil(config.ppo_steps / 512) * 512),
        "bandit_steps_per_seed": max(1, config.ppo_steps // 500) * min(500, len(train)),
        "elapsed_seconds": round(time.perf_counter() - started, 2),
    }
    save_json(output / "run_metadata.json", metadata)
    make_plots(results, traces, output, config)
    write_report(results, supervised_metrics, metadata, output)
    print(results[["policy", "seed", "conversions", "spend", "profit"]].to_string(index=False), flush=True)
    return results


def make_plots(results, traces, output, config):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    colors = ["#8999ad", "#2368a2", "#db9740", "#398472"]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.spines.top": False,
                         "axes.spines.right": False, "figure.facecolor": "white"})
    names = results.policy.drop_duplicates().tolist()
    means = results.groupby("policy", sort=False).profit.mean()
    std = results.groupby("policy", sort=False).profit.std().fillna(0.)
    fig, ax = plt.subplots(figsize=(9, 4.7), layout="constrained")
    ax.bar(names, means.loc[names], yerr=std.loc[names], color=colors, capsize=5, width=.6)
    ax.axhline(0, color="#596579", linewidth=.8)
    ax.set_ylabel("Simulated net profit (currency units)")
    ax.set_title("Held-out auction replay · equal budget, identical opportunities", loc="left", pad=20, weight="bold")
    ax.grid(axis="y", alpha=.15)
    ax.set_axisbelow(True)
    fig.text(.02, -.045, "Synthetic data only. Error bars: sample SD across training seeds; fixed baselines have one run.", fontsize=9)
    fig.savefig(output / "policy_comparison.png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), layout="constrained")
    for (name, trace), color in zip(traces.items(), colors):
        axes[0].plot(np.arange(len(trace)) + 1, trace.cumulative_spend, label=name, color=color)
        axes[1].plot(np.arange(len(trace)) + 1, trace.cumulative_profit, label=name, color=color)
    axes[0].axhline(len(next(iter(traces.values()))) * config.budget_per_opportunity, color="#596579", ls="--", label="Budget")
    axes[0].set_ylabel("Cumulative spend")
    axes[1].set_ylabel("Cumulative net profit")
    for ax in axes:
        ax.set_xlabel("Test opportunity")
        ax.grid(alpha=.15)
    axes[0].legend(fontsize=9)
    fig.suptitle(f"Replay trajectories · learned policies shown for seed {config.seeds[0]}", x=.04, ha="left", weight="bold")
    fig.savefig(output / "replay_curves.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def write_report(results, supervised, metadata, output):
    lines = ["# Reproduced benchmark", "", "Synthetic second-price auctions; these are simulated results, not production outcomes.", "",
             "## Policy comparison", "", "| Policy | Runs | Conversions (mean) | Spend (mean) | Net profit (mean ± SD) | Budget used |",
             "|---|---:|---:|---:|---:|---:|"]
    for name, group in results.groupby("policy", sort=False):
        std = group.profit.std() if len(group) > 1 else 0.
        lines.append(f"| {name} | {len(group)} | {group.conversions.mean():.1f} | {group.spend.mean():.2f} | {group.profit.mean():.2f} ± {std:.2f} | {group.budget_utilization.mean():.1%} |")
    lines += ["", "SD describes policy-training randomness on ONE fixed holdout, not uncertainty across real markets. Fixed baselines are run once.",
              "Net profit = conversions × 30 − spend under the default configuration. ROI = net profit / spend; no-spend ROI is undefined.",
              "", "## Supervised models", "", "CVR is evaluated only among clicked opportunities.", "",
              "| Target | Model | Split | n | AUC | Log loss | Brier score |", "|---|---|---|---:|---:|---:|---:|"]
    for row in supervised:
        auc = f"{row['auc']:.4f}" if row["auc"] is not None else "N/A"
        lines.append(f"| {row['target'].upper()} | {row['model']} | {row['split']} | {row['n']} | {auc} | {row['log_loss']:.4f} | {row['brier']:.4f} |")
    lines += ["", "## Reproduction metadata", "", "See [run_metadata.json](run_metadata.json) for seeds, split timestamps, dependency versions, data hashes and a source hash.",
              "See [policy_results.csv](policy_results.csv) for every run, including underperforming policies.", "",
              "![Policy comparison](policy_comparison.png)", "", "![Replay curves](replay_curves.png)", ""]
    (output / "RESULTS.md").write_text("\n".join(lines))
