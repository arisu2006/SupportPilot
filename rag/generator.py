"""
Resolution generation.
Uses a deterministic mock generator that extracts steps from retrieved KB
articles and adds citations. Structured so a real LLM can replace it later.
"""


def build_context(results: list) -> str:
    """Concatenate retrieved documents into a context block for an LLM."""
    if not results:
        return ""
    parts = []
    for result in results:
        parts.append(
            f"""SOURCE: {result['id']}
TITLE: {result['title']}
CATEGORY: {result['category']}
RELEVANCE: {result['score']:.2f}
{result['content'].strip()}
============================="""
        )
    return "\n\n".join(parts)


def create_prompt(ticket: dict, context: str) -> str:
    """
    Prompt template for a real LLM.
    The model must ground answers in the supplied knowledge base.
    """
    return f"""You are an enterprise IT support assistant.
Your task is to troubleshoot the following support ticket.

TICKET
------
Title: {ticket.get('title', '')}
Description: {ticket.get('description', '')}
Category: {ticket.get('category', 'Unknown')}
Priority: {ticket.get('priority', 'Unknown')}

KNOWLEDGE BASE
--------------
{context}

INSTRUCTIONS
------------
1. Use the knowledge base as the primary source.
2. Do not invent company-specific policies.
3. Provide numbered troubleshooting steps.
4. Explain the likely cause when possible.
5. Cite the source KB article ID for each major step.
6. If the knowledge base does not contain enough information,
   clearly state that additional investigation is required.
7. Keep the response concise and suitable for a support agent.

Generate the recommended resolution.
"""


def generate_resolution(ticket: dict, retrieved_docs: list) -> dict:
    """
    Mock resolution generator.
    Extracts numbered steps from retrieved documents and attaches citations.
    Returns a structured dict ready for the UI and API.
    """
    if not retrieved_docs:
        return {
            "status": "INSUFFICIENT_KNOWLEDGE",
            "summary": "No sufficiently relevant knowledge-base articles were found.",
            "steps": [],
            "citations": [],
            "full_text": (
                "No sufficiently relevant knowledge-base articles were found. "
                "Please escalate to a human agent or expand the knowledge base."
            ),
        }

    steps = []
    citations = []
    step_number = 1

    for doc in retrieved_docs:
        lines = doc["content"].split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Capture numbered steps (1. 2. …)
            if len(line) > 2 and line[0].isdigit() and line[1] in ".）)":
                cleaned = line.split(".", 1)[-1].strip()
                if not cleaned:
                    continue
                steps.append(
                    {
                        "number": step_number,
                        "text": cleaned,
                        "source_id": doc["id"],
                        "source_title": doc["title"],
                    }
                )
                citations.append(
                    {
                        "step": step_number,
                        "kb_id": doc["id"],
                        "kb_title": doc["title"],
                        "score": round(doc["score"], 3),
                    }
                )
                step_number += 1

    # Fallback if no numbered steps were found — use first sentences
    if not steps:
        for doc in retrieved_docs[:2]:
            snippet = " ".join(doc["content"].split())[:220].strip()
            if snippet:
                steps.append(
                    {
                        "number": step_number,
                        "text": snippet + ("…" if len(snippet) >= 220 else ""),
                        "source_id": doc["id"],
                        "source_title": doc["title"],
                    }
                )
                citations.append(
                    {
                        "step": step_number,
                        "kb_id": doc["id"],
                        "kb_title": doc["title"],
                        "score": round(doc["score"], 3),
                    }
                )
                step_number += 1

    # Closing recommendation
    steps.append(
        {
            "number": step_number,
            "text": (
                "If the issue persists after completing the above steps, "
                "test from another network or device to isolate the cause, "
                "then escalate to Tier 2 with the collected diagnostics."
            ),
            "source_id": None,
            "source_title": "General best practice",
        }
    )

    lines = ["Recommended Resolution:"]
    for s in steps:
        cite = f"  [Source: {s['source_id']} – {s['source_title']}]" if s["source_id"] else ""
        lines.append(f"{s['number']}. {s['text']}{cite}")

    full_text = "\n".join(lines)

    return {
        "status": "OK",
        "summary": f"Generated {len(steps)} troubleshooting steps from {len(retrieved_docs)} knowledge articles.",
        "steps": steps,
        "citations": citations,
        "full_text": full_text,
        "top_sources": [
            {"id": d["id"], "title": d["title"], "score": round(d["score"], 3)}
            for d in retrieved_docs
        ],
    }
