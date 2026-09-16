# Inventário Autopass — V82.11 ENXUTA

Correções prioritárias de correlação de bases.

- Mapeamento ATM: normalização ampliada do Modelo (MK/MKNeo), consultando variações de campos da base mestre e complemento; preserva `model_raw` para diagnóstico.
- Novo diagnóstico `/api/mapeamento-atm/diagnostico-modelos` com totais por modelo e amostras MKNeo/não informadas.
- Monitoramento de Coletas: reconciliação por ATM + data passa a combinar campos complementares de registros importados da mesma coleta, em vez de depender de um único registro.
- Priorização do registro com maior completude e fechamento sistêmico R0050 quando disponível.
- Declarado, Apurado, GTV e observação podem ser enriquecidos retroativamente a partir de registros irmãos da mesma ATM/data, sem converter ausência em zero.
- Mantidas as regras e funcionalidades da V82.10.
