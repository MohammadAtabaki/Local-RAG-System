import os
import json
import re
from PyPDF2 import PdfReader
from pathlib import Path
from sentence_transformers import SentenceTransformer, util
from collections import Counter
import unicodedata

embedder = SentenceTransformer("all-MiniLM-L6-v2")

def clean_unicode(text):
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^\x20-\x7E]+", "", text)

def extract_text_from_pdf(file_path):
    reader = PdfReader(file_path)
    pages = []
    headers = []
    footers = []
    for page in reader.pages:
        text = page.extract_text() or ""
        lines = text.strip().split("\n")
        if lines:
            headers.append(lines[0].strip())
            footers.append(lines[-1].strip())
        pages.append(lines)
    return pages, headers, footers


def join_wrapped_lines(text):
    lines = text.split('\n')
    joined = []
    buffer = ""

    for line in lines:
        line = line.strip()
        if not line:
            if buffer:
                joined.append(buffer.strip())
                buffer = ""
            joined.append("")  # Preserve intentional paragraph break
            continue

        if buffer and not buffer.endswith(('.', '?', '!', ':')) and not re.match(r'^\d+[.)]?', line):
            buffer += " " + line
        else:
            if buffer:
                joined.append(buffer.strip())
            buffer = line

    if buffer:
        joined.append(buffer.strip())

    return '\n'.join(joined)



def identify_common_lines(lines_list):
    counter = Counter(lines_list)
    return set([line for line, count in counter.items() if count > 1])

def normalize(text):
    return re.sub(r'\s+', ' ', str(text or '')).strip()

def infer_title_semantic(text, fallback="Untitled Section"):
    lines = text.split("\n")
    candidates = [normalize(line) for line in lines if 4 <= len(line.split()) <= 12 and not line.endswith('.')]
    if not candidates:
        return fallback
    para_embedding = embedder.encode([text])[0]
    cand_embeddings = embedder.encode(candidates)
    scores = util.pytorch_cos_sim([para_embedding], cand_embeddings)[0]
    best_idx = scores.argmax().item()
    best_score = scores[best_idx].item()
    if best_score < 0.4:
        return fallback
    return candidates[best_idx]


def split_paragraphs(text):
    text = join_wrapped_lines(text)
    raw_paragraphs = re.split(r'\n\s*\n|(?<=\.)\s{2,}', text)
    return [normalize(p) for p in raw_paragraphs if len(normalize(p)) > 50]


    if len(buffer) >= 2:
        paragraphs.append(' '.join(buffer))
    return [p for p in paragraphs if len(p.split()) > 10]

def summarize_paragraph(paragraph):
    sentences = re.split(r'(?<=[.!?]) +', paragraph)
    if len(sentences) < 2:
        return normalize(paragraph[:150])
    embeddings = embedder.encode(sentences)
    scores = util.pytorch_cos_sim(embeddings, embeddings).mean(dim=1)
    return normalize(sentences[scores.argmax()])

def save_json(data, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def format_prompt_parsev3(prev_doc_context, prev_chapter_context, prev_page_context):
    prev_doc_context = "merged with " + prev_doc_context if prev_doc_context else ""
    prev_chapter_context= "or if it's not yet available use this " + prev_chapter_context if prev_chapter_context else ""
    prev_page_context= "or if it's not yet available use this " + prev_page_context if prev_page_context else ""

    systemp = f"""   
You are an expert document parser. Your task is to extract structured information from documents and produce a well-formed JSON according to the following schema:

Your response must begin with a valid JSON object. Do not include any commentary or explanations. Do not use markdown. Do not prefix the JSON with ```json or any other characters.

### **Top-Level JSON Structure**

{{
  "document_context": "(General summary of the document’s overall content, emphasizing the key information from the first page where available {prev_doc_context}.)",
  "pages": [
    {{
      "chapter_context": "(Summary of the chapter’s content. If not available, use the previous chapter context.)",
      "page_context": "(Summary of the page’s content. If not available, use the previous page context.)",
      "page_number": "(The page number.)",
      "content": [
        // Extracted elements (paragraphs, tables, images)
      ]
    }},
    ...
  ]
}}

### **Content Extraction Rules**

- **Paragraphs:** 
{{
  "type": "paragraph",
  "title": "(Descriptive title for the paragraph)",
  "context": "(Semantic context of the paragraph)",
  "text": "(Exact extracted text)"
}}
- **Images:**
{{
  "type": "image",
  "title": "(Descriptive title for the image)",
  "context": "(Semantic context of the image)",
  "text": "(Concise description of the image)"
}}
- **Tables:**
{{
  "type": "table",
  "title": "(Descriptive title for the table)",
  "context": "(Semantic context of the table)",
  "text": "(Extracted table in CSV format, with headers)"
}}

The final JSON must be syntactically correct.
    """

    userp = f"""
Extract the information from the provided document pages according to the defined rules.
Process pages sequentially from first to last.
Structure the output as a JSON according to the defined rules.
Ensure that page context inheritance, formatting, and content fidelity are respected.
"""
    return systemp, userp



def process_document(file_path, output_dir):
    pages_raw, headers, footers = extract_text_from_pdf(file_path)
    common_headers = identify_common_lines(headers)
    common_footers = identify_common_lines(footers)

    all_text_for_summary = ' '.join([' '.join(p) for p in pages_raw[:3]])
    parsed_data = {
        "document_context": summarize_paragraph(clean_unicode(all_text_for_summary)),
        "pages": []
    }

    prev_chapter = ""
    for i, lines in enumerate(pages_raw):
        clean_lines = [line for line in lines if line.strip() not in common_headers and line.strip() not in common_footers]
        content = '\n'.join(clean_lines)
        content = clean_unicode(content)
        paragraphs = split_paragraphs(content)
        page_summary = summarize_paragraph(' '.join(paragraphs))
        chapter = infer_title_semantic('\n'.join(clean_lines))

        page_data = {
            "chapter_context": chapter if chapter else prev_chapter,
            "page_context": page_summary,
            "page_number": i + 1,
            "content": []
        }
        prev_chapter = chapter

        for para in paragraphs:
            para_summary = summarize_paragraph(para)
            para_title = infer_title_semantic(para)
            page_data["content"].append({
                "type": "paragraph",
                "title": para_title,
                "context": para_summary,
                "text": normalize(para)
            })

        parsed_data["pages"].append(page_data)

    # Optional: use LLM to enhance parsing (disabled by default)
    # Uncomment below to use prompt-based parsing
    # full_text = "\n".join(pages)
    # prev_doc_context = ""
    # prev_chapter_context = ""
    # prev_page_context = ""
    # systemp, userp = format_prompt_parsev3(prev_doc_context, prev_chapter_context, prev_page_context)
    # prompt = f"{systemp}\n\n{userp}\n\nDocument Content:\n{full_text[:4000]}"
    # response = generate_llm_response(prompt)
    # try:
    #     match = re.search(r'\{.*\}', response, re.DOTALL)
    #     if not match:
    #         raise ValueError("LLM did not return a JSON object")
    #     json_text = match.group(0)
    #     parsed_data = json.loads(json_text)
    # except Exception as e:
    #     parsed_data = {"error": str(e), "raw_response": response}

    filename = Path(file_path).stem + ".json"
    save_json(parsed_data, os.path.join(output_dir, filename))
