# PWA File Checker

Script para verificar a integridade e organização das pastas de clientes.

## Verificações

1. Identificar pastas de CONSULTAS desatualizadas (sem modificação em 30 dias)
2. Identificar pastas que estão ocupando muito espaço (top 10 maiores)
3. Copiar os Modelos da pasta Raíz (ZMODELOS) para a Pasta Modelos (MODELOS)
4. Verificar integridade dos nomes das pastas (padrão `NOME (numero)`)
5. Verificar problemas de nomeação de arquivos (extensões, padrões de data, CNIS)

## Execução

### Manual
```bash
.venv/bin/python run.py
```

### Automatizada (Cron)
O script `cron_runner.py` executa todas as verificações, gera um JSON estruturado e envia para o webhook do N8N.

```bash
.venv/bin/python cron_runner.py
```

**Agendamento:** Toda Quarta-Feira às 09:00 via systemd timer.
Se o computador estiver desligado no horário, executa automaticamente na próxima inicialização (`Persistent=true`).

**Comandos úteis:**
```bash
# Executar manualmente
systemctl --user start pwa-file-checker.service

# Ver status do timer
systemctl --user list-timers

# Ver logs
cat cron_runner.log
journalctl --user -u pwa-file-checker.service
```

## Audio Daily Runner (transcrição + relatório de atendimentos)

Roda diariamente às 04:00, varre `BASE_DIR/<CLIENTE (XXX)>/ATENDIMENTO/` por arquivos de áudio, transcreve com **faster-whisper** localmente (sem expor o áudio) e gera um relatório estruturado via **OpenRouter**.

### Saída ao lado do áudio

```
ATENDIMENTO/
├── audio-atendimento-2026-05-06.m4a
├── audio-atendimento-2026-05-06.m4a.transcricao.txt
└── audio-atendimento-2026-05-06.m4a.relatorio.md
```

Idempotente: pula áudios cujo `.transcricao.txt` e `.relatorio.md` já existem e estão mais recentes que o áudio.

### Configuração

No `.env`:
```
WHISPER_MODEL=small            # tiny, base, small, medium, large-v3
WHISPER_DEVICE=cpu             # cpu ou cuda
WHISPER_COMPUTE_TYPE=int8      # int8 (rápido CPU) | float16 (GPU)
WHISPER_LANGUAGE=pt

OPENROUTER_API_KEY=sk-or-...   # https://openrouter.ai/keys
OPENROUTER_MODEL=anthropic/claude-sonnet-4
```

Sem `OPENROUTER_API_KEY` o relatório é pulado mas a transcrição continua funcionando.

### Comandos úteis

```bash
# Executar manualmente
.venv/bin/python audio_daily_runner.py
systemctl --user start pwa-audio-transcriber.service

# Ver status do timer
systemctl --user list-timers | grep audio

# Logs
tail -f audio_daily_runner.log
journalctl --user -u pwa-audio-transcriber.service -f
```

### LGPD

- **Áudio**: 100% local. Whisper roda no seu computador, áudio nunca sai.
- **Texto da transcrição**: enviado à OpenRouter para gerar o resumo. Trate o modelo escolhido como você trataria um terceiro com acesso aos dados do cliente. Para conformidade total, use modelo com acordo DPA ou rode resumo localmente também (Ollama, futuramente).

## Configuração geral

- `.env` - Define `BASE_DIR` (diretório raiz dos arquivos), webhook, chaves de API
- `src/config/settings.py` - Constantes e thresholds
- Webhook N8N configurado em `cron_runner.py`

## ToDo

1. ~~Adicionar um CRON Job para Execução do Script~~ (feito - systemd timer semanal)
2. ~~Enviar notificação~~ (feito - webhook N8N)
3. Criar Backup automatizado - rsync?
4. Adicionar acesso remoto ao rsync/backups - NAS?
5. Melhorar sistema de integridade geral => criar script separado para Não Clientes
6. Melhorar sistema de integridade geral => compressão e diminuição dos arquivos
7. Melhorar sistema de integridade geral => melhorar sistema de nomeação dos `CNIS`
8. Adicionar mini servidor com raspberrypi
9. Adicionar compressor PDF > 5mb?

`gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/screen -dNOPAUSE -dQUIET -dBATCH -dDetectDuplicateImages=true -dEmbedAllFonts=false -dSubsetFonts=true -dConvertCMYKImagesToRGB=true -dCompressFonts=true -dDownsampleColorImages=true -dColorImageResolution=72 -dDownsampleGrayImages=true -dGrayImageResolution=72 -dDownsampleMonoImages=true -dMonoImageResolution=72 -sOutputFile=highly_compressed.pdf input.pdf`
