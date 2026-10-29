"""Reconciliação do BU em CSV consolidado (Dados Abertos) do 2º turno de 2026 com as fontes anteriores.

Fontes (todas locais, já baixadas e com hash conferido):
  CONSOLIDADO  BU em CSV do 2º turno (bweb_2t_*.zip, SHA-512 oficial conferido) → secoes_bu_2026.parquet (turno 2)
               e dados/processados/bweb/presidente_2026_2t_*.parquet (campos de urna, abertura, encerramento)
  ANTERIOR     resultado oficial por seção (Detalhe + Votação por seção) usado antes → historico/.../secoes_oficiais_2026_2t.parquet
  PORTAL       BU binário e log coletados seção a seção no Portal de Resultados (hash publicado = SHA-256 do vota.vsc)

Saídas em resultados/2026/consolidado_2t/. Nenhum arquivo anterior é sobrescrito.
"""
from __future__ import annotations

import duckdb
import pandas as pd

from .config import MANIFESTOS, PROCESSADOS, RESULTADOS

SAIDA = RESULTADOS / "2026" / "consolidado_2t"
ANTERIOR = PROCESSADOS / "historico" / "antes_consolidado_2026-10-29" / "secoes_oficiais_2026_2t.parquet"
CAMPOS = [("qt_aptos", "aptos"), ("qt_comparecimento", "comparecimento"), ("qt_abstencoes", "abstencoes"),
          ("votos_nominais", "validos"), ("votos_brancos", "brancos"), ("votos_nulos", "nulos")]


def inventario() -> pd.DataFrame:
    inv = pd.read_csv(MANIFESTOS / "inventario_fontes.csv", dtype=str)
    dl = pd.read_csv(MANIFESTOS / "downloads.csv", dtype=str).drop_duplicates("url", keep="last")
    sel = inv[(inv.ano == "2026") & (inv.tipo.isin(["bu_csv", "arquivos_urna", "detalhe_votacao_secao", "votacao_secao",
                                                     "detalhe_votacao_munzona", "votacao_candidato_munzona",
                                                     "relatorio_totalizacao"]))]
    d = sel.merge(dl[["url", "sha256", "sha512", "sha512_oficial", "hash_oficial_confere", "baixado_em", "etag"]],
                  on="url", how="left", suffixes=("", "_baixado"))
    d["versao_local_igual_a_atual"] = d.etag_baixado == d.etag
    cols = ["tipo", "uf", "turno", "nome", "url", "ckan_created", "consultado_em", "http_status", "tamanho_bytes", "etag",
            "last_modified", "hash_publicado_url", "sha512_oficial", "sha512", "hash_oficial_confere", "sha256",
            "baixado_em", "etag_baixado", "versao_local_igual_a_atual"]
    d = d[cols].sort_values(["tipo", "turno", "uf"])
    d.to_csv(SAIDA / "inventario_arquivos_oficiais_2026.csv", index=False)
    return d


def comparar(con) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Comparação direta, seção a seção, de cada fonte com o BU em CSV consolidado."""
    con.execute(f"CREATE OR REPLACE VIEW cons AS SELECT * FROM '{PROCESSADOS}/secoes_bu_2026.parquet' WHERE turno = 2")
    con.execute(f"CREATE OR REPLACE VIEW ant AS SELECT * FROM '{ANTERIOR}'")
    con.execute(f"""CREATE OR REPLACE VIEW bin AS SELECT uf, cd_municipio, nr_zona, nr_secao, bu_qtd_aptos qt_aptos,
        bu_qtd_comparecimento qt_comparecimento, bu_qtd_aptos - bu_qtd_comparecimento qt_abstencoes,
        bu_votos_nominais votos_nominais, bu_votos_brancos votos_brancos, bu_votos_nulos votos_nulos,
        map_from_entries(list_transform(bu_votos_candidato, lambda e: struct_pack(k := e.k, v := e.v))) votos_candidato
      FROM (SELECT regexp_extract(filename, '_([A-Z]{{2}})\\.parquet', 1) uf,
                   CAST(regexp_extract(arquivo, '^o\\d{{5}}(?:-|[a-z]{{2}})(\\d{{5}})(\\d{{4}})(\\d{{4}})', 1) AS INT) cd_municipio,
                   CAST(regexp_extract(arquivo, '^o\\d{{5}}(?:-|[a-z]{{2}})(\\d{{5}})(\\d{{4}})(\\d{{4}})', 2) AS INT) nr_zona,
                   CAST(regexp_extract(arquivo, '^o\\d{{5}}(?:-|[a-z]{{2}})(\\d{{5}})(\\d{{4}})(\\d{{4}})', 3) AS INT) nr_secao, *
            FROM read_parquet('{PROCESSADOS}/bu/2026_2t_*.parquet', union_by_name=true, filename=true))""")
    linhas, resumo = [], []
    for nome, v in (("resultado oficial por seção (DSEC+VSEC) usado antes", "ant"),
                    ("BU binário coletado no Portal de Resultados", "bin")):
        pres = con.execute(f"""SELECT count(*) FILTER (c.nr_secao IS NOT NULL AND o.nr_secao IS NOT NULL),
            count(*) FILTER (o.nr_secao IS NULL), count(*) FILTER (c.nr_secao IS NULL)
          FROM cons c FULL JOIN {v} o USING (uf, cd_municipio, nr_zona, nr_secao)""").fetchall()[0]
        ausentes = con.execute(f"""SELECT coalesce(c.uf, o.uf) uf, coalesce(c.cd_municipio, o.cd_municipio) cd_municipio,
            coalesce(c.nr_zona, o.nr_zona) nr_zona, coalesce(c.nr_secao, o.nr_secao) nr_secao, 'presenca' campo,
            CASE WHEN o.nr_secao IS NULL THEN NULL ELSE 1 END valor_fonte_anterior,
            CASE WHEN c.nr_secao IS NULL THEN NULL ELSE 1 END valor_consolidado
          FROM cons c FULL JOIN {v} o USING (uf, cd_municipio, nr_zona, nr_secao)
          WHERE c.nr_secao IS NULL OR o.nr_secao IS NULL""").df()
        ausentes["fonte_anterior"] = nome
        linhas.append(ausentes)
        for col, rot in CAMPOS + [("v13", "votos_13"), ("v22", "votos_22"), ("cand", "votos_por_candidato_soma_dif_abs")]:
            if col == "v13":
                ea, eb = "coalesce(o.votos_candidato[13], 0)", "coalesce(c.votos_candidato[13], 0)"
            elif col == "v22":
                ea, eb = "coalesce(o.votos_candidato[22], 0)", "coalesce(c.votos_candidato[22], 0)"
            elif col == "cand":
                ea = """coalesce(list_sum(list_transform(list_distinct(map_keys(c.votos_candidato) || coalesce(map_keys(o.votos_candidato), [])),
                         lambda k: abs(coalesce(c.votos_candidato[k], 0) - coalesce(o.votos_candidato[k], 0)))), 0)"""
                eb = "0"
            else:
                ea, eb = f"o.{col}", f"c.{col}"
            d = con.execute(f"""SELECT c.uf, c.cd_municipio, c.nr_zona, c.nr_secao, '{rot}' campo,
                CAST({ea} AS BIGINT) valor_fonte_anterior, CAST({eb} AS BIGINT) valor_consolidado
              FROM cons c JOIN {v} o USING (uf, cd_municipio, nr_zona, nr_secao)
              WHERE CAST({ea} AS BIGINT) IS DISTINCT FROM CAST({eb} AS BIGINT)""").df()
            d["fonte_anterior"] = nome
            linhas.append(d)
            resumo.append({"comparacao": f"BU em CSV consolidado × {nome}", "campo": rot, "secoes_em_ambas": pres[0],
                           "so_no_consolidado": pres[1], "so_na_fonte_anterior": pres[2], "divergencias": len(d),
                           "soma_abs_diferencas": int((d.valor_fonte_anterior - d.valor_consolidado).abs().sum()) if len(d) else 0})
    return pd.concat(linhas, ignore_index=True), pd.DataFrame(resumo)


def bu_x_log(con) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Campos que só o BU em CSV traz (abertura, encerramento, urna efetivada) × registros do log."""
    con.execute(f"""CREATE OR REPLACE TABLE bux AS SELECT SG_UF uf, CAST(CD_MUNICIPIO AS INT) cd_municipio,
        CAST(NR_ZONA AS INT) nr_zona, CAST(NR_SECAO AS INT) nr_secao, any_value(DT_ABERTURA) dt_abertura,
        any_value(DT_ENCERRAMENTO) dt_encerramento, any_value(NR_URNA_EFETIVADA) urna_efetivada,
        any_value(DS_TIPO_URNA) tipo_urna, any_value(DT_BU_RECEBIDO) dt_bu_recebido
      FROM read_parquet('{PROCESSADOS}/bweb/presidente_2026_2t_*.parquet', union_by_name=true) GROUP BY ALL""")
    con.execute(f"""CREATE OR REPLACE TABLE jl AS SELECT b.*, l.log_ids_urna, l.t_pronta_primeiro, l.t_encerramento_confirmado_primeiro,
        epoch(strptime(dt_abertura, '%Y-%m-%d %H:%M:%S')::TIME)::BIGINT ab_s,
        epoch(strptime(dt_encerramento, '%Y-%m-%d %H:%M:%S')::TIME)::BIGINT enc_s
      FROM bux b JOIN read_parquet('{PROCESSADOS}/logs/2026_2t_*.parquet', union_by_name=true) l
        USING (uf, cd_municipio, nr_zona, nr_secao) WHERE l.tem_log""")
    testes = [("E1", "abertura no BU × primeira 'Urna pronta para receber votos' no log", "ab_s", "t_pronta_primeiro"),
              ("E2", "encerramento no BU × 'Procedimento de encerramento confirmado' no log", "enc_s",
               "t_encerramento_confirmado_primeiro")]
    res, lst = [], []
    total = con.execute("SELECT count(*) FROM jl").fetchone()[0]
    for cod, desc, a, b in testes:
        r = con.execute(f"""SELECT count(*) FILTER (abs({a} - {b}) <= 2), count(*) FILTER (abs({a} - {b}) <= 60),
            count(*) FILTER (abs({a} - {b}) > 60), count(*) FILTER ({b} IS NULL) FROM jl""").fetchone()
        res.append({"teste": cod, "descricao": desc, "secoes": total, "ate_2s": r[0], "ate_60s": r[1],
                    "diferenca_maior_60s": r[2], "sem_registro_no_log": r[3]})
        d = con.execute(f"""SELECT uf, cd_municipio, nr_zona, nr_secao, '{cod}' teste,
            strftime(to_timestamp({a}) AT TIME ZONE 'UTC', '%H:%M:%S') valor_bu,
            CASE WHEN {b} IS NULL THEN NULL ELSE strftime(to_timestamp({b}) AT TIME ZONE 'UTC', '%H:%M:%S') END valor_log,
            {a} - {b} diferenca_s, log_ids_urna, urna_efetivada
          FROM jl WHERE abs({a} - {b}) > 60 OR {b} IS NULL""").df()
        lst.append(d)
    r = con.execute("""SELECT count(*) FILTER (contains(log_ids_urna, lpad(urna_efetivada, 8, '0'))) FROM jl""").fetchone()[0]
    res.append({"teste": "E3", "descricao": "urna efetivada no BU presente entre os identificadores de urna do log",
                "secoes": total, "ate_2s": None, "ate_60s": None, "diferenca_maior_60s": total - r, "sem_registro_no_log": None})
    d = con.execute("""SELECT uf, cd_municipio, nr_zona, nr_secao, 'E3' teste, urna_efetivada valor_bu, log_ids_urna valor_log,
        NULL diferenca_s, log_ids_urna, urna_efetivada FROM jl WHERE NOT contains(coalesce(log_ids_urna, ''), lpad(urna_efetivada, 8, '0'))""").df()
    lst.append(d)
    lst = pd.concat(lst, ignore_index=True)
    tipo = con.execute(f"""SELECT regexp_extract(filename, '_([A-Z]{{2}})\\.parquet', 1) uf, CAST(bu_municipio AS INT) cd_municipio,
        CAST(bu_zona AS INT) nr_zona, CAST(bu_secao AS INT) nr_secao, bu_tipo_urna
      FROM read_parquet('{PROCESSADOS}/bu/2026_2t_*.parquet', union_by_name=true, filename=true)""").df()
    lst = lst.merge(tipo, on=["uf", "cd_municipio", "nr_zona", "nr_secao"], how="left")

    def classificar(r):
        if r.bu_tipo_urna == "reservaSecao" and r.teste == "E1":
            return ("Diferença explicada", "Urna substituída por reserva (bu_tipo_urna = reservaSecao no BU assinado): a "
                    "abertura do BU é a da seção; o log publicado é o da urna de reserva, que começou depois.")
        if r.bu_tipo_urna == "reservaEncerrandoSecao":
            return ("Diferença explicada", "Seção encerrada por urna de reserva (bu_tipo_urna = reservaEncerrandoSecao): a "
                    "urna efetivada é a de reserva; o log publicado é o da urna original, copiado para a mídia externa "
                    "(arquivo …ME.jez), sem o registro de encerramento.")
        return ("Incompatibilidade documental pendente", "Sem substituição de urna registrada no BU; exige ata da mesa.")
    if len(lst):
        lst[["classificacao", "explicacao"]] = lst.apply(lambda r: pd.Series(classificar(r)), axis=1)
    contagem = tipo.bu_tipo_urna.value_counts().rename_axis("bu_tipo_urna").reset_index(name="secoes")
    contagem.to_csv(SAIDA / "tipos_de_urna_bu_binario_2t.csv", index=False)
    return pd.DataFrame(res), lst


def executar() -> dict:
    SAIDA.mkdir(parents=True, exist_ok=True)
    inv = inventario()
    con = duckdb.connect()
    con.execute("SET memory_limit='6GB'")
    diverg, resumo = comparar(con)
    e_res, e_lst = bu_x_log(con)
    con.close()
    diverg.to_csv(SAIDA / "divergencias_bu_csv_x_fontes_anteriores.csv", index=False)
    resumo.to_csv(SAIDA / "resumo_bu_csv_x_fontes_anteriores.csv", index=False)
    e_res.to_csv(SAIDA / "resumo_bu_csv_x_log_horarios_urna.csv", index=False)
    e_lst.to_csv(SAIDA / "divergencias_bu_csv_x_log_horarios_urna.csv", index=False)
    # divergências da reconciliação geral (testes A–K), só 2º turno, com explicação
    inc = pd.read_csv(RESULTADOS / "2026" / "incompatibilidades.csv", low_memory=False)
    inc = inc[inc.turno == 2]
    inc.to_csv(SAIDA / "divergencias_reconciliacao_2t.csv", index=False)
    return {"inventario": inv, "divergencias": diverg, "resumo": resumo, "e_resumo": e_res, "e_lista": e_lst,
            "reconciliacao_2t": inc}


def afirmacoes_externas() -> pd.DataFrame:
    """Confronto das afirmações de terceiros com cálculos próprios refeitos a partir dos dados oficiais.
    Classificação: Confirmada pelos dados | Contrariada pelos dados | Dependente de metodologia ou definição |
    Não verificável com as fontes disponíveis."""
    from .fusos import sql_desloc_brt
    con = duckdb.connect()
    P = PROCESSADOS
    logs = f"read_parquet('{P}/logs/2026_2t_*.parquet', union_by_name=true)"
    d = sql_desloc_brt()
    v = con.execute(f"""SELECT count(*),
        sum(len(list_filter(votos_s, lambda x: x + {d} >= 61200))),
        sum(len(list_filter(votos_s, lambda x: x + {d} > 61200))),
        sum(len(list_filter(votos_s, lambda x: x + {d} >= 61200 AND x + {d} < 61500))),
        sum(len(list_filter(votos_s, lambda x: x + {d} > 64800))),
        sum(len(list_filter(votos_s, lambda x: x + {d} > 68400))),
        count(*) FILTER (len(list_filter(votos_s, lambda x: x + {d} >= 61200)) = 0)
      FROM {logs} WHERE tem_log AND uf <> 'ZZ'""").fetchall()[0]
    conc = {}
    for a, t in ((2022, 1), (2022, 2), (2026, 1), (2026, 2)):
        conc[(a, t)] = con.execute(f"""SELECT count(*) FILTER (votos_nominais > 0 AND list_max(map_values(votos_candidato)) > 0.9 * votos_nominais),
            count(*) FILTER (votos_nominais > 0 AND list_max(map_values(votos_candidato)) = votos_nominais)
          FROM '{P}/secoes_bu_{a}.parquet' WHERE turno = {t}""").fetchall()[0]
    con.close()
    ext = pd.read_csv(RESULTADOS / "2026" / "estudos_externos_2t.csv")
    nosso = dict(zip(ext.verificacao + "|" + ext.fonte_externa, ext.nossa_extracao))
    g = pd.read_csv(RESULTADOS / "2026" / "horario_grupos_uf.csv")
    sp = g[(g.uf == "SP") & (g.grupo == "D")].iloc[0]
    C, R, D, N = ("Confirmada pelos dados", "Contrariada pelos dados", "Dependente de metodologia ou definição",
                  "Não verificável com as fontes disponíveis")
    L = [
        ("CNN/setup.news", "497.895 urnas analisadas (sem exterior)", 497895, v[0], D,
         "nossa base tem 497.896 seções com log; diferença de 1 seção de universo"),
        ("CNN/setup.news", "34.330 votos após as 17h", 34330, v[1], C, "reproduzido contando a partir de 17:00:00 (≥); após 17:00:00 (>) são 34.050"),
        ("CNN/setup.news", "29.001 votos nos primeiros 5 minutos após 17h", 29001, v[3], C, "17:00:00 a 17:04:59"),
        ("CNN/setup.news", "1.993 votos após 18h", 1993, v[4], C, ""),
        ("CNN/setup.news", "11 votos após 19h", 11, v[5], C, ""),
        ("CNN/setup.news", "468.043 urnas sem voto após 17h", 468043, v[6], C, "diferença de 1 = universo de seções"),
        ("André Agnoletto", "497.896 urnas com log (sem exterior)", 497896, v[0], C, ""),
        ("André Agnoletto", "31.060 votos após o encerramento previsto", 31060,
         nosso.get("Votos após o encerramento previsto (17h Brasília)|Agnoletto"), D,
         "ele usa o horário local previsto; 17h de Brasília dá 34.050 e 17h da hora local, 30.979"),
        ("André Agnoletto", "2.512 votos com habilitação manual após o encerramento", 2512,
         nosso.get("Votos manuais após 17h (seções com modalidade alinhada)|Agnoletto"), D, "definição de horário diferente"),
        ("André Agnoletto", "7.577 urnas encerradas às 19h", 7577,
         nosso.get("Seções com início de encerramento a partir de 18h55|Agnoletto"), D,
         "início do encerramento a partir de 18h55; após 19h00:00 são 6.766 (grupo D)"),
        ("André Agnoletto", "mediana de 10 s por voto", 10, nosso.get("Mediana da duração do voto (s)|Agnoletto"), D,
         "medimos habilitação → voto computado"),
        ("André Agnoletto", "habilitação manual após falha: UE2013 11,0% / UE2015 9,8% / UE2020 6,2% / UE2022 6,2%", None,
         "10,8 / 9,6 / 6,0 / 6,0", C, "diferenças de até 0,2 p.p. por regra de classificação das mensagens do log"),
        ("Painel auditoriaeleicoes.com", "2026, 1º turno: 3.806 seções com mais de 90% para um candidato", 3806,
         conc[(2026, 1)][0], D, "o painel declara universo de 499.038 seções (210 a menos que o oficial)"),
        ("Painel auditoriaeleicoes.com", "2026, 1º turno: 34 seções com 100%", 34, conc[(2026, 1)][1], D, "mesmo motivo"),
        ("Painel auditoriaeleicoes.com", "2022: 5.947 (1º) e 9.606 (2º) seções com mais de 90%", "5947 / 9606",
         f"{conc[(2022, 1)][0]} / {conc[(2022, 2)][0]}", D, "mesmo motivo"),
        ("Painel auditoriaeleicoes.com", "2022: 55 (1º) e 132 (2º) seções com 100%", "55 / 132",
         f"{conc[(2022, 1)][1]} / {conc[(2022, 2)][1]}", D, "mesmo motivo"),
        ("Painel auditoriaeleicoes.com", "2026, 1º turno: soma dos BUs difere do oficial em MG e no exterior", "MG −233/−242; ZZ −391/−310",
         "BU em CSV = oficial em todas as UFs", D,
         "o painel soma só seções com arquivo de urna; faltam 2 em MG (RED e Sistema de Apuração) e 70 no exterior"),
        ("Observatório (destaque anterior do painel)", "SP, encerramento após 19h: 13 com 57,12% dos válidos em 1.676 seções",
         "57,12% / 1.676", f"{sp.pct_validos_13:.2f}% / {int(sp.secoes)}", C,
         "diferença bruta; no mesmo local de votação o efeito ajustado é ~0"),
        ("kakaroto.dev", "afirmações sobre arquivos e totalização do 2º turno", None, None, N,
         "site fora do ar desde 26/10/2026 e sem código público"),
        ("Relatório externo com recortes 17h01–17h15 / 17h16–18h59", "valores por recorte de horário", None, None, N,
         "os valores não foram fornecidos ao Observatório; nossos recortes estão em resultados/2026/horario_recortes_votos.csv"),
        ("Afirmações gerais de inconsistência na totalização do 2º turno", "BU ≠ resultado oficial", None,
         "0 divergências em 499.205 seções", R,
         "BU em CSV consolidado, BU binário assinado e tabelas oficiais coincidem em todos os campos de votos"),
        ("2026, 2º turno (cálculo próprio, sem afirmação externa)", "seções com mais de 90% / com 100%", None,
         f"{conc[(2026, 2)][0]} / {conc[(2026, 2)][1]}", "Referência", "mesma definição aplicada a todos os anos"),
    ]
    df = pd.DataFrame(L, columns=["fonte", "afirmacao", "valor_alegado", "valor_reproduzido", "classificacao", "nota"])
    df.to_csv(SAIDA / "afirmacoes_externas_confronto.csv", index=False)
    return df
