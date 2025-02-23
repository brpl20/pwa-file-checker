# Descrição
Esse script simples serve para verificar:
1. A integralidade do nome das pastas;
2. Identificar pastas que estão ocupando muito espaço;
3. Copiar os Modelos da pasta Raíz (zMODELOS) para a Pasta Modelos (MODELOS);
4. Identificar pastas de CONSULTAS desatualizadas;
5. Verificar integridade geral de arquivos;

## ToDo
1. Adicionar um CRON Job Diário para Execução do Script;
2. Enviar notificação;
3. Criar Backup automatizado - rsync?;
4. Adicionar acesso remoto ao rsync/backups - NAS?;
4. Melhorar sistema de integridade geral => alterar downcase to upcase;
5. Melhorar sistema de integridade geral => criar script separado para Não Clientes
6. Melhorar sistema de integridade geral => compressão e diminuição dos arquivos
7. Melhorar sistema de integridade geral => melhorar sistema de nomeação dos `CNIS`
8. Adicionar mini servidor com raspberrypi;