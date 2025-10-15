from typing import List, Dict, Any
import logging

logger = logging.getLogger("ELESS.Chunker")

# Note: For simplicity, we are using basic Python logic.
# In a full production system, you might use an external library like
# LangChain's text splitters for more advanced chunking algorithms.


def chunk_text(
    raw_text: str, file_hash: str, chunk_size: int, chunk_overlap: int
) -> List[Dict[str, Any]]:
    """
    Splits a raw text string into smaller chunks with overlap and attaches metadata.

    Args:
        raw_text: The entire text content extracted from the document.
        file_hash: The unique identifier for the file (used for metadata).
        chunk_size: The maximum size of each chunk (in characters).
        chunk_overlap: The size of the overlap between consecutive chunks (in characters).

    Returns:
        A list of dictionaries, where each dictionary contains the 'text'
        and necessary 'metadata'.
    """
    if not raw_text:
        return []

    # Use a large set of common delimiters to try and preserve sentence boundaries
    delimiters = ["\n\n", "\n", ". ", " "]

    # 1. Initial Split by largest delimiter (e.g., paragraphs)
    current_splits = [raw_text]

    # 2. Recursive splitting logic
    final_chunks = []

    for delimiter in delimiters:
        # Only split if the current list contains large chunks
        new_splits = []
        should_continue = False

        for text_segment in current_splits:
            if len(text_segment) > chunk_size:
                # If segment is too large, split by the current delimiter
                sub_splits = text_segment.split(delimiter)
                # Apply overlap logic during the split
                for i in range(len(sub_splits)):
                    # Recombine with overlap (simplified overlap logic)
                    if i > 0 and chunk_overlap > 0:
                        # Take the overlap from the end of the previous segment
                        overlap_start = max(0, len(sub_splits[i - 1]) - chunk_overlap)
                        overlap_text = sub_splits[i - 1][overlap_start:]
                        new_splits.append(overlap_text + delimiter + sub_splits[i])
                    else:
                        new_splits.append(sub_splits[i])
                should_continue = True
            else:
                new_splits.append(text_segment)

        current_splits = new_splits

        # If we successfully split any segment, check the next delimiter
        if should_continue:
            continue
        # If no further splitting occurred with this delimiter, the loop ends.

    # After recursive splitting, the segments in current_splits should mostly be
    # close to or under the chunk_size.
    final_segments = [s.strip() for s in current_splits if s.strip()]

    # 3. Format the final output with metadata
    for i, text in enumerate(final_segments):
        final_chunks.append(
            {
                "text": text,
                "metadata": {
                    "file_hash": file_hash,
                    "chunk_id": f"{file_hash[:8]}-{i:04d}",  # Example chunk identifier
                    "chunk_index": i,
                    "char_length": len(text),
                    # Note: Full path and filename should be added here later
                    # (likely passed down from the Dispatcher's initial data)
                },
            }
        )

    logger.debug(f"File {file_hash[:8]} split into {len(final_chunks)} chunks.")
    return final_chunks
