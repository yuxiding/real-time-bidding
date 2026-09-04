# Design and evaluation protocol

## Decision problem

The bidder observes context, available background history, predicted CTR/CVR,
and campaign progress. A win requires meeting both the highest competing bid
and reserve price. Ties favor our bidder; zero bids abstain. Amounts are arbitrary
simulated currency units per impression. Net profit is conversion value minus
spend. Training rewards divide net profit by the conversion value. A lost auction
has no cost and earns no reward, even if its potential outcome is positive.

## Data and time boundaries

`generate_data()` creates 15,000 opportunities, 250 fictitious users, and four
slots. Outcome probabilities depend on context; market prices are lognormal and
reserve prices uniform. The exact distribution and seeds are in `data.py`.

Background activity is a separate, policy-independent publisher stream. Binary
searches count only events strictly before the request: impressions at impression
time, clicks at click time, conversions at conversion time. No target outcome
from the evaluated auction enters these historical features.

The earliest 60% of timestamp groups are training, the next 20% validation, and
the final 20% test. Equal-time events cannot cross split boundaries. Fixed encodings
need no fitting; learned standardization is fitted on training only. Bundles
record an ordered feature schema and the API reuses `encode_requests()`.

## Models and policies

Logistic regression and histogram gradient boosting compete on validation log
loss for each target. CTR uses all examples; conditional CVR uses clicked examples.
Selected estimators remain fitted on training. Validation also selects the
expected-value bid multiplier; no test-set tuning occurs.

Policy training uses in-sample predictions from the training-fitted estimators.
Out-of-fold training predictions would be a useful additional check; validation
and test predictions are out of sample.

| Policy | Action | Training / selection |
|---|---|---|
| Constant bid | Bid 1 unit | Fixed baseline |
| Value-based | Multiplier × pCTR × conditional pCVR × value | Multiplier from 0, 0.5, 1, 1.5, 2 selected on validation profit |
| Disjoint LinUCB | One of the same five multipliers | Separate linear reward model and uncertainty estimate per action |
| PPO | One of the same five multipliers | Stable-Baselines3 stochastic actor-critic training |

Learned policies observe pCTR, pCVR, normalized expected value, normalized reserve
price, remaining-budget fraction, and remaining-time fraction. Clearing prices
and outcome labels are hidden until after the action. Training uses random
chronological windows of up to 500 training opportunities, with 0.35 budget units
per opportunity. PPO's 512-step rollouts turn 30,000 requested steps into 30,208
actual steps; LinUCB trains on 60 windows / 30,000 steps by default.

LinUCB is a myopic contextual-bandit baseline in a sequential budgeted problem,
not a proven optimal allocation algorithm. Test evaluation uses greedy LinUCB
actions and deterministic PPO actions without updates. The first configured seed,
not the best test seed, supplies the saved demo policies.

## Budget and API semantics

Each replay is one fixed-budget horizon, not an automatically renewing daily
budget. Proposed bids are capped by `max_bid` and remaining budget before clearing.
Settlement rejects overspending. Lost auctions cost zero; exhausted budgets yield
zero bids. The API bounds one stateless quote using caller-supplied budget state.
It does not reserve funds across concurrent requests. A production system would
need an atomic campaign ledger, idempotent settlement, authentication, monitoring,
and an independently measured latency target.

## Fair comparisons and interpretation

Policies replay identical test opportunities, competing prices, and potential
outcomes. No test-price resampling depends on the policy. Three training seeds
measure training sensitivity on one fixed holdout, not uncertainty across markets.

CTR = clicks / won impressions; CVR = conversions / clicks; CPM = spend per 1,000
won impressions. ROI = `(revenue - spend) / spend`, undefined at zero spend.
Report profit alongside spend and budget utilization. All configured seeds,
including underperforming policies, remain in the result files.

Unlike typical advertiser logs, the simulator has complete potential outcomes for
lost auctions. Replay profits are neither an online A/B test nor a causal estimate
of deployment uplift. Conversion value is an explicit assumption.

## Changes from the initial prototype

The initial snapshot remains in Git history. Its current-outcome history counts,
inconsistent feature order, custom PPO objective, mismatched weight filenames,
and soft budget controls made the old weights unsuitable for reuse.

This version retrains models, integrates SB3 PPO, and documents synthetic data
provenance. Supervised baselines are now logistic regression and boosted trees.
Unvalidated multi-campaign/Lagrangian variants and unused deployment scaffolding
are outside the supported scope. Generated data, model binaries, Python caches,
and debugging outputs are excluded from version control.

## Useful next experiments

1. Evaluate independent datasets and distribution shifts.
2. Generate out-of-fold training predictions for downstream policies.
3. Compare with a budget-aware optimization baseline.
4. Add delayed auction rewards and first-price auctions.
5. Adapt a documented public dataset with suitable counterfactual evaluation.
