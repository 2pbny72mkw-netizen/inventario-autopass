AUTOPASS — V1.3 OPERACIONAL + DASHBOARD EXECUTIVO V4.1
================================================================

OBJETIVO
Transformar a coleta de campo em informação auditável:
Base oficial + inventário realizado + WhatsApp + fotos/vídeos + concorrência.

O QUE ENTRA NESTA RELEASE

1. CENTRO DE EVIDÊNCIAS DE CAMPO
- Nova tela /evidencias-campo.
- Visitas por estação, data e responsável.
- Itens detectados no WhatsApp.
- Confronto automático com a BaseAsset e o Inventory.
- Status de auditoria:
  * CONFORME / JÁ INVENTARIADO
  * CONFIRMADO EM CAMPO / FALTA PROMOVER
  * DIVERGÊNCIA DE LOCALIDADE
  * NOVO / NÃO PREVISTO
  * PENDENTE DE REVISÃO
  * EVIDÊNCIA FORA DO PARQUE OFICIAL

2. FOTOS E VÍDEOS
- Galeria por visita/localidade.
- Imagens com carregamento lazy.
- Vídeos reproduzíveis no navegador.
- Mídias armazenadas no Cloudflare R2 quando configurado.
- Fallback local temporário existe, mas R2 é recomendado para produção.

3. WHATSAPP COMPLETO / DEDUPLICAÇÃO
- Upload máximo elevado para 160 MB.
- Parser aceita "Linha 12", "Linha 11 coral", "Linha 1-Azul" etc.
- Trata mensagens simultâneas de equipes diferentes pelo responsável.
- Mensagens complementares de POS são ligadas à última estação do mesmo técnico.
- Fotos enviadas antes/depois do texto são associadas por janela de tempo.
- Reimportar o mesmo histórico não duplica visita/item/mídia.
- TCI / TCI NEO / MK / MK NEO são confrontados como ATM, preservando o modelo.
- POS captura TOP, SN e patrimônio quando presentes.
- Concorrência é armazenada separadamente e não contamina o parque oficial.
- Rack/Hack fica como evidência fora do parque oficial.

4. BANCO DE DADOS
Novas tabelas:
- field_evidence_visits
- field_evidence_items
- field_evidence_media
db.create_all() cria as tabelas automaticamente no deploy.

5. SEGURANÇA DO DADO
IMPORTANTE: o repositório GitHub é público.
Por isso o ZIP do WhatsApp, fotos, vídeos, nomes/mensagens e IDs de mídia NÃO foram
embutidos neste pacote GitHub.
Depois do deploy, abra /importar-whatsapp e envie o ZIP diretamente pela aplicação.
O arquivo e as mídias vão para o R2/PostgreSQL, não para o repositório público.

6. PROMOÇÃO CONTROLADA
- Evidência não altera automaticamente os Big Numbers oficiais.
- Gestor pode clicar "Promover" para transformar um item revisado em Inventory.
- Se já existir, o sistema apenas vincula a evidência ao inventário existente.

7. EXCEL V4
- A exportação Excel ganha a aba "Evidências de Campo".
- Permite consulta futura e auditoria externa.

8. DASHBOARD V4
- Nova faixa "Evidências de campo" com:
  Visitas | Itens | Conformes | Revisar | Fotos/Vídeos
- Link direto para o Centro de Evidências.
- Carregamento da evidência é assíncrono e não bloqueia KPIs oficiais.

9. MAPA
- Preservado nesta release.
- Linha 4-Amarela e Linha 17-Ouro continuam como intervenção específica futura.

COMO SUBIR
1. Substitua o conteúdo do repositório pelo conteúdo deste ZIP.
2. Commit único.
3. Render -> Deploy latest commit.
4. Aguarde Live.
5. Ctrl+F5.

TESTES DE VERSÃO
Console em /gerencial:
  window.AUTOPASS_MANAGER_VERSION
Esperado:
  "dashboard-v4-1"

TESTE DO WHATSAPP
1. Abra /importar-whatsapp.
2. Selecione o arquivo:
   WhatsApp Chat - Inventário de Equipamentos (Autopass)(1).zip
3. Clique "Analisar e confrontar".
4. Revise os totais e algumas estações.
5. Clique "Importar evidências para o PostgreSQL".
6. Abra /evidencias-campo.
7. Confira fotos, itens e status de auditoria.

STORAGE
Antes da importação, como Gestor, teste:
  /r2-status
Se R2 estiver OK, as fotos/vídeos ficam persistentes.
Se R2 não estiver configurado, a importação ainda funciona com fallback local,
mas as mídias podem desaparecer em reinício/deploy do Render.

PRIVACIDADE
Não faça upload do ZIP bruto do WhatsApp para o GitHub público.
Use somente a tela /importar-whatsapp do sistema V4.
