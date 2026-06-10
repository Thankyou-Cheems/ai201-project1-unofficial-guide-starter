# The Unofficial Guide — Project 1

This project is the **Unofficial Guide** for Columbia University Graduate Dining and Meal Plans: a RAG (Retrieval-Augmented Generation) system designed to help graduate students navigate dining plan options, location limits, and real-world student experiences.

---

## Domain

The system covers **Columbia University dining and meal plans for graduate students** on the Morningside Heights campus. 

This knowledge is highly valuable because:
- Official Columbia Dining pages often describe dining plans broadly, leaving graduate-specific options, pricing, and caps (such as term block limitations) buried across different subpages.
- Crucial location-based restrictions (e.g., that graduate meal plans are restricted to select retail spots and do not work at popular residential dining halls like John Jay or Ferris) are only explicitly discussed or summarized in unofficial student communities like Reddit.
- This guide makes this scattered information searchable, providing grad students with objective answers regarding plans, convenience (especially for engineering students near Mudd), and cost-effectiveness.

---

## Document Sources

We collected 13 distinct documents across official policy pages, student-run wikis, and Reddit threads:

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | Columbia Dining main site | official | https://dining.columbia.edu |
| 2 | Dining Plan Policy | official | https://dining.columbia.edu/content/dining-plan-policy |
| 3 | Spring 2026 Dining Plan Change Period | official | https://dining.columbia.edu/news/spring-2026-dining-plan-change-period-january-13-27 |
| 4 | Engineering: Dining (SEAS Guide) | official | https://www.engineering.columbia.edu/student-life/dining |
| 5 | First-Year Dining Plans | official | https://dining.columbia.edu/content/first-year-dining-plans |
| 6 | Graduate Student Dining Plans Main Page | official | https://dining.columbia.edu/graduate-plans |
| 7 | WikiCU: Dining Services | wiki | https://www.wikicu.com/Dining_Services |
| 8 | WikiCU: Meal plan | wiki | https://www.wikicu.com/Meal_plan |
| 9 | Prked 2025–26 Meal Plan Guide | guide | https://prked.com/post/columbia-university-meal-plan-guide-a-deep-dive-for-2025-26 |
| 10 | Reddit: Grad dining policy change | forum | https://www.reddit.com/r/columbia/comments/1mylwoa/columbia_dinings_new_policy_regarding_graduate/ |
| 11 | Reddit: Buying extra meals | forum | https://www.reddit.com/r/columbia/comments/197mdia/can_you_add_more_meals_to_the_meal_plan_if_i_run/ |
| 12 | Reddit: Dining halls experiences | forum | https://www.reddit.com/r/columbia/comments/1tct9ad/dining_halls/ |
| 13 | Student Dining Plans Index | official | https://dining.columbia.edu/student-dining-plans |

---

## Chunking Strategy

To avoid text dilution and loss of context, we implemented custom chunking strategies per document type:

- **Reddit Threads (S10–S12)**: Split at the post and comment level using regular expressions (`OP (` or `Comment `). This ensures each student's response or feedback is kept as a self-contained, semantic chunk.
- **Location lists (S4, S7)**: Split at the location level (e.g., matching lists `1. `, `2. ` or `- `). Each dining hall or cafe and its description forms a single, complete chunk.
- **Policies/Guides (S1–S3, S5, S6, S8, S9, S13)**: Paragraph-based splitting with a target chunk size of 1200 characters (~300 tokens) and 150 characters of overlap to preserve context across boundaries.
- **Preprocessing**: Prior to chunking, all HTML structures were stripped of script, style, navigation menu, header, and footer tags using BeautifulSoup.

**Chunk size:** Tailored by type (Location-level, Comment-level, or 1200-character paragraph blocks).  
**Overlap:** 150 characters (only for paragraph-based chunks).  
**Why these choices fit your documents:** Location lists and comments are independent units of information. Paragraph-based chunking with overlap prevents context fragmentation for narrative policies.  
**Final chunk count:** 60 chunks.

---

## Embedding Model

**Model used:** `sentence-transformers/all-MiniLM-L6-v2` (runs locally, 384-dimensional dense vectors).

**Production tradeoff reflection:**
If deploying this system for real users with no cost constraints, we would consider upgrading to a larger model like OpenAI's `text-embedding-3-large` or Cohere's multilingual embedding models:
- **Context Length**: Local MiniLM models have a 256-token limit. A production model with larger limits (e.g., 8192 tokens) would allow us to index larger tables or entire comment threads in a single chunk.
- **Accuracy**: Larger models capture finer domain-specific details and academic abbreviations (e.g., distinguishing "SEAS" from "seas").
- **Multilingual Support**: Essential for international graduate students who might search or ask questions in other languages (e.g., Chinese or Korean).
- **Latency vs. Cost**: Running embeddings locally has zero API latency and zero cost, which is ideal for a free-tier prototype. For production, API-based embeddings require scaling and handling rate limits.

---

## Grounded Generation

**System prompt grounding instruction:**
Grounded generation is enforced in [query.py](file:///d:/Dev/AI201/ai201-project1-unofficial-guide-starter/query.py) via a strict system prompt and greedy decoding (`temperature=0.0`):
```
You are an assistant for Columbia University Graduate Dining and Meal Plans.
Your goal is to answer the user's question using ONLY the provided document context below.

RULES:
1. Base your answer strictly and only on the provided context. Do NOT use any general external knowledge.
2. If the context does not contain enough information to fully answer the question, or if the question is completely out-of-scope, you MUST respond exactly with: 'I don't have enough information on that.'
3. Cite the Source ID (e.g., [S6_grad_plans]) for each major claim you make. Do not create fake citations.
4. Be objective, concise, and helpful to graduate students.
```

**How source attribution is surfaced in the response:**
Source attribution is surfaced in two ways:
1. **Inline Citations**: The model is instructed to cite the Source ID (e.g., `[S6_grad_plans]`) directly next to claims in the generated text.
2. **Programmatic Sources List**: The UI prints a structured "Retrieved Sources" section displaying the titles and URLs of all chunks retrieved.

---

## Evaluation Report

We evaluated the RAG system using our 5 test queries:

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What is the structure of the current meal plan options for graduate students, and how do they differ from the older '14 meals per week' style plans? | Graduate students can only select 25, 50, or 75 meals per term, restricted to retail locations (not residential halls). This differs from older plans which offered weekly structures like 14 meals per week. | Grads can only choose between 25, 50, or 75 meals per term. This differs from older weekly plans (like 14 meals/week) and restricts swipes to select retail locations (Chef Mike's, Faculty House) [S10_reddit_grad_policy]. | Relevant | Accurate |
| 2 | Can graduate students use their meal plans at John Jay, Ferris, or JJ's? | No, graduate plans cannot be used at traditional residential dining halls (John Jay, Ferris, JJ's). | Graduate students cannot use their meal plans at Ferris, John Jay, or JJ's Place. They are restricted to select retail locations [S10_reddit_grad_policy]. | Relevant | Accurate |
| 3 | What happens if I run out of meals before the end of the term? Can I buy more? | Yes, you can purchase 10-meal expansion packs for $110. GS students can also request up to 6 emergency meal tickets from the GS Student Senate. | You can use floating meals [S9_prked_meal_plan_guide_2025] or buy 10-meal expansion packs for $110 through the portal/email [S11_reddit_extra_meals]. | Relevant | Accurate |
| 4 | If I have most of my classes in Mudd, which on-campus dining locations are most convenient for grabbing lunch? | Blue Java Café in Mudd, Chef Don's Pizza Pi in Mudd, Chef Mike's Sub Shop in Uris, and Faculty House. | Several convenient dining options are available [S4_engineering_dining], including Faculty House (buffet-style lunch for swipes). However, context does not specify other locations or if it is the closest. | Partially relevant | Partially accurate |
| 5 | As an off-campus SEAS grad student, is it worth it to buy a graduate meal plan, or should I just pay per meal or cook at home? | Conditional: buying a plan does not save money and locks you into a contract, so paying per meal or cooking at home is generally better, especially given retail location limits. | A student review [S10_reddit_grad_policy] suggests the plan does not save money compared to retail and locks you in. Given location limits [S6_grad_plans], cooking or paying per meal is recommended. | Relevant | Accurate |

---

## Failure Case Analysis

**Question that failed:**  
*"If I have most of my classes in Mudd, which on-campus dining locations are most convenient for grabbing lunch?"*

**What the system returned:**  
The system returned that only "Faculty House" was available in the context near Mudd and stated that the context did not contain other locations.

**Root cause (tied to a specific pipeline stage):**  
This was a **Retrieval Stage** failure caused by our **Chunking Strategy**. In `index.py`, we split the `S4_engineering_dining` page into 6 very small chunks (one for the intro and one for each of the 5 locations). Because they were separate chunks, the top-k retriever (k=5) returned the intro chunk (`S4_engineering_dining_c0`) and the Faculty House chunk (`S4_engineering_dining_c5`) along with other general dining guides. The other Mudd-adjacent location chunks (Blue Java, Chef Mike's, Chef Don's, and Fac Shack) did not rank in the top-5 similarity results, leaving the LLM with incomplete context to answer the query.

**What you would change to fix it:**  
To fix this, we should merge the location lists in `S4` into a single combined chunk (or use a larger chunk size for location guides) rather than splitting them into separate files. This guarantees that when the engineering dining page is retrieved, all Mudd-adjacent locations are passed to the LLM together.

---

## Spec Reflection

**One way the spec helped you during implementation:**  
The `planning.md` document pre-defined our custom chunking strategy for each source type (directories, Reddit comments, and policies). Having this laid out in the spec allowed us to implement `index.py` with specific modular chunking functions directly, rather than using trial-and-error with a general chunker.

**One way your implementation diverged from the spec, and why:**  
The ingestion pipeline in the spec initially assumed we would scrape live URLs on the fly using standard `requests`. However, during implementation, we discovered that Columbia Dining and Reddit blocked standard scraper requests (returning HTTP 403 or Cloudflare captcha verification pages). We diverged by building a robust fallback mechanism in `ingest.py` to use curated pre-scraped text when blocked, ensuring the pipeline runs successfully in any environment.

---

## AI Usage

**Instance 1**
- *What I gave the AI:* The requests fetching block from `ingest.py` and asked how to handle Cloudflare verification blocks that return HTTP 200.
- *What it produced:* A Python helper to check the response text for common verification keywords and lower character counts.
- *What I changed or overrode:* I adjusted the character threshold limit from 500 to 150 because some legitimate small API responses or JSONs are naturally short, but Reddit's verification page was exactly 37 characters.

**Instance 2**
- *What I gave the AI:* The custom location chunking requirements for `S4` and `S7` from `planning.md`.
- *What it produced:* A generic regex-based text splitter utilizing markdown headers.
- *What I changed or overrode:* I overrode this by writing explicit string splitting logic on `\n\d+\.\s+` and `- ` because the raw text was not structured with markdown hashes (`#`), but rather formatted as numbered lists and bullet points.

---
