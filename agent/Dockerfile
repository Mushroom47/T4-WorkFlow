FROM python:3.13-slim@sha256:bf44cdfcb76cd3b41e879bc058fc37ec5872002ccfde7fcb765e218cde0cd79c

LABEL qfbench2.interface_version="2.0"
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# Build with agent/ as the context. Explicit COPY keeps reference data, frozen
# example inputs, private evidence, host caches and development tools out.
COPY analyze.py candidate.py ./
COPY baseline_agent/ ./baseline_agent/
COPY contracts/ ./contracts/
COPY LICENSE.upstream THIRD-PARTY-NOTICES.md upstream-manifest.json ./

ENTRYPOINT ["python", "analyze.py"]
CMD ["analyze", "--help"]
