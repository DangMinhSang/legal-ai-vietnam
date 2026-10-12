"""
Vietnamese legal text chunking module.

Provides structure-aware chunking for Vietnamese legal documents (codes, decrees, circulars)
and court judgments, splitting hierarchically by article/chapter/section, clause, paragraph,
and sentence while maintaining character offsets and chunk overlaps.
"""

from __future__ import annotations

from dataclasses import dataclass

import regex
from loguru import logger

# Exact regex patterns as specified
ARTICLE_PATTERN = regex.compile(r'(?i)(?:^|\n)(Điều\s+\d+[a-z]?[\.\s])', regex.MULTILINE)
CLAUSE_PATTERN = regex.compile(r'(?:^|\n)(\d+\.\s)', regex.MULTILINE)
CHAPTER_PATTERN = regex.compile(r'(?i)(?:^|\n)(Chương\s+[IVXLC]+|\bChương\s+\d+)', regex.MULTILINE)
SECTION_PATTERN = regex.compile(r'(?:^|\n)((?:I{1,3}|IV|VI{0,3}|IX|X{1,3})\.\s)', regex.MULTILINE)

# Additional structural patterns for Vietnamese legal hierarchy
PART_PATTERN = regex.compile(r'(?i)(?:^|\n)(Phần\s+[IVXLC\d]+[\.\s])', regex.MULTILINE)
MUC_PATTERN = regex.compile(r'(?i)(?:^|\n)(Mục\s+[IVXLC\d]+[\.\s])', regex.MULTILINE)

# Regex for extracting legal reference ("Điều \d+")
LEGAL_REF_PATTERN = regex.compile(r'(?i)\b(Điều\s+\d+[a-z]?)\b')

# Lower-priority split delimiters
PARAGRAPH_DELIMITER = regex.compile(r'\n\s*\n+')
SENTENCE_DELIMITER = regex.compile(r'(?<=[.?!])\s+')


@dataclass
class TextChunkResult:
    """Represents an individual text chunk from a legal document.

    Attributes:
        content: Text content of the chunk (with overlap if applicable).
        chunk_index: 0-based sequential index of the chunk.
        start_char: Original document start character index (pre-overlap).
        end_char: Original document end character index.
        chunk_type: Structural level ("article" | "clause" | "paragraph" | "section" | "unknown").
        legal_ref: Optional legal reference extracted from content (e.g. "Điều 123").
    """

    content: str
    chunk_index: int
    start_char: int
    end_char: int
    chunk_type: str
    legal_ref: str | None = None


@dataclass
class _RawSegment:
    """Internal segment prior to overlap prepending."""

    content: str
    start_char: int
    end_char: int
    chunk_type: str
    legal_ref: str | None = None


class LegalTextChunker:
    """Structure-aware chunker for Vietnamese legal texts and judgments."""

    def __init__(
        self,
        target_chunk_size: int = 512,
        overlap: int = 64,
        min_chunk_size: int = 0,
    ) -> None:
        """Initialize LegalTextChunker.

        Args:
            target_chunk_size: Target character count per chunk (default 512).
            overlap: Character overlap prepended to subsequent chunks (default 64).
            min_chunk_size: Minimum characters required to keep a chunk (default 0).
        """
        self.target_chunk_size = target_chunk_size
        self.overlap = overlap
        self.min_chunk_size = min_chunk_size

    def _extract_legal_ref(self, text: str) -> str | None:
        """Extract 'Điều \\d+' pattern from text and normalize whitespace."""
        match = LEGAL_REF_PATTERN.search(text)
        if match:
            raw_ref = match.group(1).strip()
            return regex.sub(r'\s+', ' ', raw_ref)
        return None

    def _determine_structural_type(self, text: str) -> str:
        """Infer chunk_type from leading content."""
        stripped = text.strip()
        if ARTICLE_PATTERN.match(stripped) or regex.match(r'(?i)^Điều\s+\d+', stripped):
            return "article"
        if CLAUSE_PATTERN.match(stripped) or regex.match(r'^\d+\.\s', stripped):
            return "clause"
        if CHAPTER_PATTERN.match(stripped) or regex.match(r'(?i)^Chương\s+', stripped):
            return "section"
        if PART_PATTERN.match(stripped) or regex.match(r'(?i)^Phần\s+', stripped):
            return "section"
        if MUC_PATTERN.match(stripped) or regex.match(r'(?i)^Mục\s+', stripped):
            return "section"
        if SECTION_PATTERN.match(stripped):
            return "section"
        return "unknown"

    def _find_structural_split_points(self, text: str) -> list[tuple[int, str]]:
        """Find all Priority 1 split boundaries (Article, Chapter, Section, Part, Mục).

        Returns:
            Sorted list of (character_offset, chunk_type) tuples.
        """
        pattern_types = [
            (ARTICLE_PATTERN, "article"),
            (CHAPTER_PATTERN, "section"),
            (PART_PATTERN, "section"),
            (SECTION_PATTERN, "section"),
            (MUC_PATTERN, "section"),
        ]

        found: list[tuple[int, str]] = []
        for pat, ctype in pattern_types:
            for m in pat.finditer(text):
                found.append((m.start(1), ctype))

        # Sort by position
        found.sort(key=lambda x: x[0])

        # Deduplicate positions (preserving earliest pattern matched)
        unique: list[tuple[int, str]] = []
        seen_positions: set[int] = set()
        for pos, ctype in found:
            if pos not in seen_positions:
                unique.append((pos, ctype))
                seen_positions.add(pos)

        return unique

    def _split_by_clause(
        self,
        text: str,
        base_start: int,
        parent_ref: str | None = None,
    ) -> list[_RawSegment]:
        """Split a long text segment into clauses using CLAUSE_PATTERN."""
        matches = list(CLAUSE_PATTERN.finditer(text))
        if not matches:
            return []

        # Find split positions in local text
        clause_starts = [m.start(1) for m in matches]

        segments: list[_RawSegment] = []
        first_clause_pos = clause_starts[0]

        # If there's preamble text before the first clause
        if first_clause_pos > 0:
            preamble = text[:first_clause_pos]
            if len(preamble) <= self.target_chunk_size and len(clause_starts) > 0:
                # Attach short preamble (e.g. article header) to the first clause
                clause_starts[0] = 0
            else:
                p_type = self._determine_structural_type(preamble)
                p_ref = self._extract_legal_ref(preamble) or parent_ref
                segments.append(
                    _RawSegment(
                        content=preamble,
                        start_char=base_start,
                        end_char=base_start + first_clause_pos,
                        chunk_type=p_type if p_type != "unknown" else "paragraph",
                        legal_ref=p_ref,
                    )
                )

        # Build segments from clause boundaries
        for i, start_pos in enumerate(clause_starts):
            end_pos = clause_starts[i + 1] if i + 1 < len(clause_starts) else len(text)
            clause_content = text[start_pos:end_pos]
            ref = self._extract_legal_ref(clause_content) or parent_ref
            segments.append(
                _RawSegment(
                    content=clause_content,
                    start_char=base_start + start_pos,
                    end_char=base_start + end_pos,
                    chunk_type="clause",
                    legal_ref=ref,
                )
            )

        return segments

    def _split_by_paragraph(
        self,
        text: str,
        base_start: int,
        parent_ref: str | None = None,
    ) -> list[_RawSegment]:
        """Split a long text segment at double newlines."""
        matches = list(PARAGRAPH_DELIMITER.finditer(text))
        if not matches:
            return []

        # Boundaries separating paragraphs
        split_points = [0] + [m.end() for m in matches]
        if split_points[-1] != len(text):
            split_points.append(len(text))

        segments: list[_RawSegment] = []
        for i in range(len(split_points) - 1):
            s_start = split_points[i]
            s_end = split_points[i + 1]
            seg_text = text[s_start:s_end]
            if not seg_text:
                continue
            ref = self._extract_legal_ref(seg_text) or parent_ref
            segments.append(
                _RawSegment(
                    content=seg_text,
                    start_char=base_start + s_start,
                    end_char=base_start + s_end,
                    chunk_type="paragraph",
                    legal_ref=ref,
                )
            )

        return segments

    def _split_by_sentence(
        self,
        text: str,
        base_start: int,
        parent_ref: str | None = None,
    ) -> list[_RawSegment]:
        """Split a long paragraph segment by sentence boundaries, packing up to target size."""
        matches = list(SENTENCE_DELIMITER.finditer(text))
        if not matches:
            # Fall back to hard chunking if no sentence punctuation exists
            return self._split_by_chars(text, base_start, parent_ref)

        sentence_boundaries = [0] + [m.end() for m in matches]
        if sentence_boundaries[-1] != len(text):
            sentence_boundaries.append(len(text))

        sentence_spans = [
            (sentence_boundaries[i], sentence_boundaries[i + 1])
            for i in range(len(sentence_boundaries) - 1)
        ]

        segments: list[_RawSegment] = []
        curr_start = 0
        curr_end = 0

        for s_start, s_end in sentence_spans:
            s_len = s_end - s_start
            # If a single sentence exceeds target size, flush current and hard-split the sentence
            if s_len > self.target_chunk_size:
                if curr_end > curr_start:
                    seg_text = text[curr_start:curr_end]
                    segments.append(
                        _RawSegment(
                            content=seg_text,
                            start_char=base_start + curr_start,
                            end_char=base_start + curr_end,
                            chunk_type="paragraph",
                            legal_ref=self._extract_legal_ref(seg_text) or parent_ref,
                        )
                    )
                    curr_start = 0
                    curr_end = 0
                sub_segs = self._split_by_chars(
                    text[s_start:s_end], base_start + s_start, parent_ref
                )
                segments.extend(sub_segs)
                continue

            if curr_end == 0:
                curr_start = s_start
                curr_end = s_end
            elif (s_end - curr_start) <= self.target_chunk_size:
                curr_end = s_end
            else:
                seg_text = text[curr_start:curr_end]
                segments.append(
                    _RawSegment(
                        content=seg_text,
                        start_char=base_start + curr_start,
                        end_char=base_start + curr_end,
                        chunk_type="paragraph",
                        legal_ref=self._extract_legal_ref(seg_text) or parent_ref,
                    )
                )
                curr_start = s_start
                curr_end = s_end

        if curr_end > curr_start:
            seg_text = text[curr_start:curr_end]
            segments.append(
                _RawSegment(
                    content=seg_text,
                    start_char=base_start + curr_start,
                    end_char=base_start + curr_end,
                    chunk_type="paragraph",
                    legal_ref=self._extract_legal_ref(seg_text) or parent_ref,
                )
            )

        return segments

    def _split_by_chars(
        self,
        text: str,
        base_start: int,
        parent_ref: str | None = None,
    ) -> list[_RawSegment]:
        """Hard split by target_chunk_size characters when natural boundaries are exhausted."""
        segments: list[_RawSegment] = []
        pos = 0
        text_len = len(text)
        while pos < text_len:
            end_pos = min(pos + self.target_chunk_size, text_len)
            seg_text = text[pos:end_pos]
            ref = self._extract_legal_ref(seg_text) or parent_ref
            segments.append(
                _RawSegment(
                    content=seg_text,
                    start_char=base_start + pos,
                    end_char=base_start + end_pos,
                    chunk_type="unknown",
                    legal_ref=ref,
                )
            )
            pos = end_pos
        return segments

    def _recursively_split_segment(
        self,
        segment: _RawSegment,
    ) -> list[_RawSegment]:
        """Recursively apply lower-priority splitting if segment length > target_chunk_size.

        Hierarchy:
        1. Clause (CLAUSE_PATTERN)
        2. Paragraph (double newline)
        3. Sentence (period/question/exclamation followed by space)
        4. Character limit
        """
        if len(segment.content) <= self.target_chunk_size:
            return [segment]

        # 1. Try Clause splitting
        clause_segs = self._split_by_clause(
            segment.content,
            base_start=segment.start_char,
            parent_ref=segment.legal_ref,
        )
        if len(clause_segs) > 1:
            results: list[_RawSegment] = []
            for c_seg in clause_segs:
                results.extend(self._recursively_split_segment(c_seg))
            return results

        # 2. Try Paragraph splitting
        para_segs = self._split_by_paragraph(
            segment.content,
            base_start=segment.start_char,
            parent_ref=segment.legal_ref,
        )
        if len(para_segs) > 1:
            results = []
            for p_seg in para_segs:
                results.extend(self._recursively_split_segment(p_seg))
            return results

        # 3. Try Sentence splitting
        sent_segs = self._split_by_sentence(
            segment.content,
            base_start=segment.start_char,
            parent_ref=segment.legal_ref,
        )
        if len(sent_segs) > 1:
            results = []
            for s_seg in sent_segs:
                results.extend(self._recursively_split_segment(s_seg))
            return results

        # 4. Fallback: Character splitting
        return self._split_by_chars(
            segment.content,
            base_start=segment.start_char,
            parent_ref=segment.legal_ref,
        )

    def chunk_legal_document(
        self,
        text: str,
        doc_type: str = "unknown",
        min_chunk_size: int | None = None,
    ) -> list[TextChunkResult]:
        """Chunk a Vietnamese legal document into structure-aware segments with overlap.

        Args:
            text: Raw document text string.
            doc_type: Document classification hint (e.g. "code", "judgment", "decree").
            min_chunk_size: Optional threshold to filter chunks below minimum length.

        Returns:
            List of TextChunkResult objects with sequential chunk_index.
        """
        if not text or not text.strip():
            logger.debug("Input text is empty. Returning empty chunk list.")
            return []

        effective_min_size = self.min_chunk_size if min_chunk_size is None else min_chunk_size
        logger.debug(
            f"Chunking document (length={len(text)} chars, doc_type='{doc_type}', "
            f"target_size={self.target_chunk_size}, overlap={self.overlap})..."
        )

        # -------------------------------------------------------------
        # Step 1: Find highest-priority split points (Structural: Level 1)
        # -------------------------------------------------------------
        structural_splits = self._find_structural_split_points(text)
        raw_segments: list[_RawSegment] = []

        if structural_splits:
            first_pos = structural_splits[0][0]
            # Handle text preceding first structural header
            if first_pos > 0:
                preamble_text = text[:first_pos]
                if preamble_text.strip():
                    raw_segments.append(
                        _RawSegment(
                            content=preamble_text,
                            start_char=0,
                            end_char=first_pos,
                            chunk_type="section" if doc_type == "judgment" else "unknown",
                            legal_ref=self._extract_legal_ref(preamble_text),
                        )
                    )
                else:
                    # Expand first segment start to 0 to preserve whitespace
                    structural_splits[0] = (0, structural_splits[0][1])

            # Build initial segments from structural split points
            for i, (start_pos, c_type) in enumerate(structural_splits):
                end_pos = (
                    structural_splits[i + 1][0]
                    if i + 1 < len(structural_splits)
                    else len(text)
                )
                seg_content = text[start_pos:end_pos]
                ref = self._extract_legal_ref(seg_content)
                raw_segments.append(
                    _RawSegment(
                        content=seg_content,
                        start_char=start_pos,
                        end_char=end_pos,
                        chunk_type=c_type,
                        legal_ref=ref,
                    )
                )
        else:
            # No structural markers found
            if len(text) <= self.target_chunk_size:
                # Text fits completely in a single chunk
                initial_type = "paragraph" if "\n" in text else "unknown"
                raw_segments.append(
                    _RawSegment(
                        content=text,
                        start_char=0,
                        end_char=len(text),
                        chunk_type=initial_type,
                        legal_ref=self._extract_legal_ref(text),
                    )
                )
            else:
                # Need lower-priority initial split
                synthetic_seg = _RawSegment(
                    content=text,
                    start_char=0,
                    end_char=len(text),
                    chunk_type="unknown",
                    legal_ref=self._extract_legal_ref(text),
                )
                raw_segments = self._recursively_split_segment(synthetic_seg)

        # -------------------------------------------------------------
        # Step 2: Recursively apply lower-priority splitting for segments > target_chunk_size
        # -------------------------------------------------------------
        final_raw_segments: list[_RawSegment] = []
        for seg in raw_segments:
            if len(seg.content) > self.target_chunk_size:
                sub_segments = self._recursively_split_segment(seg)
                final_raw_segments.extend(sub_segments)
            else:
                final_raw_segments.append(seg)

        # -------------------------------------------------------------
        # Step 3: Apply overlap by prepending last N chars of previous chunk
        #         (tracking start_char/end_char based on original positions)
        # -------------------------------------------------------------
        chunk_results: list[TextChunkResult] = []
        for i, seg in enumerate(final_raw_segments):
            if i == 0:
                chunk_content = seg.content
            else:
                prev_content = final_raw_segments[i - 1].content
                overlap_size = min(self.overlap, len(prev_content))
                overlap_prefix = prev_content[-overlap_size:]
                chunk_content = overlap_prefix + seg.content

            # Resolve legal_ref
            ref = seg.legal_ref or self._extract_legal_ref(seg.content)

            chunk_results.append(
                TextChunkResult(
                    content=chunk_content,
                    chunk_index=len(chunk_results),
                    start_char=seg.start_char,
                    end_char=seg.end_char,
                    chunk_type=seg.chunk_type,
                    legal_ref=ref,
                )
            )

        # -------------------------------------------------------------
        # Step 4: Optional minimum chunk size filtering
        # -------------------------------------------------------------
        if effective_min_size > 0:
            filtered_chunks: list[TextChunkResult] = []
            for chk in chunk_results:
                raw_len = chk.end_char - chk.start_char
                if raw_len >= effective_min_size or len(chk.content.strip()) >= effective_min_size:
                    filtered_chunks.append(
                        TextChunkResult(
                            content=chk.content,
                            chunk_index=len(filtered_chunks),
                            start_char=chk.start_char,
                            end_char=chk.end_char,
                            chunk_type=chk.chunk_type,
                            legal_ref=chk.legal_ref,
                        )
                    )
            chunk_results = filtered_chunks

        logger.info(
            f"Successfully chunked text into {len(chunk_results)} chunks (doc_type='{doc_type}')."
        )
        return chunk_results

    def chunk_judgment(self, text: str) -> list[TextChunkResult]:
        """Convenience wrapper calling chunk_legal_document with doc_type='judgment'.

        Args:
            text: Vietnamese court judgment text.

        Returns:
            List of TextChunkResult objects.
        """
        return self.chunk_legal_document(text=text, doc_type="judgment")


# Convenience alias matching test references
LegalChunker = LegalTextChunker

__all__ = [
    "LegalTextChunker",
    "LegalChunker",
    "TextChunkResult",
    "ARTICLE_PATTERN",
    "CLAUSE_PATTERN",
    "CHAPTER_PATTERN",
    "SECTION_PATTERN",
]
