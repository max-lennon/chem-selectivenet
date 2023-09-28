import os
import sys

base = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../')
sys.path.append(base)

from collections import namedtuple

import pandas as pd

import torch
import torchvision
from torch.utils.data import Dataset

class DrugOODDataset(Dataset):
    def __init__(self, file_name, input_size):

        df = pd.read_csv(file_name)

        self.labels = df['Label'].values
        
        # Extract data columns based on the "fp_#" format
        data_columns = [f'fp_{i}' for i in range(1, input_size + 1)]
        self.data = df[data_columns].values.astype(float)
        
    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        sample = (
            torch.tensor(self.data[idx], dtype=torch.float32),
            torch.tensor(self.labels[idx], dtype=torch.int64)
        )
        return sample
    


class ChemDatasetBuilder(object):

    DC = namedtuple('DatasetConfig', ['dataclass', 'splits', 'input_size', 'num_classes'])
    drugood_splits = ['train', 'val', 'test']

    DATASET_CONFIG = {
        'dataset1' : DC(DrugOODDataset, drugood_splits, 1024, 2),
        'dataset2' : DC(DrugOODDataset, drugood_splits, 1024, 2),
        'dataset3' : DC(DrugOODDataset, drugood_splits, 1024, 2),
        'dataset4' : DC(DrugOODDataset, drugood_splits, 1024, 2)
    }

    def __init__(self, name:str, root_path:str):
        """
        Args
        - name: name of dataset
        - root_path: root path to datasets
        """
        if name not in self.DATASET_CONFIG.keys():
            raise ValueError('name of dataset is invalid')
        self.name = name
        self.root_path = os.path.join(root_path, self.name)

    def __call__(self, split:str, ood:bool):
        input_size = self.DATASET_CONFIG[self.name].input_size
        file_name = os.path.join(self.root_path, f"{split}{('_'+('ood' if ood else 'id') if split !='train' else '')}.csv")

        dataset = self.DATASET_CONFIG[self.name].dataclass(file_name, input_size)

        return dataset
    
    @property
    def input_size(self):
        return self.DATASET_CONFIG[self.name].input_size

    @property
    def num_classes(self):
        return self.DATASET_CONFIG[self.name].num_classes

class DatasetBuilder(object):
    # tuple for dataset config
    DC = namedtuple('DatasetConfig', ['mean', 'std', 'input_size', 'num_classes'])
    
    DATASET_CONFIG = {
        'svhn' :   DC([0.43768210, 0.44376970, 0.47280442], [0.19803012, 0.20101562, 0.19703614], 32, 10),
        'cifar10': DC([0.49139968, 0.48215841, 0.44653091], [0.24703223, 0.24348513, 0.26158784], 32, 10),
    } 

    def __init__(self, name:str, root_path:str):
        """
        Args
        - name: name of dataset
        - root_path: root path to datasets
        """
        if name not in self.DATASET_CONFIG.keys():
            raise ValueError('name of dataset is invalid')
        self.name = name
        self.root_path = os.path.join(root_path, self.name)

    def __call__(self, train:bool, normalize:bool):
        input_size = self.DATASET_CONFIG[self.name].input_size
        transform = self._get_transform(self.name, input_size, train, normalize)
        if self.name == 'svhn':
            dataset = torchvision.datasets.SVHN(root=self.root_path, split='train' if self.train else 'test', transform=transform, download=True)
        elif self.name == 'cifar10':
            dataset = torchvision.datasets.CIFAR10(root=self.root_path, train=train, transform=transform, download=True)
        else: 
            raise NotImplementedError 

        return dataset

    def _get_transform(self, name:str, input_size:int, train:bool, normalize:bool):
        transform = []

        # arugmentation
        if train:
            transform.extend([
                torchvision.transforms.RandomHorizontalFlip(),
            ])

        else:
            pass

        # to tensor
        transform.extend([torchvision.transforms.ToTensor(),])

        # normalize
        if normalize:
            transform.extend([
                torchvision.transforms.Normalize(mean=self.DATASET_CONFIG[name].mean, std=self.DATASET_CONFIG[name].std),
            ])

        return torchvision.transforms.Compose(transform)
    
    @property
    def input_size(self):
        return self.DATASET_CONFIG[self.name].input_size

    @property
    def num_classes(self):
        return self.DATASET_CONFIG[self.name].num_classes