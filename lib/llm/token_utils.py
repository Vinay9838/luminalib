import tiktoken


def count_tokens(text: str, model: str = "gpt-4") -> int:
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))


def chunk_text(text: str, max_tokens: int = 2000, model: str = "gpt-4"):
    encoding = tiktoken.encoding_for_model(model)
    tokens = encoding.encode(text)

    for i in range(0, len(tokens), max_tokens):
        chunk = tokens[i:i + max_tokens]
        yield encoding.decode(chunk)