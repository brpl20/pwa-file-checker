"""
Generate a structured report (relatorio) from a transcript via OpenRouter.

The report mirrors the Ficha de Atendimento (Previdenciário) format so it can
be pasted directly into the manual workflow.

LGPD note: only the TEXT transcript is sent to OpenRouter — never the raw audio.
The transcript may still contain sensitive data; choose the OpenRouter model
according to your data-protection posture.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path

import requests

from src.config.settings import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    OPENROUTER_MODEL,
    REPORT_SUFFIX,
    TRANSCRIPT_SUFFIX,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Você é um assistente jurídico especializado em direito previdenciário brasileiro. \
Recebe a transcrição de um atendimento inicial entre um(a) advogado(a) e um(a) cliente \
e produz um relatório estruturado pré-preenchendo a Ficha de Atendimento padrão do escritório.

Regras:
- Responda em português do Brasil.
- Use apenas informações presentes na transcrição. Se um campo não foi mencionado, escreva: "(não mencionado)".
- Não invente dados (nome, CPF, RG, datas, valores).
- Quando a transcrição mencionar siglas ou termos técnicos (CNIS, DER, DIB, PPP, LTCAT, BPC, etc.), preserve-os.
- Identifique a demanda principal do cliente (aposentadoria por idade, BPC, pensão por morte, etc.) com base no que foi conversado.
- Liste documentos que o cliente disse ter / trouxe e separadamente os que ainda faltam.
- Para a "narrativa do cliente", produza um resumo de 5–10 linhas com os fatos relevantes para a estratégia.
- Saída em Markdown."""

USER_TEMPLATE = """# Cliente
Pasta: **{client_folder}**

# Transcrição do atendimento
{transcript}

---

Produza o relatório no formato abaixo (Markdown), preenchendo cada campo a partir da transcrição:

```markdown
# Relatório de Atendimento — {client_folder}

**Gerado em:** {generated_at}
**Modelo:** {model}

## 1. Identificação (extraída da conversa)
- Nome completo:
- Data de nascimento:
- Estado civil:
- Profissão atual / última:
- RG / CPF:
- E-mail / Telefone:
- Endereço:

## 2. Histórico previdenciário
- Já é segurado(a) do INSS?
- Possui CNIS?
- Tempo total de contribuição estimado:
- DER anterior:
- Indeferimento anterior?
- DIB atual (se já tem benefício):

## 3. Atividades exercidas
- Tipo (urbana / rural / mista):
- Atividades especiais (insalubre / periculosa)?
- Períodos rurais?
- Empresas anteriores:

## 4. Demanda identificada
- Tipo de benefício/ação pretendido:
- Justificativa (o que foi conversado):

## 5. Documentos apresentados
- (lista do que o cliente disse ter trazido)

## 6. Documentos pendentes (a solicitar)
- (lista do que falta)

## 7. Narrativa do cliente (resumo)
(5–10 linhas com os fatos relevantes para a estratégia)

## 8. Próximos passos sugeridos
- (com base no que foi conversado)

## 9. Pontos de atenção
(qualquer alerta relevante: prazos, contradições na história, riscos processuais)
```"""


def report_path_for(transcript_path: Path) -> Path:
    """Compute the report path from the transcript path.

    Example:
      audio.m4a.transcricao.txt -> audio.m4a.relatorio.md
    """
    if transcript_path.name.endswith(TRANSCRIPT_SUFFIX):
        base = transcript_path.name[: -len(TRANSCRIPT_SUFFIX)]
        return transcript_path.parent / (base + REPORT_SUFFIX)
    return transcript_path.with_suffix(REPORT_SUFFIX)


def needs_report(transcript_path: Path) -> bool:
    """True if the report is missing or older than the transcript."""
    report = report_path_for(transcript_path)
    if not report.exists():
        return True
    return transcript_path.stat().st_mtime > report.stat().st_mtime


def _strip_code_fence(text: str) -> str:
    """If the model wrapped the report in a ```markdown ... ``` block, strip it."""
    m = re.match(r"^\s*```(?:markdown)?\s*\n(.*)\n```\s*$", text, re.DOTALL)
    return m.group(1) if m else text


def summarize(transcript: str, client_folder: str) -> str:
    """Call OpenRouter to generate the report. Returns the report markdown."""
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY not set in .env")

    user_msg = USER_TEMPLATE.format(
        client_folder=client_folder,
        transcript=transcript,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        model=OPENROUTER_MODEL,
    )

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        "temperature": 0.2,
    }

    resp = requests.post(
        f"{OPENROUTER_BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/brpl/pwa-file-checker",
            "X-Title": "PWA Audio Summarizer",
        },
        data=json.dumps(payload),
        timeout=180,
    )
    resp.raise_for_status()
    body = resp.json()

    try:
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Unexpected OpenRouter response: {body}") from e

    return _strip_code_fence(content).strip()


def summarize_and_save(transcript_path: Path, client_folder: str) -> Path:
    """Read transcript, generate report, write `<audio>.relatorio.md`. Returns the report path."""
    transcript = transcript_path.read_text(encoding="utf-8")
    if not transcript.strip():
        raise RuntimeError(f"Empty transcript: {transcript_path}")

    report = summarize(transcript, client_folder)
    report_path = report_path_for(transcript_path)
    report_path.write_text(report, encoding="utf-8")
    logger.info(f"Saved report: {report_path}")
    return report_path
