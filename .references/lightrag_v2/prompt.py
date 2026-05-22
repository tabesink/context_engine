from __future__ import annotations
from typing import Any


PROMPTS: dict[str, Any] = {}

PROMPTS["DEFAULT_LANGUAGE"] = "English"
PROMPTS["DEFAULT_TUPLE_DELIMITER"] = "<|>"
PROMPTS["DEFAULT_RECORD_DELIMITER"] = "##"
PROMPTS["DEFAULT_COMPLETION_DELIMITER"] = "<|COMPLETE|>"

PROMPTS["DEFAULT_ENTITY_TYPES"] = [
    "component",
    "module",
    "operation",
    "procedure",
    "setting",
    "parameter",
    "input",
    "output",
    "result",
    "concept",
]

PROMPTS["DEFAULT_ENTITY_TYPE_DESCRIPTIONS"] = """- component: named software object, product object, UI object, configuration object, or physical object described by the manual
- module: major functional unit, engine, provider, analyzer, editor, subsystem, or service
- operation: action the software or component performs during analysis, import, export, calculation, conversion, or reporting
- procedure: documented workflow, user task, algorithmic sequence, or recommended setup process
- setting: named configurable option, property, mode, flag, enum value, or selectable behavior
- parameter: numeric, scalar, vector, unit-bearing, or formula input that tunes a setting, operation, or procedure
- input: file, data, signal, model, load, result set, user selection, or external artifact consumed by a module or operation
- output: file, result, plot, report, value, intermediate artifact, or status produced by a module or operation
- result: interpreted analysis result, computed value, prediction, factor, damage, life, safety assessment, or diagnostic outcome
- concept: fallback technical idea when no stricter software-manual type fits"""

PROMPTS["DEFAULT_USER_PROMPT"] = "n/a"

PROMPTS["entity_extraction"] = """---Goal---
You are an expert knowledge graph extractor for software manuals and technical product documentation.

Given a structured manual section, extract entities and relationships from prose using the supplied upper ontology, document structure context, and corpus-derived domain guidance.
Use {language} as output language.

IMPORTANT:
- This is technical documentation, not narrative text.
- Use document hierarchy as semantic grounding.
- The entity_type MUST be one of the allowed upper entity types.
- Domain guidance gives examples and subtype hints only; do NOT invent new entity_type values from it.
- Prefer precise technical relationships over broad semantic associations.
- Treat tables, figures, TOCs, figure lists, and table lists as citation/navigation context only unless their prose is explicitly included in the text.

---Allowed Upper Entity Types---
[{entity_types}]

---Upper Entity Type Meanings---
{entity_type_descriptions}

---Document Structure Context---
{section_context}

Use this structure to:
- treat section titles as local technical anchors when they name components, modules, operations, procedures, settings, parameters, inputs, outputs, results, or concepts
- avoid merging entities across sibling sections unless the text explicitly connects them
- prefer local section scope over global topic guessing

---Corpus-Derived Domain Guidance---
{ontology_guidance}

Use this guidance to recognize domain-specific subtypes and examples, but keep the output entity_type in the allowed upper ontology.

---Steps---
1. Identify all entities. For each identified entity, extract the following information:
- entity_name: exact name as written where possible, preserving capitalization for English technical names
- entity_type: one of the allowed upper entity types
- entity_description: concise technical explanation of the entity's function, role, or meaning in this section
Format each entity as ("entity"{tuple_delimiter}<entity_name>{tuple_delimiter}<entity_type>{tuple_delimiter}<entity_description>)

2. From the entities identified in step 1, identify all pairs of (source_entity, target_entity) that are clearly and technically related to each other.
For each pair of related entities, extract the following information:
- source_entity: name of the source entity, as identified in step 1
- target_entity: name of the target entity, as identified in step 1
- relationship_description: technical explanation of how the entities interact, depend on each other, compose each other, produce/consume each other, or constrain each other
- relationship_strength: a numeric score indicating strength of the relationship between the source entity and target entity
- relationship_keywords: short technical tags, not sentences
Format each relationship as ("relationship"{tuple_delimiter}<source_entity>{tuple_delimiter}<target_entity>{tuple_delimiter}<relationship_description>{tuple_delimiter}<relationship_keywords>{tuple_delimiter}<relationship_strength>)

3. Identify 3-8 high-level technical keywords that summarize the main concepts, themes, or topics of the section. Use short noun phrases, not full sentences.
Format the content-level key words as ("content_keywords"{tuple_delimiter}<high_level_keywords>)

4. Return output in {language} as a single list of all the entities and relationships identified in steps 1 and 2. Use **{record_delimiter}** as the list delimiter.

5. When finished, output {completion_delimiter}

######################
---Examples---
######################
{examples}

#############################
---Real Data---
######################
Entity_types: [{entity_types}]
Section Context:
{section_context}
Text:
{input_text}
######################
Output:"""

PROMPTS["entity_extraction_examples"] = [
    """Example 1:

Entity_types: [component, module, operation, procedure, setting, parameter, input, output, result, concept]
Text:
```
The Standard SN Analysis Engine computes fatigue life from stress-life material data. The engine consumes a time history load provider and applies rainflow counting before evaluating the SN curve. The fatigue safety factor is reported with life prediction results.
```

Output:
("entity"{tuple_delimiter}"Standard SN Analysis Engine"{tuple_delimiter}"module"{tuple_delimiter}"Standard SN Analysis Engine is a manual-described analysis engine that computes fatigue life from stress-life material data."){record_delimiter}
("entity"{tuple_delimiter}"stress-life material data"{tuple_delimiter}"input"{tuple_delimiter}"Stress-life material data is input data used by the SN fatigue calculation."){record_delimiter}
("entity"{tuple_delimiter}"time history load provider"{tuple_delimiter}"input"{tuple_delimiter}"Time history load provider supplies time-varying load data consumed by the fatigue engine."){record_delimiter}
("entity"{tuple_delimiter}"rainflow counting"{tuple_delimiter}"operation"{tuple_delimiter}"Rainflow counting is the cycle-counting operation applied before SN curve evaluation."){record_delimiter}
("entity"{tuple_delimiter}"SN curve"{tuple_delimiter}"input"{tuple_delimiter}"SN curve is fatigue material data used to evaluate stress-life behavior."){record_delimiter}
("entity"{tuple_delimiter}"fatigue safety factor"{tuple_delimiter}"result"{tuple_delimiter}"Fatigue safety factor is an interpreted analysis result reported with life prediction results."){record_delimiter}
("entity"{tuple_delimiter}"life prediction results"{tuple_delimiter}"output"{tuple_delimiter}"Life prediction results are fatigue analysis outputs produced by the Standard SN Analysis Engine."){record_delimiter}
("relationship"{tuple_delimiter}"Standard SN Analysis Engine"{tuple_delimiter}"time history load provider"{tuple_delimiter}"The Standard SN Analysis Engine consumes time-varying load data from the time history load provider."{tuple_delimiter}"load input, fatigue analysis"{tuple_delimiter}8){record_delimiter}
("relationship"{tuple_delimiter}"Standard SN Analysis Engine"{tuple_delimiter}"rainflow counting"{tuple_delimiter}"The Standard SN Analysis Engine applies rainflow counting before evaluating fatigue life."{tuple_delimiter}"cycle counting, method usage"{tuple_delimiter}8){record_delimiter}
("relationship"{tuple_delimiter}"Standard SN Analysis Engine"{tuple_delimiter}"life prediction results"{tuple_delimiter}"The Standard SN Analysis Engine produces life prediction results as analysis output."{tuple_delimiter}"analysis output, fatigue life"{tuple_delimiter}9){record_delimiter}
("content_keywords"{tuple_delimiter}"fatigue analysis, stress-life method, load history, life prediction"){completion_delimiter}
#############################""",
    """Example 2:

Entity_types: [component, module, operation, procedure, setting, parameter, input, output, result, concept]
Text:
```
The FE import results set defines the FE results files used for the job. Set IncludeTemperatures to True when temperatures must be read from the FE results. IncludeDisplacements controls whether nodal displacements are written to the intermediate file for the Animation analysis engine.
```

Output:
("entity"{tuple_delimiter}"FE import results set"{tuple_delimiter}"component"{tuple_delimiter}"FE import results set is a configuration object that defines FE results files used for the job."){record_delimiter}
("entity"{tuple_delimiter}"FE results files"{tuple_delimiter}"input"{tuple_delimiter}"FE results files are input artifacts consumed by the FE import results set."){record_delimiter}
("entity"{tuple_delimiter}"IncludeTemperatures"{tuple_delimiter}"setting"{tuple_delimiter}"IncludeTemperatures is a Boolean setting that controls whether temperatures are read from FE results."){record_delimiter}
("entity"{tuple_delimiter}"IncludeDisplacements"{tuple_delimiter}"setting"{tuple_delimiter}"IncludeDisplacements is a setting that controls whether nodal displacements are written to the intermediate file."){record_delimiter}
("entity"{tuple_delimiter}"nodal displacements"{tuple_delimiter}"output"{tuple_delimiter}"Nodal displacements are written to the intermediate file when IncludeDisplacements enables them."){record_delimiter}
("entity"{tuple_delimiter}"intermediate file"{tuple_delimiter}"output"{tuple_delimiter}"Intermediate file is an output artifact that can contain nodal displacements for downstream analysis."){record_delimiter}
("entity"{tuple_delimiter}"Animation analysis engine"{tuple_delimiter}"module"{tuple_delimiter}"Animation analysis engine is a module that requires nodal displacements from the intermediate file."){record_delimiter}
("relationship"{tuple_delimiter}"FE import results set"{tuple_delimiter}"FE results files"{tuple_delimiter}"The FE import results set defines which FE results files are used for the job."{tuple_delimiter}"configuration input, FE results"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"IncludeTemperatures"{tuple_delimiter}"FE results files"{tuple_delimiter}"IncludeTemperatures controls whether temperatures are read from the FE results files."{tuple_delimiter}"setting, temperature input"{tuple_delimiter}8){record_delimiter}
("relationship"{tuple_delimiter}"IncludeDisplacements"{tuple_delimiter}"intermediate file"{tuple_delimiter}"IncludeDisplacements controls whether nodal displacements are written to the intermediate file."{tuple_delimiter}"setting, intermediate output"{tuple_delimiter}8){record_delimiter}
("relationship"{tuple_delimiter}"Animation analysis engine"{tuple_delimiter}"nodal displacements"{tuple_delimiter}"The Animation analysis engine requires nodal displacements."{tuple_delimiter}"module input, displacement data"{tuple_delimiter}8){record_delimiter}
("content_keywords"{tuple_delimiter}"FE import, configuration settings, FE results files, intermediate file"){completion_delimiter}
#############################""",
]

PROMPTS[
    "summarize_entity_descriptions"
] = """You are a helpful assistant responsible for generating a comprehensive summary of the data provided below.
Given one or two entities, and a list of descriptions, all related to the same entity or group of entities.
Please concatenate all of these into a single, comprehensive description. Make sure to include information collected from all the descriptions.
If the provided descriptions are contradictory, please resolve the contradictions and provide a single, coherent summary.
Make sure it is written in third person, and include the entity names so we the have full context.
Use {language} as output language.

#######
---Data---
Entities: {entity_name}
Description List: {description_list}
#######
Output:
"""

PROMPTS["entity_continue_extraction"] = """
MANY entities and relationships were missed in the last extraction.

---Remember Steps---

1. Identify all entities. For each identified entity, extract the following information:
- entity_name: Name of the entity, use same language as input text. If English, capitalized the name.
- entity_type: One of the following upper ontology types: [{entity_types}]. Do NOT invent new entity_type values.
- entity_description: Comprehensive description of the entity's attributes and activities
Format each entity as ("entity"{tuple_delimiter}<entity_name>{tuple_delimiter}<entity_type>{tuple_delimiter}<entity_description>)

2. From the entities identified in step 1, identify all pairs of (source_entity, target_entity) that are *clearly related* to each other.
For each pair of related entities, extract the following information:
- source_entity: name of the source entity, as identified in step 1
- target_entity: name of the target entity, as identified in step 1
- relationship_description: explanation as to why you think the source entity and the target entity are related to each other
- relationship_strength: a numeric score indicating strength of the relationship between the source entity and target entity
- relationship_keywords: one or more high-level key words that summarize the overarching nature of the relationship, focusing on concepts or themes rather than specific details
Format each relationship as ("relationship"{tuple_delimiter}<source_entity>{tuple_delimiter}<target_entity>{tuple_delimiter}<relationship_description>{tuple_delimiter}<relationship_keywords>{tuple_delimiter}<relationship_strength>)

3. Identify high-level key words that summarize the main concepts, themes, or topics of the entire text. These should capture the overarching ideas present in the document.
Format the content-level key words as ("content_keywords"{tuple_delimiter}<high_level_keywords>)

4. Return output in {language} as a single list of all the entities and relationships identified in steps 1 and 2. Use **{record_delimiter}** as the list delimiter.

5. When finished, output {completion_delimiter}

---Output---

Add them below using the same format:\n
""".strip()

PROMPTS["entity_if_loop_extraction"] = """
---Goal---

It appears some entities may have still been missed.

---Output---

Answer ONLY by `YES` OR `NO` if there are still entities that need to be added.
""".strip()

PROMPTS["fail_response"] = (
    "Sorry, I'm not able to provide an answer to that question.[no-context]"
)

PROMPTS["rag_response"] = """---Role---

You are a helpful assistant responding to user query about Knowledge Graph and Document Chunks provided in JSON format below.


---Goal---

Generate a concise response based on Knowledge Base and follow Response Rules, considering both the conversation history and the current query. Summarize all information in the provided Knowledge Base, and incorporating general knowledge relevant to the Knowledge Base. Do not include information not provided by Knowledge Base.

When handling relationships with timestamps:
1. Each relationship has a "created_at" timestamp indicating when we acquired this knowledge
2. When encountering conflicting relationships, consider both the semantic content and the timestamp
3. Don't automatically prefer the most recently created relationships - use judgment based on the context
4. For time-specific queries, prioritize temporal information in the content before considering creation timestamps

---Conversation History---
{history}

---Knowledge Graph and Document Chunks---
{context_data}

---Response Rules---

- Target format and length: {response_type}
- Use markdown formatting with appropriate section headings
- Please respond in the same language as the user's question.
- Ensure the response maintains continuity with the conversation history.
- List up to 5 most important reference sources at the end under "References" section. Use the provided Reference Sources labels exactly when available, for example: [KG] dl_theory_guide.pdf > Parent > Section, p.42. Do not repeat the same document, section, and page reference.
- If you don't know the answer, just say so.
- Do not make anything up. Do not include information not provided by the Knowledge Base.
- Addtional user prompt: {user_prompt}

Response:"""

PROMPTS["keywords_extraction"] = """---Role---

You are a helpful assistant tasked with identifying both high-level and low-level keywords in the user's query and conversation history.

---Goal---

Given the query and conversation history, list both high-level and low-level keywords. High-level keywords focus on overarching concepts or themes, while low-level keywords focus on specific entities, details, or concrete terms.

---Instructions---

- Consider both the current query and relevant conversation history when extracting keywords
- Output the keywords in JSON format, it will be parsed by a JSON parser, do not add any extra content in output
- The JSON should have two keys:
  - "high_level_keywords" for overarching concepts or themes
  - "low_level_keywords" for specific entities or details

######################
---Examples---
######################
{examples}

#############################
---Real Data---
######################
Conversation History:
{history}

Current Query: {query}
######################
The `Output` should be human text, not unicode characters. Keep the same language as `Query`.
Output:

"""

PROMPTS["keywords_extraction_examples"] = [
    """Example 1:

Query: "How does international trade influence global economic stability?"
################
Output:
{
  "high_level_keywords": ["International trade", "Global economic stability", "Economic impact"],
  "low_level_keywords": ["Trade agreements", "Tariffs", "Currency exchange", "Imports", "Exports"]
}
#############################""",
    """Example 2:

Query: "What are the environmental consequences of deforestation on biodiversity?"
################
Output:
{
  "high_level_keywords": ["Environmental consequences", "Deforestation", "Biodiversity loss"],
  "low_level_keywords": ["Species extinction", "Habitat destruction", "Carbon emissions", "Rainforest", "Ecosystem"]
}
#############################""",
    """Example 3:

Query: "What is the role of education in reducing poverty?"
################
Output:
{
  "high_level_keywords": ["Education", "Poverty reduction", "Socioeconomic development"],
  "low_level_keywords": ["School access", "Literacy rates", "Job training", "Income inequality"]
}
#############################""",
]

PROMPTS["naive_rag_response"] = """---Role---

You are a helpful assistant responding to user query about Document Chunks provided provided in JSON format below.

---Goal---

Generate a concise response based on Document Chunks and follow Response Rules, considering both the conversation history and the current query. Summarize all information in the provided Document Chunks, and incorporating general knowledge relevant to the Document Chunks. Do not include information not provided by Document Chunks.

When handling content with timestamps:
1. Each piece of content has a "created_at" timestamp indicating when we acquired this knowledge
2. When encountering conflicting information, consider both the content and the timestamp
3. Don't automatically prefer the most recent content - use judgment based on the context
4. For time-specific queries, prioritize temporal information in the content before considering creation timestamps

---Conversation History---
{history}

---Document Chunks(DC)---
{content_data}

---Response Rules---

- Target format and length: {response_type}
- Use markdown formatting with appropriate section headings
- Please respond in the same language as the user's question.
- Ensure the response maintains continuity with the conversation history.
- List up to 5 most important reference sources at the end under "References" section. Use the provided Reference Sources labels exactly when available, for example: [DC] dl_theory_guide.pdf > Parent > Section, p.42. Do not repeat the same document, section, and page reference.
- If you don't know the answer, just say so.
- Do not include information not provided by the Document Chunks.
- Addtional user prompt: {user_prompt}

Response:"""

# TODO: deprecated
PROMPTS[
    "similarity_check"
] = """Please analyze the similarity between these two questions:

Question 1: {original_prompt}
Question 2: {cached_prompt}

Please evaluate whether these two questions are semantically similar, and whether the answer to Question 2 can be used to answer Question 1, provide a similarity score between 0 and 1 directly.

Similarity score criteria:
0: Completely unrelated or answer cannot be reused, including but not limited to:
   - The questions have different topics
   - The locations mentioned in the questions are different
   - The times mentioned in the questions are different
   - The specific individuals mentioned in the questions are different
   - The specific events mentioned in the questions are different
   - The background information in the questions is different
   - The key conditions in the questions are different
1: Identical and answer can be directly reused
0.5: Partially related and answer needs modification to be used
Return only a number between 0-1, without any additional content.
"""
