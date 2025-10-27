# real-time-bidding
End-to-end ad bidding simulator integrating supervised CTR/CVR prediction and reinforcement learning for dynamic bid pricing and constrained budget control.
AuroraBid/
│── README.md # This file
│── requirements.txt # Python dependencies
│── setup.py # Optional: for pip install -e .
│
├── config/
│ ├── training.yaml # RL algorithm and hyperparameters
│ ├── serving.yaml # Online serving configuration
│ ├── budget.yaml # Budget pacing and constraints
│ └── logging.yaml # Logging configuration
│
├── data/
│ ├── raw/ # Raw logs (impression, click, conversion)
│ ├── processed/ # Cleaned and feature-engineered data
│ └── schema.json # Data schema definition
│
├── src/
│ ├── features/ # Feature engineering modules
│ │ ├── user_features.py
│ │ ├── context_features.py
│ │ ├── history_features.py
│ │ └── feature_store.py # Unified interface for Kafka/Redis/local mock
│ │
│ ├── simulation/ # Real-time bidding simulation
│ │ ├── bid_simulator.py
│ │ ├── auction_engine.py
│ │ └── market_env.py # Gym environment (state/action/reward)
│ │
│ ├── models/ # Prediction & RL models
│ │ ├── ctr_model.py
│ │ ├── cvr_model.py
│ │ ├── bid_landscape.py
│ │ ├── rl_agent.py # PPO/DDPG/TD3
│ │ └── bandit_agent.py # LinUCB/Thompson/NeuralUCB
│ │
│ ├── bidding/ # Bidding & budget control logic
│ │ ├── bid_strategy.py
│ │ ├── budget_controller.py
│ │ ├── multi_campaign_rl.py
│ │ └── constrained_rl.py
│ │
│ ├── serving/ # Lightweight serving prototype
│ │ ├── api.py # FastAPI endpoints (/bid, /health)
│ │ ├── model_server.py
│ │ └── latency_monitor.py
│ │
│ └── utils/
│ ├── metrics.py
│ ├── logger.py
│ └── helpers.py
│
├── training/
│ ├── offline_rl.py
│ ├── online_rl.py
│ ├── hyperparam_search.py
│ ├── replay_buffer.py
│ └── reward_design.py
│
├── experiments/
│ ├── ab_test_results.csv
│ ├── rl_vs_rulebased.md
│ └── latency_benchmark.md
│
└── reports/
├── visualizations/
├── uplift_summary.md
├── business_value.md
└── system_architecture.pn
