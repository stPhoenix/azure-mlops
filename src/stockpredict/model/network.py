import lightning.pytorch as pl
import torch
import torch.nn as nn
from lightning.pytorch.utilities.types import OptimizerLRScheduler, STEP_OUTPUT
from torch.nn.modules.loss import _Loss

from stockpredict.settings import TORCH_DTYPE


class StockNN(pl.LightningModule):
    def __init__(self, in_features: int, out_labels: int, learning_rate: float = 0.001, loss_fn: _Loss = nn.L1Loss(),
                 lstm_layers: int = 1, lstm_dropout: int = 0):
        super().__init__()
        self.save_hyperparameters()
        self.accuracy = lambda pred, y: torch.abs(torch.mean((pred / y) * 100))
        self.learning_rate = learning_rate
        self.loss_fn = loss_fn
        self.hidden = in_features * 25
        self.lstm = nn.LSTM(input_size=in_features,
                            hidden_size=self.hidden,
                            num_layers=lstm_layers,
                            dropout=lstm_dropout,
                            batch_first=True,
                            dtype=TORCH_DTYPE)
        self.price_predictor = nn.Sequential(
            nn.Linear(self.hidden, in_features, dtype=TORCH_DTYPE),
            nn.ReLU(),
            nn.Linear(in_features, self.hidden, dtype=TORCH_DTYPE),
            nn.ReLU(),
            nn.Linear(self.hidden, in_features, dtype=TORCH_DTYPE),
            nn.ReLU(),
            nn.Linear(in_features, out_labels, dtype=TORCH_DTYPE),

        )

    def forward(self, x):
        k, h = self.lstm(x)
        return self.price_predictor(k)

    def configure_optimizers(self) -> OptimizerLRScheduler:
        return torch.optim.SGD(self.parameters(), lr=self.learning_rate)

    def training_step(self, batch, batch_idx: int) -> STEP_OUTPUT:
        x, y = batch
        pred = self(x)
        loss = self.loss_fn(pred, y)
        self.log("train_loss", loss)
        self.log("train_accuracy", self.accuracy(pred, y))
        for item in pred:
            self.log("train_pred", item)
        for item in y:
            self.log("train_y", item)
        return loss

    def test_step(self, batch, batch_idx: int) -> STEP_OUTPUT:
        x, y = batch
        pred = self(x)
        loss = self.loss_fn(pred, y)
        self.log("test_loss", loss)
        self.log("test_accuracy", self.accuracy(pred, y))
        for item in pred:
            self.log("test_pred", item)
        for item in y:
            self.log("test_y", item)

        return loss
