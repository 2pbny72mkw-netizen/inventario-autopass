Inventário Autopass — V56-A.4 HOTFIX2

Correção direcionada à Troca de Chip Recarga / Validadores.

- Corrige estação com contador de validadores previstos, mas lista de ativos vazia.
- Unifica a regra de associação linha + estação entre contador/listagem/gravação.
- Normaliza nomes equivalentes de estação, por exemplo SÉ x PRAÇA DA SÉ.
- Usa comparação por tokens inteiros para evitar casar SÉ com BRESSER.
- Quando existem ativos detalhados, o total exibido passa a refletir a quantidade real da base detalhada.
- Mantém expected_validator como fallback para localidades ainda sem ativos detalhados.

Teste prioritário: METRÔ > 03 - VERMELHA > SÉ.
