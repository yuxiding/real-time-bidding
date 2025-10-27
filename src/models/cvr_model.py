import pandas as pd
import numpy as np
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
import torch
import torch.nn as nn
import torch.nn.functional as F
import os


class CVRDataset(Dataset):
    def __init__(self, dataframe: pd.DataFrame, feature_cols, label_col):
        self.X = dataframe[feature_cols].values.astype(np.float32)
        self.y = dataframe[label_col].values.astype(np.float32)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return torch.tensor(self.X[idx]), torch.tensor(self.y[idx])


class CVRModel(nn.Module):
    def __init__(self, input_dim, hidden_dims=[128, 64]):
        super(CVRModel, self).__init__()
        self.deep = nn.Sequential(
            nn.Linear(input_dim, hidden_dims[0]),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_dims[0]),
            nn.Linear(hidden_dims[0], hidden_dims[1]),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_dims[1]),
            nn.Linear(hidden_dims[1], 1)
        )

    def forward(self, x):
        x = self.deep(x)
        return torch.sigmoid(x.squeeze(1))


class CVREstimator:
    def __init__(self, input_dim, hidden_dims=[128, 64], lr=1e-3):
        self.model = CVRModel(input_dim, hidden_dims)
        self.criterion = nn.BCELoss()
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)

    def fit(self, train_loader, val_loader, epochs=10):
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

            self.model.eval()
            all_preds, all_labels = [], []
            with torch.no_grad():
                for X_batch, y_batch in val_loader:
                    preds = self.model(X_batch)
                    all_preds.append(preds.numpy())
                    all_labels.append(y_batch.numpy())
            self._evaluate(np.concatenate(all_labels), np.concatenate(all_preds))

    def _evaluate(self, y_true, y_pred):
        from sklearn.metrics import roc_auc_score, log_loss
        auc = roc_auc_score(y_true, y_pred)
        loss = log_loss(y_true, y_pred)
        print(f"Validation AUC: {auc:.4f}, LogLoss: {loss:.4f}")

    def predict(self, X):
        self.model.eval()
        with torch.no_grad():
            X_tensor = torch.tensor(X, dtype=torch.float32)
            return self.model(X_tensor).numpy()

    def save(self, path):
        torch.save(self.model.state_dict(), path)

    def load(self, path):
        self.model.load_state_dict(torch.load(path))


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--data', type=str, required=True, help='Path to dataset with features and label')
    parser.add_argument('--output', type=str, default='cvr_model.pt', help='Model save path')
    parser.add_argument('--label', type=str, default='converted', help='Label column name')
    args = parser.parse_args()

    df = pd.read_csv(args.data)
    feature_cols = [c for c in df.columns if c not in ['request_id', 'user_id', 'converted']]

    train_df, val_df = train_test_split(df, test_size=0.2, random_state=42)
    train_set = CVRDataset(train_df, feature_cols, args.label)
    val_set = CVRDataset(val_df, feature_cols, args.label)

    train_loader = DataLoader(train_set, batch_size=128, shuffle=True)
    val_loader = DataLoader(val_set, batch_size=128, shuffle=False)

    estimator = CVREstimator(input_dim=len(feature_cols))
    estimator.fit(train_loader, val_loader, epochs=10)
    estimator.save(args.output)
    print(f"Model saved to {args.output}")
