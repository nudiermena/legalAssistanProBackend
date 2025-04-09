import torch
from transformers import TrainingArguments
from legal_beto.model import LegalBETOMultiTask
from legal_beto.preprocessing import LegalTextPreprocessor
from legal_beto.data_collection import LegalDataCollector
from legal_beto.dataset import LegalDatasetPreparator
from legal_beto.trainer import LegalTrainer

def main():
    # Initialize data collector
    collector = LegalDataCollector()
    
    # Collect data
    print("Collecting court decisions...")
    court_decisions = collector.collect_court_decisions(2015, 2023)
    
    print("Collecting contracts...")
    contracts = collector.collect_contracts("path/to/contracts/directory")
    
    # Save raw data
    collector.save_dataset(court_decisions, "data/court_decisions.json")
    collector.save_dataset(contracts, "data/contracts.json")
    
    # Initialize preprocessor
    preprocessor = LegalTextPreprocessor()
    
    # Initialize dataset preparator
    preparator = LegalDatasetPreparator(preprocessor)
    
    # Prepare datasets
    print("Preparing datasets...")
    
    # Combine and prepare all texts and labels
    all_texts = [doc['text'] for doc in court_decisions + contracts]
    all_labels = [doc['type'] for doc in court_decisions + contracts]
    
    # Convert labels to integers
    label2id = {label: idx for idx, label in enumerate(set(all_labels))}
    labels = [label2id[label] for label in all_labels]
    
    # Prepare data for training
    datasets = preparator.prepare_classification_data(
        all_texts,
        labels,
        test_size=0.2,
        val_size=0.1
    )
    
    # Initialize model
    model = LegalBETOMultiTask.from_pretrained(
        "dccuchile/bert-base-spanish-wwm-uncased",
        num_labels=len(label2id)
    )
    
    # Set up training arguments
    training_args = TrainingArguments(
        output_dir="./legal_beto_results",
        num_train_epochs=3,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        warmup_steps=500,
        weight_decay=0.01,
        logging_dir="./logs",
        logging_steps=10,
        evaluation_strategy="steps",
        eval_steps=100,
        save_steps=100,
        load_best_model_at_end=True,
    )
    
    # Initialize trainer
    trainer = LegalTrainer(
        model=model,
        preprocessor=preprocessor,
        training_args=training_args
    )
    
    # Train the model
    print("Starting training...")
    trainer.train(
        train_texts=datasets['train']['input_ids'],
        train_labels=datasets['train']['labels'],
        eval_texts=datasets['validation']['input_ids'],
        eval_labels=datasets['validation']['labels']
    )
    
    # Save the final model
    model.save_pretrained("./legal_beto_final")
    preprocessor.tokenizer.save_pretrained("./legal_beto_final")

if __name__ == "__main__":
    main() 