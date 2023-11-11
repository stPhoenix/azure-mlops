from typing import Tuple, Callable, Any, Union, List

import torch
from deltalake import DeltaTable
from pandas import DataFrame
from torch import Tensor
from torch.utils.data import Dataset

from stockpredict.settings import TORCH_DTYPE


class DeltaLakeDataset(Dataset):
    def __init__(self, input_path: str, label_name: Union[str, List[str]], transform: Callable[[DataFrame], Tensor],
                 target_transform: Callable[[DataFrame], Tensor]):
        self.label_name = label_name if isinstance(label_name, list) else [label_name]
        self.transform = transform
        self.target_transform = target_transform
        self.dt = DeltaTable(input_path)
        self.df: DataFrame = self.dt.to_pandas()

    def __getitem__(self, idx: Any) -> Tuple[Any, Any]:
        if torch.is_tensor(idx):
            idx = idx.tolist()

        data = self.df.iloc[[idx]]
        train = data.drop(columns=self.label_name)
        label = data[self.label_name]

        if self.transform:
            train = self.transform(train)
        if self.target_transform:
            label = self.target_transform(label)

        return train, label

    def __len__(self) -> int:
        return len(self.df)


def df_to_tensor(df: DataFrame) -> Tensor:
    tensor = torch.tensor(data=df.values, dtype=TORCH_DTYPE)
    shape = list(tensor.shape)
    if len(shape) < 2:
        tensor = torch.reshape(tensor, (*list(tensor.shape)[::-1], 1))
    return tensor
