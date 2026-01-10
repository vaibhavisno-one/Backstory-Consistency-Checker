"""Novel ingestion with paragraph-based chunking."""

from typing import List, Tuple, Union, Any
import hashlib

try:
    import pathway as pw
    _PATHWAY_AVAILABLE = hasattr(pw, 'Schema')
except (ImportError, AttributeError):
    _PATHWAY_AVAILABLE = False
    pw = None


if _PATHWAY_AVAILABLE:
    class NarrativeChunkSchema(pw.Schema):
        chunk_id: str
        position: int
        text: str
        char_start: int
        char_end: int
else:
    NarrativeChunkSchema = None


class _FallbackTable:
    def __init__(self, rows: List[dict]):
        self._rows = rows
    
    def filter(self, condition):
        return self
    
    def __iter__(self):
        return iter(self._rows)
    
    def __len__(self):
        return len(self._rows)


def _read_novel(path_to_txt: str) -> str:
    with open(path_to_txt, 'r', encoding='utf-8') as f:
        return f.read()


def _split_into_paragraphs(text: str) -> List[str]:
    paragraphs = text.split('\n\n')
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    return paragraphs


def _create_chunks_with_overlap(
    paragraphs: List[str], 
    overlap_paragraphs: int = 1
) -> List[Tuple[str, int, int]]:
    chunks = []
    
    for i in range(len(paragraphs)):
        start_idx = max(0, i - overlap_paragraphs)
        end_idx = i + 1
        
        chunk_paragraphs = paragraphs[start_idx:end_idx]
        chunk_text = '\n\n'.join(chunk_paragraphs)
        
        chunks.append((chunk_text, start_idx, end_idx))
    
    return chunks


def _calculate_char_offsets(
    text: str, 
    paragraphs: List[str]
) -> List[Tuple[int, int]]:
    offsets = []
    search_start = 0
    
    for paragraph in paragraphs:
        char_start = text.find(paragraph, search_start)
        
        if char_start == -1:
            char_start = search_start
        
        char_end = char_start + len(paragraph)
        offsets.append((char_start, char_end))
        
        search_start = char_end
    
    return offsets


def _generate_chunk_id(text: str, position: int) -> str:
    content = f"{text}_{position}"
    hash_digest = hashlib.sha256(content.encode('utf-8')).hexdigest()
    return f"chunk_{hash_digest[:16]}"


def ingest_novel(path_to_txt: str, overlap_paragraphs: int = 1) -> Union['pw.Table', _FallbackTable]:
    text = _read_novel(path_to_txt)
    paragraphs = _split_into_paragraphs(text)
    para_offsets = _calculate_char_offsets(text, paragraphs)
    chunks_with_indices = _create_chunks_with_overlap(paragraphs, overlap_paragraphs)
    
    rows = []
    for position, (chunk_text, start_para_idx, end_para_idx) in enumerate(chunks_with_indices):
        char_start = para_offsets[start_para_idx][0]
        char_end = para_offsets[end_para_idx - 1][1]
        chunk_id = _generate_chunk_id(chunk_text, position)
        
        if _PATHWAY_AVAILABLE:
            row = (chunk_id, position, chunk_text, char_start, char_end)
            rows.append(row)
        else:
            row = {
                'chunk_id': chunk_id,
                'position': position,
                'text': chunk_text,
                'char_start': char_start,
                'char_end': char_end
            }
            rows.append(row)
    
    if _PATHWAY_AVAILABLE:
        table = pw.debug.table_from_rows(
            schema=NarrativeChunkSchema,
            rows=rows
        )
    else:
        table = _FallbackTable(rows)
    
    return table


def export_chunks_to_list(table: Union['pw.Table', _FallbackTable]) -> List[dict]:
    if _PATHWAY_AVAILABLE and not isinstance(table, _FallbackTable):
        return pw.debug.table_to_dicts(table)
    else:
        return table._rows
