import torch
from torch import nn
from transformers import BertPreTrainedModel, BertModel
from typing import Optional, Dict, List, Tuple, Union
import torch.nn.functional as F

class LegalBETOMultiTask(BertPreTrainedModel):
    def __init__(self, config):
        super().__init__(config)
        self.bert = BertModel(config)
        
        # Task-specific heads
        self.contract_classifier = nn.Linear(config.hidden_size, config.num_contract_labels)
        self.entity_classifier = nn.Linear(config.hidden_size, config.num_entity_labels)
        self.similarity_scorer = nn.Linear(config.hidden_size, 1)
        self.compliance_classifier = nn.Linear(config.hidden_size, config.num_compliance_labels)
        
        # Dropout for regularization
        self.dropout = nn.Dropout(config.hidden_dropout_prob)
        
        # Initialize weights
        self.init_weights()
        
    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        token_type_ids: Optional[torch.Tensor] = None,
        task_type: str = None,
        labels: Optional[torch.Tensor] = None,
        pair_input_ids: Optional[torch.Tensor] = None,
        pair_attention_mask: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, ...]:
        
        outputs = self.bert(
            input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
        )
        
        pooled_output = outputs[1]
        pooled_output = self.dropout(pooled_output)
        
        loss = None
        logits = None
        
        if task_type == "contract_analysis":
            logits = self.contract_classifier(pooled_output)
            if labels is not None:
                loss_fct = nn.CrossEntropyLoss()
                loss = loss_fct(logits.view(-1, self.config.num_contract_labels), labels.view(-1))
                
        elif task_type == "entity_recognition":
            sequence_output = outputs[0]
            logits = self.entity_classifier(sequence_output)
            if labels is not None:
                loss_fct = nn.CrossEntropyLoss()
                active_loss = attention_mask.view(-1) == 1
                active_logits = logits.view(-1, self.config.num_entity_labels)
                active_labels = labels.view(-1)
                loss = loss_fct(active_logits[active_loss], active_labels[active_loss])
                
        elif task_type == "similarity":
            if pair_input_ids is not None:
                pair_outputs = self.bert(
                    pair_input_ids,
                    attention_mask=pair_attention_mask,
                )
                pair_pooled_output = pair_outputs[1]
                pair_pooled_output = self.dropout(pair_pooled_output)
                
                # Compute similarity score
                similarity = self.similarity_scorer(
                    torch.abs(pooled_output - pair_pooled_output)
                )
                logits = similarity
                
                if labels is not None:
                    loss_fct = nn.MSELoss()
                    loss = loss_fct(similarity.squeeze(), labels.float())
                    
        elif task_type == "compliance":
            logits = self.compliance_classifier(pooled_output)
            if labels is not None:
                loss_fct = nn.BCEWithLogitsLoss()
                loss = loss_fct(logits, labels.float())
        
        return (loss, logits) if loss is not None else logits 