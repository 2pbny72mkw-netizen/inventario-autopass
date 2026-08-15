AUTOPASS INVENTÁRIO DE CAMPO — V9.0
Data: 15/08/2026

Principais evoluções
- Técnico orientado por localização: estações próximas em até 6 km, ordenadas por distância.
- Estações integradas: uma estação física pode oferecer múltiplas linhas/operações (ex.: Luz, Brás, Barra Funda).
- Seleção manual preservada para localidades externas ou exceções.
- Confronto GPS x referência da localidade: aviso >250 m; limite padrão 600 m com justificativa de exceção.
  Limites podem ser ajustados no Render por FIELD_GPS_WARN_DISTANCE_M e FIELD_GPS_MAX_DISTANCE_M.
- Aprendizado geográfico: API calcula referência observada robusta a partir de coletas confiáveis, sem sobrescrever a referência oficial.
- Mapa gerencial: marcador das coletas GPS usa a foto do técnico, em conceito de avatar circular.
- Central de Equipes mantém atualização de localização e foto dos integrantes.
- Novo perfil RH: visualiza Equipes e administra Usuários; sem acesso de gravação de inventário.
- PWA/cache atualizado para V9 (autopass-v9-0) e arquivos com cache-busting para evitar tela/app antigo.
- app.py atualizado para V9.0 e manifest servido corretamente.

Observação
As referências observadas são apoio de calibração. Não alteram automaticamente coordenadas oficiais.
