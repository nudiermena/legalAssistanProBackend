import re
from typing import Dict, List, Any, Optional, Union
from transformers import AutoTokenizer
import spacy
import pandas as pd

class LegalTextPreprocessor:
    def __init__(self, model_name: str = "dccuchile/bert-base-spanish-wwm-uncased"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.nlp = spacy.load("es_core_news_lg")
        
        # Legal document structure patterns
        self.section_patterns = {
            "articulo": r"Art[íi]culo\s+\d+\.?",
            "clausula": r"Cl[áa]usula\s+\d+\.?",
            "considerando": r"Considerando\s+\d+\.?",
            "parrafo": r"P[áa]rrafo\s+\d+\.?",
        }
        
        # Legal entity patterns
        self.entity_patterns = {
            "persona_juridica": r"[A-Z][A-Za-z]*\s+S\.?A\.?S?\.?",
            "documento": r"[A-Z]+\s+No\.\s+\d+",
            "fecha": r"\d{1,2}\s+de\s+[a-zA-Z]+\s+de\s+\d{4}",
        }
        
    def clean_text(self, text: str) -> str:
        """Clean and normalize legal text."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Normalize quotes
        text = re.sub(r'["""]', '"', text)
        
        # Normalize dashes
        text = re.sub(r'[–—]', '-', text)
        
        # Normalize ellipsis
        text = re.sub(r'\.{3,}', '...', text)
        
        return text
        
    def extract_document_structure(self, text: str) -> Dict[str, List[str]]:
        """Extract structured elements from legal text."""
        structure = {
            "sections": [],
            "articles": [],
            "clauses": [],
            "paragraphs": []
        }
        
        # Split into sections
        sections = re.split(r'\n{2,}', text)
        
        for section in sections:
            # Identify section type
            for pattern_name, pattern in self.section_patterns.items():
                if re.match(pattern, section.strip()):
                    structure[f"{pattern_name}s"].append(section.strip())
                    break
                    
        return structure
        
    def prepare_for_contract_analysis(
        self, 
        text: str, 
        max_length: int = 512
    ) -> Dict[str, torch.Tensor]:
        """Prepare text for contract analysis task."""
        # Clean text
        text = self.clean_text(text)
        
        # Tokenize
        encoding = self.tokenizer(
            text,
            max_length=max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        return encoding
        
    def prepare_for_entity_recognition(
        self, 
        text: str,
        max_length: int = 512
    ) -> Dict[str, torch.Tensor]:
        """Prepare text for legal entity recognition."""
        # Process with spaCy
        doc = self.nlp(text)
        
        # Extract entities
        entities = []
        for ent in doc.ents:
            if ent.label_ in ["ORG", "PER", "LOC", "MISC"]:
                entities.append({
                    "text": ent.text,
                    "label": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char
                })
                
        # Tokenize
        encoding = self.tokenizer(
            text,
            max_length=max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        return {
            "encoding": encoding,
            "entities": entities
        }
        
    def prepare_for_similarity(
        self,
        text1: str,
        text2: str,
        max_length: int = 512
    ) -> Dict[str, torch.Tensor]:
        """Prepare text pair for similarity analysis."""
        # Clean texts
        text1 = self.clean_text(text1)
        text2 = self.clean_text(text2)
        
        # Tokenize both texts
        encoding1 = self.tokenizer(
            text1,
            max_length=max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        encoding2 = self.tokenizer(
            text2,
            max_length=max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        return {
            "encoding1": encoding1,
            "encoding2": encoding2
        } 