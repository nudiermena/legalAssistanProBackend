import torch
from torch.utils.data import Dataset
import pandas as pd
import json
from typing import List, Dict, Any, Optional
from sklearn.model_selection import train_test_split

class LegalDatasetPreparator:
    def __init__(self, preprocessor):
        self.preprocessor = preprocessor

    def prepare_classification_data(
        self,
        texts: List[str],
        labels: List[int],
        test_size: float = 0.2,
        val_size: float = 0.1
    ) -> Dict[str, torch.Tensor]:
        """Prepare data for classification tasks."""
        # Split data into train, validation, and test sets
        train_texts, test_texts, train_labels, test_labels = train_test_split(
            texts, labels, test_size=test_size, stratify=labels
        )
        
        train_texts, val_texts, train_labels, val_labels = train_test_split(
            train_texts, train_labels,
            test_size=val_size/(1-test_size),
            stratify=train_labels
        )
        
        # Prepare each set
        train_data = self._prepare_batch(train_texts, train_labels)
        val_data = self._prepare_batch(val_texts, val_labels)
        test_data = self._prepare_batch(test_texts, test_labels)
        
        return {
            'train': train_data,
            'validation': val_data,
            'test': test_data
        }

    def _prepare_batch(
        self,
        texts: List[str],
        labels: List[int]
    ) -> Dict[str, torch.Tensor]:
        """Prepare a batch of data."""
        encodings = self.preprocessor.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encodings['input_ids'],
            'attention_mask': encodings['attention_mask'],
            'labels': torch.tensor(labels)
        }

class LegalDataset(Dataset):
    def __init__(
        self,
        encodings: Dict[str, torch.Tensor],
        labels: torch.Tensor
    ):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        item = {key: val[idx] for key, val in self.encodings.items()}
        item['labels'] = self.labels[idx]
        return item

    def __len__(self) -> int:
        return len(self.labels) 