# 02 — User Capabilities

This system is stronger than normal RAG because it supports semantic retrieval plus document navigation plus image-aware source evidence.

## A User Can Ask Normal RAG Questions

```text
What does the manual say about hydraulic pressure limits?
How do I reset the controller?
What are the installation requirements?
Which documents discuss calibration?
```

## A User Can Ask Navigation-Aware Questions

```text
Where in the document is the maintenance schedule?
Which page discusses alarm code E42?
Show me the subsection under Preventive Maintenance that talks about filters.
What are the child sections under Installation?
Give me the content from pages 14 to 17.
```

The answer should include:

```text
document name
section path
page range
chunk/source ids
answer text
related images/tables/figures when relevant
```

## A User Can Ask Structure-Based Summary Questions

```text
Summarize Chapter 3.
Summarize every subsection under Operation.
Create a one-page summary of this manual.
What are the main procedures in this document?
```

## A User Can Ask Procedure Extraction Questions

```text
Give me the step-by-step startup procedure.
Extract the shutdown procedure.
Create a checklist from the maintenance section.
What warnings apply before performing this repair?
```

## A User Can Ask Image/Figure/Table Questions

```text
Which figure shows the wiring diagram?
Show me the image related to the controller harness.
Which table lists torque specifications?
What diagram explains the hydraulic circuit?
Find all figures related to the maintenance procedure.
```

The system should return the answer and related assets:

```json
{
  "answer": "The wiring diagram shows the controller connected to the emergency stop circuit and sensor harness.",
  "sources": [
    {
      "document_id": "doc_123",
      "section_title": "Electrical Wiring",
      "page_start": 18,
      "page_end": 20,
      "chunk_id": "chunk_007_002"
    }
  ],
  "assets": [
    {
      "asset_id": "asset_044",
      "type": "figure",
      "caption": "Figure 6. Main controller wiring diagram",
      "thumbnail_url": "/api/documents/doc_123/assets/asset_044/thumbnail",
      "url": "/api/documents/doc_123/assets/asset_044"
    }
  ]
}
```

## Admin / Debug Questions

```text
Did Docling detect the table of contents correctly?
Did the PageIndex-style TOC refiner run?
Which chunks were sent to LightRAG?
Which assets are linked to this chunk?
Which section/page did this answer come from?
Why was this image returned?
Which documents failed structure validation?
```

## The Main Value Proposition

Normal RAG answers:

```text
What does the document say?
```

This system answers:

```text
What does the document say?
Where does it say it?
What section/page/chunk supports it?
What diagram/table/image is associated with it?
How can I navigate the original document?
```
