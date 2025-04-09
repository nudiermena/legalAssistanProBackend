from transformers import Trainer, TrainingArguments
from typing import Dict, List, Optional
import torch
from torch.utils.data import Dataset
import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

class LegalDataset(Dataset):
    def __init__(
        self,
        texts: List[str],
        labels: List[int],
        task_types: List[str],
        preprocessor: LegalTextPreprocessor,
        pair_texts: Optional[List[str]] = None
    ):
        self.texts = texts
        self.labels = labels
        self.task_types = task_types
        self.preprocessor = preprocessor
        self.pair_texts = pair_texts
        
    def __len__(self):
        return len(self.texts)
        
    def __getitem__(self, idx):
        text = self.texts[idx]
        label = self.labels[idx]
        task_type = self.task_types[idx]
        
        if task_type == "similarity" and self.pair_texts is not None:
            prepared = self.preprocessor.prepare_for_similarity(
                text,
                self.pair_texts[idx]
            )
            return {
                "input_ids": prepared["encoding1"]["input_ids"],
                "attention_mask": prepared["encoding1"]["attention_mask"],
                "pair_input_ids": prepared["encoding2"]["input_ids"],
                "pair_attention_mask": prepared["encoding2"]["attention_mask"],
                "labels": torch.tensor(label),
                "task_type": task_type
            }
        else:
            prepared = self.preprocessor.prepare_for_contract_analysis(text)
            return {
                "input_ids": prepared["input_ids"],
                "attention_mask": prepared["attention_mask"],
                "labels": torch.tensor(label),
                "task_type": task_type
            }

class LegalTrainer:
    def __init__(
        self,
        model,
        preprocessor: LegalTextPreprocessor,
        training_args: TrainingArguments
    ):
        self.model = model
        self.preprocessor = preprocessor
        self.training_args = training_args
        
    def compute_metrics(self, pred):
        labels = pred.label_ids
        preds = pred.predictions.argmax(-1)
        
        precision, recall, f1, _ = precision_recall_fscore_support(
            labels,
            preds,
            average='weighted'
        )
        
        acc = accuracy_score(labels, preds)
        
        return {
            'accuracy': acc,
            'f1': f1,
            'precision': precision,
            'recall': recall
        }
        
    def train(
        self,
        train_texts: List[str],
        train_labels: List[int],
        train_task_types: List[str],
        eval_texts: Optional[List[str]] = None,
        eval_labels: Optional[List[int]] = None,
        eval_task_types: Optional[List[str]] = None,
        pair_train_texts: Optional[List[str]] = None,
        pair_eval_texts: Optional[List[str]] = None
    ):
        # Create datasets
        train_dataset = LegalDataset(
            train_texts,
            train_labels,
            train_task_types,
            self.preprocessor,
            pair_train_texts
        )
        
        eval_dataset = None
        if eval_texts is not None:
            eval_dataset = LegalDataset(
                eval_texts,
                eval_labels,
                eval_task_types,
                self.preprocessor,
                pair_eval_texts
            )
            
        # Initialize trainer
        trainer = Trainer(
            model=self.model,
            args=self.training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            compute_metrics=self.compute_metrics
        )
        
        # Train the model
        trainer.train()
        
        # Save the model
        trainer.save_model()
        self.preprocessor.tokenizer.save_pretrained(
            self.training_args.output_dir
        ) 