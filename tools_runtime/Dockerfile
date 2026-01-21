FROM python:3.12-slim

WORKDIR /app

COPY agents /app/agents
COPY tools_runtime /app/tools_runtime

RUN pip install fastapi uvicorn

CMD ["uvicorn", "tools_runtime.tool_server:app", "--host", "0.0.0.0", "--port", "9000"]
