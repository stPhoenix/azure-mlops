import argparse
import logging
import os.path
import shutil
from typing import Any

import lightning.pytorch as pl
import mlflow.pytorch
from stockpredict.model.network import StockNN
from torch.utils.data import DataLoader, random_split
from stockpredict.train.dataset import DeltaLakeDataset, df_to_tensor

from stockpredict.settings import NETWORK_OUT_LABELS, MODEL_NAME

workers = os.cpu_count()


def save_model(checkpoint_path: str, output_model: str) -> None:
    model_path = os.path.join(output_model, MODEL_NAME)
    shutil.copy2(checkpoint_path, model_path)

    logging.info(f"saved model to {model_path}")


def run_train(input_data: str, batch_size: int, shuffle: bool = True, learning_rate: float = 0.01, epochs: int = 100,
              output_model: Any = './output/', progress_bar: bool = False):
    mlflow.pytorch.autolog()
    logging.info("starting flow")
    dataset = DeltaLakeDataset(input_path=input_data,
                               label_name=NETWORK_OUT_LABELS,
                               transform=df_to_tensor,
                               target_transform=df_to_tensor)
    train, test = random_split(dataset=dataset, lengths=[0.8, 0.2])

    train_dataloader = DataLoader(dataset=train,
                                  batch_size=batch_size,
                                  shuffle=shuffle,
                                  num_workers=workers
                                  )
    test_dataloader = DataLoader(dataset=test,
                                 shuffle=False,
                                 num_workers=workers
                                 )
    in_features = list(train[0][0].shape)[-1]
    model = StockNN(in_features, out_labels=len(NETWORK_OUT_LABELS), learning_rate=learning_rate)

    trainer = pl.Trainer(min_epochs=epochs, max_epochs=epochs, default_root_dir=output_model,
                         enable_progress_bar=progress_bar, logger=True)
    trainer.fit(model, train_dataloaders=train_dataloader)
    trainer.test(model, dataloaders=test_dataloader)

    save_model(trainer.checkpoint_callback.best_model_path, output_model)

    logging.info("finished training")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_data", type=str)
    parser.add_argument("--batch_size", type=int)
    parser.add_argument("--shuffle", type=bool)
    parser.add_argument("--learning_rate", type=float)
    parser.add_argument("--epochs", type=int)
    parser.add_argument("--output_model", type=str)

    args = parser.parse_args()
    logging.info(args.input_data)

    run_train(args.input_data,
              args.batch_size,
              args.shuffle,
              args.learning_rate,
              args.epochs,
              args.output_model
              )
