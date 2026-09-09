# RAG Enhancements & Optimization Proposal

Language: [English](RAG_IMPROVEMENTS_PROPOSAL.md) | [日本語](../RAG_IMPROVEMENTS_PROPOSAL.md)

This document proposes architectural enhancements and optimization strategies for Retrieval-Augmented Generation (RAG) pipelines using Docling-generated Markdown.

---

## 1. RAG Optimization Objectives

1. **Semantic Chunking Preservation**: Maintain logical document boundaries (headers, tables, lists, math blocks) to prevent chunk fragmentation.
2. **Context Window Efficiency**: Reduce token waste from verbose syntax while keeping structural integrity intact.
3. **Multi-Modal Retrieval**: Seamlessly link extracted figures and image captions to corresponding document text chunks.

---

## 2. Key Proposed Enhancements

### 2.1 Page Marker Chunking Syntax
Standardize page boundary markers (`<!-- PAGE_BREAK: Page N -->`) to allow chunkers to split documents by page when necessary while retaining document hierarchy context.

### 2.2 Table Chunking & HTML Serialization
HTML `<table>` tags preserve cell relationships across complex rows and columns. Ensure chunkers do not split single table elements across chunk boundaries.

### 2.3 Metadata Enrichment
Enhance YAML frontmatter metadata to include document category, total page count, and title to provide global context to vector search embeddings.
