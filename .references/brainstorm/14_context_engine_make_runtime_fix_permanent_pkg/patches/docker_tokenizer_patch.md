# Tokenizer Docker/runtime patch

`docker/lightrag.Dockerfile` already sets:

```Dockerfile
ENV TIKTOKEN_CACHE_DIR=/app/.cache/tiktoken
```

and runs `python -m lightrag.tools.download_cache`.

Keep that, but verify the cache exists in the final image. Add a build check:

```Dockerfile
RUN test -d "$TIKTOKEN_CACHE_DIR" && find "$TIKTOKEN_CACHE_DIR" -maxdepth 2 -type f | head
```

In generated `domain.env`, also render:

```env
TIKTOKEN_CACHE_DIR=/app/.cache/tiktoken
```

If the managed container still tries to resolve public tokenizer URLs at startup, add a local cache verification command or configure the specific LightRAG/tiktoken offline env var supported by the installed LightRAG version.
