import torch
import torch.nn as nn
import torch.nn.functional as F
import pandas as pd
import numpy as np
import os
from typing import List, Dict
from sklearn.model_selection import train_test_split
from torch.utils.data import Dataset, DataLoader


class CTRDataset(Dataset):
    def __init__(self, dataframe: pd.DataFrame, feature_cols: List[str], label_col: str):
        self.X = dataframe[feature_cols].values.astype(np.float32)
        self.y = dataframe[label_col].values.astype(np.float32)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return torch.tensor(self.X[idx]), torch.tensor(self.y[idx])


class WideAndDeep(nn.Module):
    def __init__(self, input_dim: int, hidden_dims: List[int] = [128, 64]):
        super(WideAndDeep, self).__init__()
        self.input_dim = input_dim

        # Wide 部分：线性回归
        self.wide = nn.Linear(input_dim, 1)

        # Deep 部分：多层感知机
        layers = []
        dims = [input_dim] + hidden_dims
        for i in range(len(dims) - 1):
            layers.append(nn.Linear(dims[i], dims[i + 1]))
            layers.append(nn.ReLU())
            layers.append(nn.BatchNorm1d(dims[i + 1]))
        self.deep = nn.Sequential(*layers)
        self.output_layer = nn.Linear(hidden_dims[-1] + 1, 1)

    def forward(self, x):
        wide_out = self.wide(x)  # shape: (batch, 1)
        deep_out = self.deep(x)  # shape: (batch, hidden)
        combined = torch.cat([wide_out, deep_out], dim=1)
        out = self.output_layer(combined)
        prob = torch.sigmoid(out.squeeze(1))
        return prob


class CTRModel:
    def __init__(self, input_dim: int, hidden_dims: List[int] = [128, 64], lr=1e-3):
        self.model = WideAndDeep(input_dim=input_dim, hidden_dims=hidden_dims)
        # binary cross entropy loss -> 0
        # ctrmodel(x1) => \hat{y1} = 0.75, y1 = 1 -> loss = -log(0.75) > 0 minimize
        # ctrmodel(x1) => \hat{y1} = 0.85, y1 = 1 -> loss = -log(0.85)
        # ctrmodel(x1) => \hat{y1} = 0.95, y1 = 1 -> loss = -log(0.95) -> 0
        # ctrmodel(x1) => \hat{y1} = 0.99 , y1 = 1 -> loss = -log(0.99) -> 0
        # ctrmodel(x1) => \hat{y1} = 0.995 , y1 = 1 -> loss = -log(0.995) -> 0
        self.criterion = nn.BCELoss() 
        # 梯度的反向传播
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)

    def fit(self, train_loader: DataLoader, val_loader: DataLoader, epochs: int = 10):
        for epoch in range(epochs):
            self.model.train()
            total_loss = 0
            for X_batch, y_batch in train_loader:
                self.optimizer.zero_grad()
                preds = self.model(X_batch)
                loss = self.criterion(preds, y_batch)
                loss.backward()
                self.optimizer.step()
                total_loss += loss.item()
            print(f"Epoch {epoch+1}/{epochs}, Train Loss: {total_loss/len(train_loader):.4f}")

            # Validation
            self.model.eval()
            all_preds = []
            all_labels = []
            with torch.no_grad():
                for X_batch, y_batch in val_loader:
                    preds = self.model(X_batch)
                    all_preds.append(preds.detach().numpy())
                    all_labels.append(y_batch.numpy())
            pred_concat = np.concatenate(all_preds)
            label_concat = np.concatenate(all_labels)
            auc = self._compute_auc(label_concat, pred_concat)
            print(f"Validation AUC: {auc:.4f}")

    def predict(self, X: np.ndarray) -> np.ndarray:
        self.model.eval()
        with torch.no_grad():
            X_tensor = torch.tensor(X, dtype=torch.float32)
            preds = self.model(X_tensor)
            return preds.numpy()

    def save(self, path: str):
        torch.save(self.model.state_dict(), path)

    def load(self, path: str):
        self.model.load_state_dict(torch.load(path))

    def _compute_auc(self, y_true: np.ndarray, y_score: np.ndarray) -> float:
        from sklearn.metrics import roc_auc_score
        return roc_auc_score(y_true, y_score)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--data', type=str, required=True, help='CSV with features and label')
    parser.add_argument('--output', type=str, default='ctr_model.pt', help='Where to save the trained model')
    parser.add_argument('--label', type=str, default='clicked')
    args = parser.parse_args()

    df = pd.read_csv(args.data)
    feature_cols = [col for col in df.columns if col not in ['request_id', 'user_id', 'clicked']]

    train_df, val_df = train_test_split(df, test_size=0.2, random_state=42)
    train_dataset = CTRDataset(train_df, feature_cols, args.label)
    val_dataset = CTRDataset(val_df, feature_cols, args.label)

    train_loader = DataLoader(train_dataset, batch_size=128, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=128, shuffle=False)

    model = CTRModel(input_dim=len(feature_cols))
    model.fit(train_loader, val_loader, epochs=10)
    model.save(args.output)
    print(f"Model saved to {args.output}")
