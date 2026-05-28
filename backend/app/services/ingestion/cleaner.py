import re

def clean_text(text: str) -> str:
    """
    Cleans raw text by stripping control characters, normalizing whitespace,
    and resolving spacing discrepancies while maintaining paragraph boundaries.
    """
    if not text:
        return ""
    
    # 1. Normalize line endings to standard Unix line feeds
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
    
    # 2. Strip non-printable control characters (excluding tab and newlines)
    cleaned = re.sub(r"[^\x20-\x7E\n\t]", "", cleaned)
    
    # 3. Collapse multiple consecutive horizontal spaces to a single space
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    
    # 4. Collapse three or more consecutive line feeds to two line feeds (keep paragraph splits)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    
    # 5. Trim trailing whitespaces on individual lines
    cleaned = "\n".join(line.strip() for line in cleaned.split("\n"))
    
    return cleaned.strip()
