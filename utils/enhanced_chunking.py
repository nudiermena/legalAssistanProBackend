"""
Enhanced Chunking Utilities for RAG
Provides advanced chunking strategies with proper metadata tracking
"""

import re
import uuid
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import tiktoken

class ChunkingStrategy(Enum):
    """Available chunking strategies"""
    FIXED_CHAR = "fixed_char"
    FIXED_TOKEN = "fixed_token"
    SENTENCE_BOUNDARY = "sentence_boundary"
    PARAGRAPH_BOUNDARY = "paragraph_boundary"
    LEGAL_STRUCTURE = "legal_structure"
    SEMANTIC = "semantic"

@dataclass
class ChunkMetadata:
    """Metadata for a text chunk"""
    chunk_index: int
    chunk_size: int
    chunk_overlap: int
    parent_document_id: str
    total_chunks: int
    start_position: int
    end_position: int
    chunk_type: str = "text"
    section: Optional[str] = None
    subsection: Optional[str] = None
    paragraph: Optional[int] = None
    sentence: Optional[int] = None
    legal_structure: Optional[Dict[str, Any]] = None
    additional_metadata: Optional[Dict[str, Any]] = None

@dataclass
class ChunkResult:
    """Result of chunking operation"""
    content: str
    metadata: ChunkMetadata
    vector_embedding: Optional[List[float]] = None

class EnhancedChunker:
    """Enhanced chunker with multiple strategies and metadata tracking"""
    
    def __init__(self, 
                 strategy: ChunkingStrategy = ChunkingStrategy.FIXED_CHAR,
                 max_chars: int = 3000,
                 max_tokens: int = 100000,
                 overlap_chars: int = 200,
                 overlap_tokens: int = 50,
                 model_name: str = "gpt-4"):
        self.strategy = strategy
        self.max_chars = max_chars
        self.max_tokens = max_tokens
        self.overlap_chars = overlap_chars
        self.overlap_tokens = overlap_tokens
        self.model_name = model_name
        
        # Initialize tokenizer for token-based chunking
        if strategy in [ChunkingStrategy.FIXED_TOKEN, ChunkingStrategy.SEMANTIC]:
            try:
                self.tokenizer = tiktoken.encoding_for_model(model_name)
            except Exception:
                self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Legal document patterns
        self.legal_patterns = {
            'article': r'Artículo\s+\d+',
            'section': r'Sección\s+\d+',
            'chapter': r'Capítulo\s+\d+',
            'title': r'Título\s+\d+',
            'paragraph': r'Parágrafo\s+\d+',
            'clause': r'Cláusula\s+\d+',
            'article_short': r'Art\.\s*\d+',
            'section_short': r'Sec\.\s*\d+',
            'paragraph_short': r'Par\.\s*\d+',
        }
    
    def chunk_text(self, 
                   text: str, 
                   parent_document_id: str,
                   document_type: str = "legal_document",
                   additional_metadata: Optional[Dict[str, Any]] = None) -> List[ChunkResult]:
        """
        Chunk text using the specified strategy
        
        Args:
            text: Text to chunk
            parent_document_id: ID of the parent document
            document_type: Type of document for structure-aware chunking
            additional_metadata: Additional metadata to include
            
        Returns:
            List of ChunkResult objects
        """
        if self.strategy == ChunkingStrategy.FIXED_CHAR:
            return self._chunk_fixed_char(text, parent_document_id, additional_metadata)
        elif self.strategy == ChunkingStrategy.FIXED_TOKEN:
            return self._chunk_fixed_token(text, parent_document_id, additional_metadata)
        elif self.strategy == ChunkingStrategy.SENTENCE_BOUNDARY:
            return self._chunk_sentence_boundary(text, parent_document_id, additional_metadata)
        elif self.strategy == ChunkingStrategy.PARAGRAPH_BOUNDARY:
            return self._chunk_paragraph_boundary(text, parent_document_id, additional_metadata)
        elif self.strategy == ChunkingStrategy.LEGAL_STRUCTURE:
            return self._chunk_legal_structure(text, parent_document_id, document_type, additional_metadata)
        else:
            raise ValueError(f"Unsupported chunking strategy: {self.strategy}")
    
    def _chunk_fixed_char(self, text: str, parent_document_id: str, additional_metadata: Optional[Dict[str, Any]] = None) -> List[ChunkResult]:
        """Fixed character-based chunking with overlap"""
        chunks = []
        i = 0
        n = len(text)
        chunk_index = 0
        
        while i < n:
            end = min(i + self.max_chars, n)
            chunk_content = text[i:end]
            
            # Create metadata
            metadata = ChunkMetadata(
                chunk_index=chunk_index,
                chunk_size=len(chunk_content),
                chunk_overlap=self.overlap_chars,
                parent_document_id=parent_document_id,
                total_chunks=0,  # Will be updated after all chunks are created
                start_position=i,
                end_position=end,
                chunk_type="text",
                additional_metadata=additional_metadata
            )
            
            chunks.append(ChunkResult(
                content=chunk_content,
                metadata=metadata
            ))
            
            if end == n:
                break
            
            # Move to next chunk with overlap
            i = end - self.overlap_chars
            if i < 0:
                i = 0
            chunk_index += 1
        
        # Update total_chunks in all metadata
        for chunk in chunks:
            chunk.metadata.total_chunks = len(chunks)
        
        return chunks
    
    def _chunk_fixed_token(self, text: str, parent_document_id: str, additional_metadata: Optional[Dict[str, Any]] = None) -> List[ChunkResult]:
        """Fixed token-based chunking with overlap"""
        tokens = self.tokenizer.encode(text)
        total_tokens = len(tokens)
        
        if total_tokens <= self.max_tokens:
            metadata = ChunkMetadata(
                chunk_index=0,
                chunk_size=len(text),
                chunk_overlap=0,
                parent_document_id=parent_document_id,
                total_chunks=1,
                start_position=0,
                end_position=len(text),
                chunk_type="text",
                additional_metadata=additional_metadata
            )
            return [ChunkResult(content=text, metadata=metadata)]
        
        chunks = []
        i = 0
        chunk_index = 0
        
        while i < total_tokens:
            end = min(i + self.max_tokens, total_tokens)
            chunk_tokens = tokens[i:end]
            chunk_content = self.tokenizer.decode(chunk_tokens)
            
            # Find actual character positions
            start_pos = len(self.tokenizer.decode(tokens[:i]))
            end_pos = len(self.tokenizer.decode(tokens[:end]))
            
            metadata = ChunkMetadata(
                chunk_index=chunk_index,
                chunk_size=len(chunk_content),
                chunk_overlap=self.overlap_tokens,
                parent_document_id=parent_document_id,
                total_chunks=0,  # Will be updated
                start_position=start_pos,
                end_position=end_pos,
                chunk_type="text",
                additional_metadata=additional_metadata
            )
            
            chunks.append(ChunkResult(
                content=chunk_content,
                metadata=metadata
            ))
            
            if end == total_tokens:
                break
            
            # Move to next chunk with overlap
            i = end - self.overlap_tokens
            if i < 0:
                i = 0
            chunk_index += 1
        
        # Update total_chunks
        for chunk in chunks:
            chunk.metadata.total_chunks = len(chunks)
        
        return chunks
    
    def _chunk_sentence_boundary(self, text: str, parent_document_id: str, additional_metadata: Optional[Dict[str, Any]] = None) -> List[ChunkResult]:
        """Chunk at sentence boundaries"""
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = ""
        chunk_index = 0
        char_count = 0
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= self.max_chars:
                current_chunk += sentence + " "
                char_count += len(sentence) + 1
            else:
                if current_chunk:
                    # Create chunk
                    metadata = ChunkMetadata(
                        chunk_index=chunk_index,
                        chunk_size=len(current_chunk.strip()),
                        chunk_overlap=0,
                        parent_document_id=parent_document_id,
                        total_chunks=0,  # Will be updated
                        start_position=char_count - len(current_chunk),
                        end_position=char_count,
                        chunk_type="sentence_boundary",
                        additional_metadata=additional_metadata
                    )
                    
                    chunks.append(ChunkResult(
                        content=current_chunk.strip(),
                        metadata=metadata
                    ))
                    chunk_index += 1
                
                current_chunk = sentence + " "
                char_count += len(sentence) + 1
        
        # Add final chunk
        if current_chunk:
            metadata = ChunkMetadata(
                chunk_index=chunk_index,
                chunk_size=len(current_chunk.strip()),
                chunk_overlap=0,
                parent_document_id=parent_document_id,
                total_chunks=0,  # Will be updated
                start_position=char_count - len(current_chunk),
                end_position=char_count,
                chunk_type="sentence_boundary",
                additional_metadata=additional_metadata
            )
            
            chunks.append(ChunkResult(
                content=current_chunk.strip(),
                metadata=metadata
            ))
        
        # Update total_chunks
        for chunk in chunks:
            chunk.metadata.total_chunks = len(chunks)
        
        return chunks
    
    def _chunk_paragraph_boundary(self, text: str, parent_document_id: str, additional_metadata: Optional[Dict[str, Any]] = None) -> List[ChunkResult]:
        """Chunk at paragraph boundaries"""
        paragraphs = text.split('\n\n')
        
        chunks = []
        current_chunk = ""
        chunk_index = 0
        char_count = 0
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) <= self.max_chars:
                current_chunk += paragraph + "\n\n"
                char_count += len(paragraph) + 2
            else:
                if current_chunk:
                    metadata = ChunkMetadata(
                        chunk_index=chunk_index,
                        chunk_size=len(current_chunk.strip()),
                        chunk_overlap=0,
                        parent_document_id=parent_document_id,
                        total_chunks=0,  # Will be updated
                        start_position=char_count - len(current_chunk),
                        end_position=char_count,
                        chunk_type="paragraph_boundary",
                        additional_metadata=additional_metadata
                    )
                    
                    chunks.append(ChunkResult(
                        content=current_chunk.strip(),
                        metadata=metadata
                    ))
                    chunk_index += 1
                
                current_chunk = paragraph + "\n\n"
                char_count += len(paragraph) + 2
        
        # Add final chunk
        if current_chunk:
            metadata = ChunkMetadata(
                chunk_index=chunk_index,
                chunk_size=len(current_chunk.strip()),
                chunk_overlap=0,
                parent_document_id=parent_document_id,
                total_chunks=0,  # Will be updated
                start_position=char_count - len(current_chunk),
                end_position=char_count,
                chunk_type="paragraph_boundary",
                additional_metadata=additional_metadata
            )
            
            chunks.append(ChunkResult(
                content=current_chunk.strip(),
                metadata=metadata
            ))
        
        # Update total_chunks
        for chunk in chunks:
            chunk.metadata.total_chunks = len(chunks)
        
        return chunks
    
    def _chunk_legal_structure(self, text: str, parent_document_id: str, document_type: str, additional_metadata: Optional[Dict[str, Any]] = None) -> List[ChunkResult]:
        """Chunk based on legal document structure"""
        chunks = []
        chunk_index = 0
        
        # Find legal structure markers
        structure_markers = []
        for pattern_name, pattern in self.legal_patterns.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                structure_markers.append({
                    'position': match.start(),
                    'type': pattern_name,
                    'text': match.group(),
                    'section': self._extract_section_info(match.group())
                })
        
        # Sort by position
        structure_markers.sort(key=lambda x: x['position'])
        
        if not structure_markers:
            # Fallback to paragraph chunking
            return self._chunk_paragraph_boundary(text, parent_document_id, additional_metadata)
        
        # Create chunks based on structure
        for i, marker in enumerate(structure_markers):
            start_pos = marker['position']
            end_pos = structure_markers[i + 1]['position'] if i + 1 < len(structure_markers) else len(text)
            
            chunk_content = text[start_pos:end_pos].strip()
            
            if len(chunk_content) > self.max_chars:
                # If section is too large, sub-chunk it
                sub_chunks = self._chunk_fixed_char(chunk_content, parent_document_id, additional_metadata)
                for sub_chunk in sub_chunks:
                    sub_chunk.metadata.section = marker['section']
                    sub_chunk.metadata.legal_structure = {
                        'structure_type': marker['type'],
                        'structure_text': marker['text'],
                        'section_info': marker['section']
                    }
                    sub_chunk.metadata.chunk_index = chunk_index
                    chunk_index += 1
                chunks.extend(sub_chunks)
            else:
                metadata = ChunkMetadata(
                    chunk_index=chunk_index,
                    chunk_size=len(chunk_content),
                    chunk_overlap=0,
                    parent_document_id=parent_document_id,
                    total_chunks=0,  # Will be updated
                    start_position=start_pos,
                    end_position=end_pos,
                    chunk_type="legal_structure",
                    section=marker['section'],
                    legal_structure={
                        'structure_type': marker['type'],
                        'structure_text': marker['text'],
                        'section_info': marker['section']
                    },
                    additional_metadata=additional_metadata
                )
                
                chunks.append(ChunkResult(
                    content=chunk_content,
                    metadata=metadata
                ))
                chunk_index += 1
        
        # Update total_chunks
        for chunk in chunks:
            chunk.metadata.total_chunks = len(chunks)
        
        return chunks
    
    def _extract_section_info(self, structure_text: str) -> str:
        """Extract section information from structure text"""
        # Extract numbers and text from structure markers
        numbers = re.findall(r'\d+', structure_text)
        if numbers:
            return f"Section {numbers[0]}"
        return structure_text

def create_chunk_metadata_dict(chunk_result: ChunkResult) -> Dict[str, Any]:
    """Convert ChunkResult to dictionary format for database insertion"""
    metadata = chunk_result.metadata
    
    return {
        'chunk_index': metadata.chunk_index,
        'chunk_content': chunk_result.content,
        'chunk_size': metadata.chunk_size,
        'chunk_overlap': metadata.chunk_overlap,
        'parent_document_id': metadata.parent_document_id,
        'total_chunks': metadata.total_chunks,
        'chunk_metadata': {
            'start_position': metadata.start_position,
            'end_position': metadata.end_position,
            'chunk_type': metadata.chunk_type,
            'section': metadata.section,
            'subsection': metadata.subsection,
            'paragraph': metadata.paragraph,
            'sentence': metadata.sentence,
            'legal_structure': metadata.legal_structure,
            'additional_metadata': metadata.additional_metadata
        }
    }

# Example usage and testing
if __name__ == "__main__":
    # Test the enhanced chunker
    sample_text = """
    Artículo 1. Objeto. La presente ley tiene por objeto regular el manejo de datos personales en Colombia.
    
    Artículo 2. Definiciones. Para efectos de la presente ley, se entiende por:
    a) Dato personal: Cualquier información vinculada o que pueda asociarse a una o varias personas naturales determinadas o determinables;
    b) Tratamiento: Cualquier operación o conjunto de operaciones sobre datos personales;
    
    Artículo 3. Principios. El tratamiento de datos personales se regirá por los siguientes principios:
    1. Legalidad;
    2. Finalidad;
    3. Libertad;
    4. Veracidad o calidad;
    5. Transparencia;
    6. Acceso y circulación restringida;
    7. Seguridad;
    8. Confidencialidad.
    """
    
    chunker = EnhancedChunker(
        strategy=ChunkingStrategy.LEGAL_STRUCTURE,
        max_chars=500,
        overlap_chars=50
    )
    
    parent_id = str(uuid.uuid4())
    chunks = chunker.chunk_text(sample_text, parent_id, "law")
    
    print(f"Created {len(chunks)} chunks:")
    for chunk in chunks:
        print(f"\nChunk {chunk.metadata.chunk_index}:")
        print(f"Content: {chunk.content[:100]}...")
        print(f"Metadata: {chunk.metadata}")
