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

## Configuração

- `.env` - Define `BASE_DIR` (diretório raiz dos arquivos)
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
