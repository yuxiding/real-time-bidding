"""One command reproduces all published experiment outputs."""
import argparse
from .experiment import ExperimentConfig, reproduce


def main():
    parser = argparse.ArgumentParser(prog="aurorabid", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("reproduce", help="Generate synthetic data, train and evaluate")
    run.add_argument("--output", default="outputs")
    run.add_argument("--rows", type=int, default=15000)
    run.add_argument("--data-seed", type=int, default=2026)
    run.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    run.add_argument("--ppo-steps", type=int, default=30000)
    args = parser.parse_args()
    reproduce(args.output, ExperimentConfig(rows=args.rows, data_seed=args.data_seed,
              seeds=tuple(args.seeds), ppo_steps=args.ppo_steps))


if __name__ == "__main__":
    main()
