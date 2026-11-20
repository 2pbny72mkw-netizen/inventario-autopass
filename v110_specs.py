# -*- coding: utf-8 -*-
"""V88.0 REV20 — Descrição das telas que o app Android monta com o motor nativo (Build120+).

Cada tela usa as APIs de dados da web pela ponte (/api/mobile/v1/ponte/...), com a mesma regra de negócio e permissão.
Mudar/acrescentar uma tela aqui chega ao app no próximo login, sem Build novo.

Linguagem (resumo):
  "{campo}" ou "{a.b}" insere um valor do item; filtros: |data |datahora |num |simnao |maiusc
  modelo:  "lista" (lista + detalhe + formulários) ou "painel" (indicadores e barras)
  fonte:   url da API da web e onde estão os itens ("itens": "rows"); "offline": guarda no celular
  lista:   titulo, subtitulo, meta[], etiqueta{campo,cores}, busca[], filtros[], kpis[], ordem[]
  detalhe: secoes[{titulo, campos[[rotulo, modelo]]}], fotos{lista,url}, acoes[{rotulo, form | url+metodo, confirmar}]
  forms:   {chave: {titulo, envio{url, metodo, formato json|multipart}, campos[{nome, rotulo, tipo, obrigatorio, opcoes, valor}], offline}}
  tipos de campo: texto, area, numero, data, hora, lista, simnao, fotos, gps, oculto
  cores:   sucesso, aviso, info, perigo, neutro
"""

ST_CONCL = {"CONCLUÍDO": "sucesso", "CONCLUIDO": "sucesso", "CONCLUÍDA": "sucesso", "CONCLUIDA": "sucesso",
            "EM ANDAMENTO": "info", "PENDENTE": "aviso", "RASCUNHO": "neutro", "CANCELADA": "neutro", "CANCELADO": "neutro"}

TESTE = [["TESTADO_OK", "Testado – OK"], ["TESTADO_COM_DEFEITO", "Testado – com defeito"],
         ["NAO_FOI_POSSIVEL_TESTAR", "Não foi possível testar"], ["EQUIPAMENTO_INOPERANTE", "Equipamento inoperante"], ["OUTRO", "Outro"]]

SPECS = [
    # ------------------------------------------------------------------ FIELD
    {
        "key": "firmware", "titulo": "Atualização Firmware POS – CPTM", "grupo": "field", "icone": "build",
        "perms": ["field.firmware_pos_cptm"], "web": "/firmware-pos-cptm", "modelo": "lista",
        "fonte": {"url": "/api/firmware-pos-cptm", "itens": "rows", "offline": True},
        "lista": {
            "titulo": "{terminal_number} · {model}", "subtitulo": "{line} · {station}",
            "meta": ["{technician}", "{completed_at|data}"],
            "etiqueta": {"campo": "status", "cores": ST_CONCL},
            "busca": ["terminal", "terminal_number", "serial", "patrimony", "station", "line"],
            "filtros": [{"rotulo": "Pendentes", "campo": "status", "igual": "PENDENTE"},
                        {"rotulo": "Em andamento", "campo": "status", "igual": "EM ANDAMENTO"},
                        {"rotulo": "Concluídos", "campo": "status", "igual": "CONCLUÍDO"}],
            "kpis": [{"rotulo": "TOTAL"}, {"rotulo": "PENDENTES", "campo": "status", "igual": "PENDENTE", "tom": "aviso"},
                     {"rotulo": "CONCLUÍDOS", "campo": "status", "igual": "CONCLUÍDO", "tom": "sucesso"}],
            "ordem": [{"rotulo": "Estação", "campo": "station"}, {"rotulo": "Linha", "campo": "line"},
                      {"rotulo": "Conclusão", "campo": "completed_at", "desc": True}],
        },
        "detalhe": {
            "secoes": [{"titulo": "Equipamento", "campos": [["Terminal", "{terminal}"], ["Modelo", "{manufacturer} {model}"],
                                                             ["Série", "{serial}"], ["Patrimônio", "{patrimony}"], ["IP", "{ip}"]]},
                       {"titulo": "Local", "campos": [["Linha", "{line}"], ["Estação", "{station}"]]},
                       {"titulo": "Execução", "campos": [["Técnico", "{technician}"], ["Início", "{started_at|datahora}"],
                                                          ["Conclusão", "{completed_at|datahora}"], ["Observação", "{notes}"]]}],
            "fotos": {"lista": "photos", "url": "{url}"},
            "acoes": [{"rotulo": "Registrar atualização", "form": "atualizar", "principal": True}],
        },
        "forms": {
            "atualizar": {
                "titulo": "Atualização de firmware", "offline": True,
                "envio": {"url": "/api/firmware-pos-cptm/{id}", "metodo": "POST", "formato": "multipart"},
                "campos": [
                    {"nome": "status", "rotulo": "Situação", "tipo": "lista", "obrigatorio": True, "valor": "{status}",
                     "opcoes": ["PENDENTE", "EM ANDAMENTO", "CONCLUÍDO"]},
                    {"nome": "photos", "rotulo": "Fotos (até 8)", "tipo": "fotos", "max": 8},
                    {"nome": "notes", "rotulo": "Observação", "tipo": "area", "valor": "{notes}"},
                ],
            }
        },
    },
    {
        "key": "mapeamento_atm", "titulo": "Mapeamento ATM", "grupo": "field", "icone": "list",
        "perms": ["field.atm_mapping", "field.atm_mapping_manage"], "web": "/field/mapeamento-atm", "modelo": "lista",
        "fonte": {"url": "/api/mapeamento-atm", "itens": "rows", "offline": True},
        "lista": {
            "titulo": "ATM {atm_id} · {model}", "subtitulo": "{line} · {station}",
            "meta": ["{physical_access}", "{technician}"],
            "etiqueta": {"campo": "status", "cores": ST_CONCL},
            "busca": ["atm_id", "station", "line", "model", "technician"],
            "filtros": [{"rotulo": "Pendentes", "campo": "status", "igual": "PENDENTE"},
                        {"rotulo": "Concluídos", "campo": "status", "igual": "CONCLUIDO"},
                        {"rotulo": "Furos sem vedação", "campo": "holes_sealed", "igual": False}],
            "kpis": [{"rotulo": "TOTAL"}, {"rotulo": "PENDENTES", "campo": "status", "igual": "PENDENTE", "tom": "aviso"},
                     {"rotulo": "CONCLUÍDOS", "campo": "status", "igual": "CONCLUIDO", "tom": "sucesso"}],
            "ordem": [{"rotulo": "Estação", "campo": "station"}, {"rotulo": "ATM", "campo": "atm_id"}],
        },
        "detalhe": {
            "secoes": [{"titulo": "ATM", "campos": [["ATM", "{atm_id}"], ["Modelo", "{model}"], ["Linha", "{line}"],
                                                     ["Estação", "{station}"], ["Acesso", "{physical_access}"],
                                                     ["Transações", "{transactions}"]]},
                       {"titulo": "Segurança", "campos": [["Noteiro", "{bill_acceptor}"], ["Noteiro fixado", "{acceptor_fixed|simnao}"],
                                                          ["Noteiro soldado", "{acceptor_welded|simnao}"], ["Tem furos", "{has_holes|simnao}"],
                                                          ["Furos vedados", "{holes_sealed|simnao}"], ["Porta traseira do cofre", "{rear_safe_door|simnao}"]]},
                       {"titulo": "Registro", "campos": [["Técnico", "{technician}"], ["Atualizado", "{updated_at|datahora}"],
                                                         ["Observação", "{notes}"]]}],
            "fotos": {"lista": "photo_items", "url": "{url}"},
        },
    },
    {
        "key": "chip_recarga", "titulo": "Troca de Chips – Recarga", "grupo": "field", "icone": "list",
        "perms": ["field.chip_recarga"], "web": "/troca-chips", "modelo": "lista",
        "fonte": {"url": "/api/chip-swaps/", "itens": "locations", "offline": True},
        "lista": {
            "titulo": "{location}", "subtitulo": "{company} · {line}",
            "meta": ["{concluded} de {total} concluídos", "{percent}%"],
            "etiqueta": {"campo": "pending", "cores": {"0": "sucesso"}, "padrao": "aviso", "texto": "{pending} pendente(s)"},
            "busca": ["location", "line", "company"],
            "filtros": [{"rotulo": "Com pendência", "campo": "pending", "maior": 0}, {"rotulo": "Concluídas", "campo": "pending", "igual": 0}],
            "kpis": [{"rotulo": "LOCAIS"}, {"rotulo": "PENDENTES", "soma": "pending", "tom": "aviso"},
                     {"rotulo": "CONCLUÍDOS", "soma": "concluded", "tom": "sucesso"}],
            "ordem": [{"rotulo": "Local", "campo": "location"}, {"rotulo": "Pendências", "campo": "pending", "desc": True}],
        },
        "detalhe": {
            "secoes": [{"titulo": "Local", "campos": [["Empresa", "{company}"], ["Linha", "{line}"], ["Total", "{total}"],
                                                       ["Concluídos", "{concluded}"], ["Pendentes", "{pending}"]]}],
            "sublista": {"titulo": "Equipamentos", "itens": "validators", "titulo_item": "{label} · {model}",
                         "subtitulo_item": "{technician} {completed_at|data}", "etiqueta": {"campo": "status", "cores": ST_CONCL},
                         "fotos": {"lista": "photos", "url": "{url}"}, "form": "trocar"},
        },
        "forms": {
            "trocar": {
                "titulo": "Troca de chip", "offline": True,
                "envio": {"url": "/api/chip-swaps/{pai.id}/{base_asset_id}", "metodo": "POST", "formato": "multipart"},
                "campos": [
                    {"nome": "gps", "tipo": "gps", "lat": "latitude", "lon": "longitude", "prec": "gps_accuracy"},
                    {"nome": "test_result", "rotulo": "Resultado do teste após a troca", "tipo": "lista", "obrigatorio": True, "valor": "{test_result}",
                     "opcoes": [["TESTADO_OK", "Testado OK"], ["TESTADO_COM_DEFEITO", "Testado com defeito"],
                                ["NAO_FOI_POSSIVEL_TESTAR", "Não foi possível testar"], ["EQUIPAMENTO_INOPERANTE", "Equipamento inoperante"],
                                ["OUTRO", "Outro"]]},
                    {"nome": "test_notes", "rotulo": "Observação do teste (obrigatória se não for OK)", "tipo": "area", "valor": "{test_notes}"},
                    {"nome": "photos", "rotulo": "Fotos (com foto a troca fica CONCLUÍDA)", "tipo": "fotos", "max": 6},
                    {"nome": "notes", "rotulo": "Observação", "tipo": "area", "valor": "{notes}"},
                ],
            }
        },
    },
    {
        "key": "panoramica", "titulo": "Visão Panorâmica", "grupo": "field", "icone": "image",
        "perms": ["field.panorama"], "web": "/visao-panoramica", "modelo": "lista", "nativa": "panoramica",
        "fonte": {"url": "/api/panoramas", "itens": "locations", "offline": True},
        "lista": {
            "titulo": "{location}", "subtitulo": "{company} · {line}", "meta": ["{photo_count} foto(s)"],
            "etiqueta": {"campo": "status", "cores": ST_CONCL}, "busca": ["location", "line", "company"],
            "filtros": [{"rotulo": "Pendentes", "campo": "status", "igual": "PENDENTE"}, {"rotulo": "Concluídas", "campo": "status", "igual": "CONCLUÍDA"}],
            "kpis": [{"rotulo": "LOCAIS"}, {"rotulo": "PENDENTES", "campo": "status", "igual": "PENDENTE", "tom": "aviso"},
                     {"rotulo": "CONCLUÍDAS", "campo": "status", "igual": "CONCLUÍDA", "tom": "sucesso"}],
            "ordem": [{"rotulo": "Local", "campo": "location"}],
        },
        "detalhe": {
            "secoes": [{"titulo": "Local", "campos": [["Empresa", "{company}"], ["Linha", "{line}"], ["Fotos", "{photo_count}"]]}],
            "sublista": {"titulo": "Pontos", "itens": "points", "titulo_item": "{name}", "subtitulo_item": "{technician} · {notes}",
                         "etiqueta": {"campo": "status", "cores": ST_CONCL}, "fotos": {"lista": "photos", "url": "{thumb_url}"}},
        },
    },
    {
        "key": "treinamentos", "titulo": "Treinamentos", "grupo": "field", "icone": "task",
        "perms": ["field.training", "field.training.manage"], "web": "/field/treinamentos", "modelo": "lista",
        "fonte": {"url": "/api/field/treinamentos", "itens": "techs", "offline": True,
                  "juntar": {"campo": "treinos", "de": "records", "chave": "user_id", "com": "id",
                             "nomear": {"campo": "type_id", "de": "types", "chave": "id", "rotulo": "name"}}},
        "lista": {
            "titulo": "{name}", "subtitulo": "{company}", "meta": ["{job_title}", "{treinos.length} treinamento(s)"],
            "busca": ["name", "company", "job_title"],
            "kpis": [{"rotulo": "TÉCNICOS"}],
            "ordem": [{"rotulo": "Nome", "campo": "name"}, {"rotulo": "Empresa", "campo": "company"}],
        },
        "detalhe": {
            "secoes": [{"titulo": "Técnico", "campos": [["Empresa", "{company}"], ["Cargo", "{job_title}"]]}],
            "sublista": {"titulo": "Treinamentos realizados", "itens": "treinos", "titulo_item": "{type_id__rotulo}",
                         "subtitulo_item": "{date|data} · {trainer} {notes}"},
            "acoes": [{"rotulo": "Registrar treinamento", "form": "registrar", "principal": True, "perms": ["field.training.manage"]}],
        },
        "forms": {
            "registrar": {
                "titulo": "Registrar treinamento",
                "envio": {"url": "/api/field/treinamentos", "metodo": "POST", "formato": "json"},
                "campos": [
                    {"nome": "user_ids", "tipo": "oculto", "valor": "[{id}]", "json": True},
                    {"nome": "type_id", "rotulo": "Tipo", "tipo": "lista", "obrigatorio": True,
                     "opcoes_fonte": {"de": "types", "valor": "id", "rotulo": "name"}},
                    {"nome": "date", "rotulo": "Data", "tipo": "data", "obrigatorio": True},
                    {"nome": "trainer", "rotulo": "Aplicado por", "tipo": "texto"},
                    {"nome": "notes", "rotulo": "Observação", "tipo": "area"},
                ],
            }
        },
    },
    {
        "key": "estoque_field", "titulo": "Estoque Field", "grupo": "field", "icone": "list",
        "perms": ["field.bobbins", "field.stock_manage"], "web": "/field/estoque", "modelo": "lista", "nativa": "estoque",
        "fonte": {"url": "/api/field-stock/dashboard", "itens": "balances", "offline": True},
        "lista": {
            "titulo": "{item}", "subtitulo": "{point}", "meta": ["Bom: {good} {unit}", "Ruim: {bad}"],
            "busca": ["item", "point"], "kpis": [{"rotulo": "SALDOS"}, {"rotulo": "BONS", "soma": "good", "tom": "sucesso"},
                                                 {"rotulo": "RUINS", "soma": "bad", "tom": "perigo"}],
            "ordem": [{"rotulo": "Ponto", "campo": "point"}, {"rotulo": "Item", "campo": "item"}],
        },
        "detalhe": {"secoes": [{"titulo": "Saldo", "campos": [["Item", "{item}"], ["Ponto", "{point}"], ["Bons", "{good} {unit}"],
                                                             ["Ruins", "{bad} {unit}"], ["Atualizado", "{updated_at|datahora}"]]}]},
    },
    {
        "key": "evidencias", "titulo": "Evidências", "grupo": "field", "icone": "chart",
        "perms": ["field.evidence"], "web": "/evidencias-campo", "modelo": "painel",
        "fonte": {"url": "/api/evidencias-campo/resumo"},
        "painel": {"kpis": [{"rotulo": "VISITAS", "valor": "{visits}"}, {"rotulo": "ITENS", "valor": "{items}"},
                            {"rotulo": "MÍDIAS", "valor": "{media}"}, {"rotulo": "CASADOS", "valor": "{matched}", "tom": "sucesso"},
                            {"rotulo": "EM REVISÃO", "valor": "{review}", "tom": "aviso"},
                            {"rotulo": "VISITAS SEM VÍNCULO", "valor": "{unresolved_visits}", "tom": "perigo"}]},
    },
    # ------------------------------------------------------------- IMPLANTAÇÃO
    {
        "key": "chip_emv", "titulo": "Troca de Chips EMV – Trilhos", "grupo": "implantacao", "icone": "list",
        "perms": ["implantation.emv"], "web": "/troca-chips-emv", "modelo": "lista",
        "fonte": {"url": "/api/emv-chip-swaps/", "itens": "rows", "offline": True},
        "lista": {
            "titulo": "Terminal {terminal} · {station_name}", "subtitulo": "{company} · {line}",
            "meta": ["{technician}", "{completed_at|data}"], "etiqueta": {"campo": "status", "cores": ST_CONCL},
            "busca": ["terminal", "station", "station_name", "line", "technician"],
            "filtros": [{"rotulo": "Pendentes", "campo": "status", "igual": "PENDENTE"}, {"rotulo": "Concluídas", "campo": "status", "igual": "CONCLUÍDA"}],
            "kpis": [{"rotulo": "TOTAL"}, {"rotulo": "PENDENTES", "campo": "status", "igual": "PENDENTE", "tom": "aviso"},
                     {"rotulo": "CONCLUÍDAS", "campo": "status", "igual": "CONCLUÍDA", "tom": "sucesso"}],
            "ordem": [{"rotulo": "Estação", "campo": "station_name"}, {"rotulo": "Conclusão", "campo": "completed_at", "desc": True}],
        },
        "detalhe": {"secoes": [{"titulo": "Terminal", "campos": [["Terminal", "{terminal}"], ["Versão", "{version}"], ["Modelo", "{model}"],
                                                                ["Bloco", "{block_number}"], ["Linha", "{line}"], ["Estação", "{station_name} ({station})"]]},
                               {"titulo": "Execução", "campos": [["Técnico", "{technician}"], ["Concluída", "{completed_at|datahora}"],
                                                                 ["Teste", "{test_result}"]]}],
                    "acoes": [{"rotulo": "Registrar troca", "form": "trocar", "principal": True}]},
        "forms": {
            "trocar": {
                "titulo": "Troca de chip EMV", "offline": True,
                "envio": {"url": "/api/emv-chip-swaps/{terminal}", "metodo": "POST", "formato": "multipart"},
                "campos": [
                    {"nome": "gps", "tipo": "gps"},
                    {"nome": "test_result", "rotulo": "Resultado do teste", "tipo": "lista", "obrigatorio": True, "valor": "{test_result}", "opcoes": TESTE},
                    {"nome": "notes", "rotulo": "Observação (obrigatória se não for OK)", "tipo": "area"},
                    {"nome": "photos", "rotulo": "Fotos (com foto fica CONCLUÍDA)", "tipo": "fotos", "max": 6},
                ],
            }
        },
    },
    {
        "key": "chip_garagem", "titulo": "Troca de Chips Garagem", "grupo": "implantacao", "icone": "list",
        "perms": ["implantation.garage"], "web": "/troca-chips-garagem", "modelo": "lista",
        "fonte": {"url": "/api/garage-chip-swaps", "itens": "rows", "offline": True},
        "lista": {
            "titulo": "Terminal {terminal} · {model}", "subtitulo": "{company}", "meta": ["{technician}", "{photo_count} foto(s)"],
            "etiqueta": {"campo": "status", "cores": ST_CONCL}, "busca": ["terminal", "company", "model", "technician"],
            "filtros": [{"rotulo": "Pendentes", "campo": "status", "igual": "PENDENTE"}, {"rotulo": "Concluídas", "campo": "status", "igual": "CONCLUÍDA"}],
            "kpis": [{"rotulo": "TOTAL"}, {"rotulo": "PENDENTES", "campo": "status", "igual": "PENDENTE", "tom": "aviso"},
                     {"rotulo": "CONCLUÍDAS", "campo": "status", "igual": "CONCLUÍDA", "tom": "sucesso"}],
            "ordem": [{"rotulo": "Empresa", "campo": "company"}, {"rotulo": "Terminal", "campo": "terminal"}],
        },
        "detalhe": {"secoes": [{"titulo": "Terminal", "campos": [["Terminal", "{terminal}"], ["Modelo", "{model}"], ["Empresa", "{company}"],
                                                                ["Técnico", "{technician}"], ["Teste", "{test_result}"], ["Observação", "{notes}"]]}],
                    "fotos": {"lista": "photos", "url": "{url}"},
                    "acoes": [{"rotulo": "Registrar troca", "form": "trocar", "principal": True}]},
        "forms": {
            "trocar": {
                "titulo": "Troca de chip – garagem", "offline": True,
                "envio": {"url": "/api/garage-chip-swaps/{id}", "metodo": "POST", "formato": "multipart"},
                "campos": [
                    {"nome": "test_result", "rotulo": "Resultado", "tipo": "lista", "obrigatorio": True, "valor": "{test_result}", "opcoes": TESTE},
                    {"nome": "notes", "rotulo": "Observação (obrigatória se não for OK)", "tipo": "area", "valor": "{notes}"},
                    {"nome": "photos", "rotulo": "Fotos", "tipo": "fotos", "max": 6},
                ],
            }
        },
    },
    {
        "key": "qr_trilhos", "titulo": "QR Code – Trilhos", "grupo": "implantacao", "icone": "list",
        "perms": ["implantation.qr.view", "implantation.qr.manage"], "web": "/qr-trilhos", "modelo": "lista",
        "fonte": {"url": "/api/implantacao/qr-trilhos/configs", "itens": "rows", "offline": True},
        "lista": {
            "titulo": "Terminal {TerminalId} · {station}", "subtitulo": "{company} · {line} · bloco {block}",
            "meta": ["IP {Ip}", "{installation}"], "busca": ["TerminalId", "station", "line", "Ip", "block"],
            "kpis": [{"rotulo": "TERMINAIS"}], "ordem": [{"rotulo": "Estação", "campo": "station"}, {"rotulo": "Terminal", "campo": "TerminalId"}],
        },
        "detalhe": {"secoes": [{"titulo": "Rede", "campos": [["IP", "{Ip}"], ["Máscara", "{Mask}"], ["Gateway", "{Gateway}"],
                                                            ["DNS 1", "{Dns1}"], ["DNS 2", "{Dns2}"]]},
                               {"titulo": "Terminal", "campos": [["Terminal", "{TerminalId}"], ["Linha (id)", "{LineId}"], ["Grupo", "{TermGrpId}"],
                                                                 ["Operadora", "{TransOperId}"], ["Instalação", "{installation}"]]}]},
    },
    {
        "key": "drive_tecnico", "titulo": "Drive Técnico", "grupo": "implantacao", "icone": "folder",
        "perms": ["implantation.repository.view"], "web": "/implantacao-hardware/repositorio", "modelo": "lista",
        "fonte": {"url": "/api/implantacao/repositorio", "itens": "files",
                  "juntar": {"campo": "pasta", "de": "folders", "chave": "id", "com": "folder_id", "um": True}},
        "lista": {"titulo": "{name}", "subtitulo": "{pasta.name}", "meta": ["{size|mb}", "versão {version}", "{created_at|data}"],
                  "busca": ["name", "pasta.name"], "kpis": [{"rotulo": "ARQUIVOS"}], "ordem": [{"rotulo": "Nome", "campo": "name"},
                                                                                          {"rotulo": "Mais novos", "campo": "created_at", "desc": True}]},
        "detalhe": {"secoes": [{"titulo": "Arquivo", "campos": [["Nome", "{name}"], ["Pasta", "{pasta.name}"], ["Tamanho", "{size|mb}"],
                                                               ["Versão", "{version}"], ["Enviado", "{created_at|datahora}"]]}],
                    "acoes": [{"rotulo": "Baixar", "baixar": "/api/implantacao/repositorio/arquivos/{id}/download", "principal": True}]},
    },
    {
        "key": "lista_presenca", "titulo": "Lista de Presença Digital", "grupo": "implantacao", "icone": "task",
        "perms": ["implantation.attendance.view"], "web": "/implantacao-hardware/lista-presenca", "modelo": "lista",
        "fonte": {"url": "/api/implantacao/listas-presenca", "itens": "rows"},
        "lista": {"titulo": "{title}", "subtitulo": "{location} · {instructor}", "meta": ["{activity_date|data}", "{start_time}"],
                  "etiqueta": {"campo": "status", "cores": ST_CONCL}, "busca": ["title", "location", "instructor"],
                  "kpis": [{"rotulo": "LISTAS"}, {"rotulo": "RASCUNHOS", "campo": "status", "igual": "RASCUNHO", "tom": "aviso"}],
                  "ordem": [{"rotulo": "Data", "campo": "activity_date", "desc": True}]},
        "detalhe": {"secoes": [{"titulo": "Lista", "campos": [["Título", "{title}"], ["Data", "{activity_date|data}"], ["Início", "{start_time}"],
                                                             ["Duração", "{duration}"], ["Local", "{location}"], ["Instrutor", "{instructor}"],
                                                             ["Descrição", "{description}"], ["Observações", "{observations}"]]}]},
    },
]
