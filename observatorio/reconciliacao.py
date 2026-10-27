"""Testes B, C e K — reconciliação entre fontes oficiais, seção a seção.

Fontes comparadas (todas do TSE):
  BWEB  = Boletim de Urna publicado em CSV (bweb)             -> secoes_bu_{ano}.parquet
  BUBIN = arquivo .bu binário transmitido pela urna (ASN.1)    -> processados/bu/*.parquet
  LOG   = log da urna (.logjez)                                -> processados/logs/*.parquet
  DSEC  = "Detalhe da apuração por seção eleitoral"            -> tabelas/detalhe_secao_{ano}
  VSEC  = "Votação por seção eleitoral" (por UF)               -> tabelas/votacao_secao/
  CMZ   = "Votação nominal por município e zona"               -> tabelas/candidato_munzona_{ano}
  DMZ   = "Detalhe da apuração por município e zona"           -> tabelas/detalhe_munzona_{ano}

Cada divergência é gravada individualmente (nenhuma é descartada) em
resultados/{ano}/incompatibilidades.csv; o resumo por teste vai para
resultados/{ano}/reconciliacao_resumo.csv. Valor ausente em uma das fontes é
registrado como "ausente", nunca tratado como zero.
"""
from __future__ import annotations

from pathlib import Path

import duckdb

from .config import logs_concluidos, PROCESSADOS, RESULTADOS

T = PROCESSADOS / "tabelas"


def _existe(padrao: str) -> bool:
    """Há Parquets de pacotes CONCLUÍDOS (registrados na cobertura) para o padrão?"""
    from .config import logs_concluidos
    pasta = "bu" if "/bu/" in padrao else "logs"
    ano = int(padrao.rsplit("/", 1)[-1][:4])
    try:
        logs_concluidos(ano, pasta)
        return True
    except FileNotFoundError:
        return False


def preparar(con: duckdb.DuckDBPyConnection, ano: int) -> list[str]:
    """Cria as views normalizadas (chave: turno, uf, cd_municipio, nr_zona, nr_secao)."""
    disponiveis = []
    con.execute(f"CREATE OR REPLACE VIEW bweb AS SELECT * FROM '{PROCESSADOS}/secoes_bu_{ano}.parquet'")
    disponiveis.append("bweb")
    if _existe(f"{PROCESSADOS}/bu/{ano}_*.parquet"):
        con.execute(f"""CREATE OR REPLACE VIEW bubin AS
          SELECT CAST(regexp_extract(filename, '_(\\d)t_', 1) AS INT) turno,
                 regexp_extract(filename, '_([A-Z]{{2}})\\.parquet', 1) uf,
                 CAST(regexp_extract(arquivo, '^o\\d{{5}}(?:-|[a-z]{{2}})(\\d{{5}})(\\d{{4}})(\\d{{4}})', 1) AS INT) cd_municipio,
                 CAST(regexp_extract(arquivo, '^o\\d{{5}}(?:-|[a-z]{{2}})(\\d{{5}})(\\d{{4}})(\\d{{4}})', 2) AS INT) nr_zona,
                 CAST(regexp_extract(arquivo, '^o\\d{{5}}(?:-|[a-z]{{2}})(\\d{{5}})(\\d{{4}})(\\d{{4}})', 3) AS INT) nr_secao, *
          FROM read_parquet({logs_concluidos(ano, 'bu')}, union_by_name=true, filename=true)""")
        disponiveis.append("bubin")
    if _existe(f"{PROCESSADOS}/logs/{ano}_*.parquet"):
        con.execute(f"""CREATE OR REPLACE VIEW logs AS
          SELECT * EXCLUDE (votos_s, hab_s, hab_mod, dur_voto, dur_voto_mod),
                 len(list_filter(dur_voto_mod, lambda x: x = 3)) man_votou,
                 len(list_filter(dur_voto_mod, lambda x: x = 1)) bio_votou,
                 len(list_filter(dur_voto_mod, lambda x: x = 2)) sembio_votou,
                 len(list_filter(dur_voto_mod, lambda x: x = 0)) semetapa_votou
          FROM read_parquet({logs_concluidos(ano)}, union_by_name=true)""")
        disponiveis.append("logs")
    if (T / f"detalhe_secao_{ano}.parquet").exists():
        con.execute(f"""CREATE OR REPLACE VIEW dsec AS SELECT
            CAST(NR_TURNO AS INT) turno, SG_UF uf, CAST(CD_MUNICIPIO AS INT) cd_municipio,
            CAST(NR_ZONA AS INT) nr_zona, CAST(NR_SECAO AS INT) nr_secao,
            TRY_CAST(QT_APTOS AS INT) qt_aptos, TRY_CAST(QT_COMPARECIMENTO AS INT) qt_comparecimento,
            TRY_CAST(QT_ABSTENCOES AS INT) qt_abstencoes, TRY_CAST(QT_VOTOS_NOMINAIS AS INT) votos_nominais,
            TRY_CAST(QT_VOTOS_BRANCOS AS INT) votos_brancos, TRY_CAST(QT_VOTOS_NULOS AS INT) votos_nulos,
            TRY_CAST(QT_VOTOS_LEGENDA AS INT) votos_legenda,
            TRY_CAST(QT_VOTOS_ANULADOS_APU_SEP AS INT) votos_anulados_apu_sep,
            ST_SECAO_INSTALADA, ST_SECAO_ANULADA, DS_MODELO_URNA, DS_ORIGEM_VOTO
          FROM '{T}/detalhe_secao_{ano}.parquet'""")
        disponiveis.append("dsec")
    if list((T / "votacao_secao").glob(f"{ano}_*.parquet")):
        con.execute(f"""CREATE OR REPLACE VIEW vsec AS SELECT
            CAST(NR_TURNO AS INT) turno, SG_UF uf, CAST(CD_MUNICIPIO AS INT) cd_municipio,
            CAST(NR_ZONA AS INT) nr_zona, CAST(NR_SECAO AS INT) nr_secao,
            CAST(NR_VOTAVEL AS INT) nr_votavel, sum(CAST(QT_VOTOS AS INT)) qt_votos
          FROM read_parquet('{T}/votacao_secao/{ano}_*.parquet', union_by_name=true) GROUP BY ALL""")
        disponiveis.append("vsec")
    for nome, arq in (("cmz", f"candidato_munzona_{ano}"), ("dmz", f"detalhe_munzona_{ano}")):
        if (T / f"{arq}.parquet").exists():
            con.execute(f"CREATE OR REPLACE VIEW {nome}_raw AS SELECT * FROM '{T}/{arq}.parquet'")
            disponiveis.append(nome)
    return disponiveis


CHAVE = "turno, uf, cd_municipio, nr_zona, nr_secao"


def _diff(con, teste: str, descricao: str, fonte_a: str, fonte_b: str, sql_join: str,
          campos: list[tuple[str, str, str]]) -> None:
    """Insere divergências campo a campo. `campos` = [(nome, expr_a, expr_b)]."""
    partes = []
    for nome, ea, eb in campos:
        partes.append(f"""SELECT '{teste}' teste, turno, uf, cd_municipio, nr_zona, nr_secao,
            '{nome}' campo, CAST({ea} AS BIGINT) valor_a, CAST({eb} AS BIGINT) valor_b
            FROM j""")
    con.execute(f"CREATE OR REPLACE TEMP VIEW j AS {sql_join}")
    total = con.execute("SELECT count(*) FROM j").fetchone()[0]
    uniao = " UNION ALL ".join(partes)
    con.execute(f"""INSERT INTO incompat SELECT teste, turno, uf, cd_municipio, nr_zona, nr_secao, campo,
            valor_a, '{fonte_a}', valor_b, '{fonte_b}', valor_a - valor_b,
            CASE WHEN valor_a IS NULL OR valor_b IS NULL THEN 'ausente' ELSE 'diferente' END,
            'Incompatibilidade documental', ''
        FROM ({uniao}) WHERE valor_a IS DISTINCT FROM valor_b""")
    for nome, _, _ in campos:
        r = con.execute(f"""SELECT count(*) FILTER (WHERE campo='{nome}'),
                count(*) FILTER (WHERE campo='{nome}' AND situacao='ausente'),
                coalesce(sum(abs(diferenca)) FILTER (WHERE campo='{nome}'), 0)
            FROM incompat WHERE teste='{teste}'""").fetchone()
        con.execute("INSERT INTO resumo VALUES (?,?,?,?,?,?,?,?,?)",
                    [teste, descricao, nome, fonte_a, fonte_b, total, r[0], r[1], int(r[2])])


def explicar(con, disp) -> None:
    """Aplica explicações documentais verificáveis. Só reclassifica para
    'Diferença explicada' quando a regra e a fonte da explicação são objetivas."""
    regras = [
        ("teste='B2' AND campo='biometria_nh_vs_lib_codigo' AND valor_b IS NULL AND uf='ZZ' AND valor_a=0",
         "Exterior: urnas sem identificação biométrica; o campo opcional qtdEleitoresLibCodigo é omitido no .bu "
         "(Res.-TSE 23.669/2021, art. 178, parágrafo único) e o CSV publica 0."),
        ("teste='B5' AND uf='ZZ' AND valor_a IS NULL AND valor_b=0",
         "Município do exterior presente na tabela por município/zona com todos os valores zero e sem seção no BU."),
    ]
    if "dsec" in disp:
        regras.append(("teste='A3' AND valor_b IS NULL AND EXISTS (SELECT 1 FROM dsec d WHERE d.turno=incompat.turno "
                       "AND d.uf=incompat.uf AND d.cd_municipio=incompat.cd_municipio AND d.nr_zona=incompat.nr_zona "
                       "AND d.nr_secao=incompat.nr_secao AND d.ST_SECAO_INSTALADA IN ('Não','N'))",
                       "Seção não instalada (ST_SECAO_INSTALADA = Não no Detalhe por seção): não há BU."))
        regras.append(("teste='A2' AND valor_b IS NULL AND EXISTS (SELECT 1 FROM dsec d WHERE d.turno=incompat.turno "
                       "AND d.uf=incompat.uf AND d.cd_municipio=incompat.cd_municipio AND d.nr_zona=incompat.nr_zona "
                       "AND d.nr_secao=incompat.nr_secao AND d.DS_ORIGEM_VOTO IN ('Sistema de apuração','Totalização'))",
                       "Resultado da seção não originado na urna eletrônica (DS_ORIGEM_VOTO = Sistema de apuração "
                       "ou Totalização, inclusive seções anuladas): não há arquivos de urna no pacote."))
    if "dmz" in disp:
        regras.append(("teste='B5' AND campo='aptos' AND valor_b - coalesce(valor_a, 0) = (SELECT "
                       "sum(CAST(QT_ELEITORES_SECOES_NAO_INSTALADAS AS BIGINT)) FROM dmz_raw m WHERE "
                       "CAST(m.NR_TURNO AS INT)=incompat.turno AND m.SG_UF=incompat.uf AND "
                       "CAST(m.CD_MUNICIPIO AS INT)=incompat.cd_municipio AND CAST(m.NR_ZONA AS INT)=incompat.nr_zona)",
                       "A tabela por município/zona inclui em QT_APTOS os eleitores de seções não instaladas "
                       "(QT_ELEITORES_SECOES_NAO_INSTALADAS), que não têm BU; a diferença é exatamente esse número."))
    if "dsec" in disp:
        regras.append(("teste='A3' AND valor_b IS NULL AND EXISTS (SELECT 1 FROM dsec d WHERE d.turno=incompat.turno "
                       "AND d.uf=incompat.uf AND d.cd_municipio=incompat.cd_municipio AND d.nr_zona=incompat.nr_zona "
                       "AND d.nr_secao=incompat.nr_secao AND d.qt_comparecimento = 0)",
                       "Seção instalada sem nenhum votante (comparecimento 0 no Detalhe por seção): o BU em CSV lista "
                       "apenas votáveis com votos, portanto não tem linhas para a seção."))
        regras.append(("teste='B5' AND valor_a IS NULL AND (SELECT sum(qt_comparecimento) FROM dsec d WHERE "
                       "d.turno=incompat.turno AND d.uf=incompat.uf AND d.cd_municipio=incompat.cd_municipio "
                       "AND d.nr_zona=incompat.nr_zona) = 0",
                       "Zona cujas seções não tiveram votantes: ausente do BU em CSV (que só lista votáveis com votos)."))
    if "dmz" in disp:
        tec = ("(SELECT sum(TRY_CAST(QT_VOTOS_NULOS_TECNICOS AS BIGINT)) FROM dmz_raw m WHERE "
               "CAST(m.NR_TURNO AS INT)=incompat.turno AND m.SG_UF=incompat.uf AND "
               "CAST(m.CD_MUNICIPIO AS INT)=incompat.cd_municipio AND CAST(m.NR_ZONA AS INT)=incompat.nr_zona)")
        txt_tec = ("Nulos técnicos: votos dados a candidato cuja votação foi anulada após a eleição constam como "
                   "nominais no BU e como nulos na totalização (QT_VOTOS_NULOS_TECNICOS do Detalhe por município/zona); "
                   "a diferença é exatamente esse número.")
        regras.append((f"teste='B4' AND valor_b IS NULL AND valor_a = {tec}", txt_tec))
        regras.append((f"teste='B5' AND campo IN ('validos','nulos') AND abs(diferenca) = {tec} AND {tec} > 0", txt_tec))
    if "logs" in disp:
        regras.append(("teste='B2' AND campo='biometria_nh_vs_lib_codigo' AND valor_b IS NULL AND valor_a = 0 "
                       "AND EXISTS (SELECT 1 FROM logs l WHERE l.turno=incompat.turno AND l.uf=incompat.uf "
                       "AND l.cd_municipio=incompat.cd_municipio AND l.nr_zona=incompat.nr_zona "
                       "AND l.nr_secao=incompat.nr_secao AND l.tem_log AND l.hab_biometrica = 0 "
                       "AND l.hab_manual_apos_falha = 0)",
                       "Seção sem identificação biométrica (o log não registra nenhuma etapa biométrica): o campo "
                       "opcional qtdEleitoresLibCodigo é omitido no .bu (Res.-TSE 23.669/2021, art. 178, parágrafo "
                       "único) e o CSV publica 0."))
    if "logs" in disp and "dsec" in disp:
        regras.append(("teste='B6' AND campo IN ('comparecimento_vs_votos_computados','biometria_nh_vs_liberacao_manual_no_log','comparecimento_vs_votos_presidente_mais_nulos_suspensao') "
                       "AND EXISTS (SELECT 1 FROM dsec d WHERE d.turno=incompat.turno AND d.uf=incompat.uf "
                       "AND d.cd_municipio=incompat.cd_municipio AND d.nr_zona=incompat.nr_zona AND d.nr_secao=incompat.nr_secao "
                       "AND d.DS_ORIGEM_VOTO = 'Sistema de apuração') "
                       "AND (campo = 'biometria_nh_vs_liberacao_manual_no_log' OR valor_b < valor_a)",
                       "Apuração mista: o resultado da seção foi gerado pelo Sistema de Apuração (DS_ORIGEM_VOTO), com "
                       "votos em cédula após falha da urna; esses votos e liberações não constam do log eletrônico."))
    if "logs" in disp:
        regras.append(("teste='B6' AND campo='comparecimento_vs_votos_presidente_mais_nulos_suspensao' "
                       "AND valor_b = valor_a + 1 AND NOT EXISTS (SELECT 1 FROM incompat j WHERE j.teste='B6' "
                       "AND j.campo='comparecimento_vs_votos_computados' AND j.turno=incompat.turno AND j.uf=incompat.uf "
                       "AND j.cd_municipio=incompat.cd_municipio AND j.nr_zona=incompat.nr_zona AND j.nr_secao=incompat.nr_secao) "
                       "AND EXISTS (SELECT 1 FROM logs l WHERE l.turno=incompat.turno AND l.uf=incompat.uf "
                       "AND l.cd_municipio=incompat.cd_municipio AND l.nr_zona=incompat.nr_zona AND l.nr_secao=incompat.nr_secao "
                       "AND l.n_ligada > 1)",
                       "Urna religada no dia (log): compatível com interrupção entre 'Voto confirmado para [Presidente]' e "
                       "'O voto do eleitor foi computado'; o BU coincide com o nº de votos computados no log. "
                       "Caso verificado manualmente: AC 1074/4/38 (desligamento às 10:25, religada às 10:54)."))
    for cond, txt in regras:
        con.execute(f"UPDATE incompat SET classificacao='Diferença explicada', explicacao=? WHERE {cond}", [txt])
    con.execute("""ALTER TABLE resumo ADD COLUMN explicadas BIGINT""")
    con.execute("""UPDATE resumo SET explicadas = (SELECT count(*) FROM incompat i WHERE i.teste=resumo.teste
                   AND i.campo=resumo.campo AND i.classificacao='Diferença explicada')""")


def referencias(con, ano: int, disp) -> None:
    """Teste L: referências documentais de cada divergência (pacote, versão, membro, hash)."""
    from .config import MANIFESTOS
    con.execute("ALTER TABLE incompat ADD COLUMN ref_pacote_urna VARCHAR")
    con.execute("ALTER TABLE incompat ADD COLUMN ref_membro VARCHAR")
    con.execute("ALTER TABLE incompat ADD COLUMN ref_bu_csv VARCHAR")
    cob = MANIFESTOS / "cobertura_arquivos_urna.csv"
    if cob.exists():
        con.execute(f"""CREATE OR REPLACE TEMP VIEW cobv AS SELECT CAST(ano AS INT) ano, CAST(turno AS INT) turno, uf,
            url || ' (ETag ' || etag || ', ' || last_modified || ')' ref FROM read_csv('{cob}', all_varchar=true)""")
        con.execute(f"UPDATE incompat SET ref_pacote_urna = c.ref FROM cobv c WHERE c.ano = {ano} "
                    "AND c.turno = incompat.turno AND c.uf = incompat.uf")
    if "logs" in disp:
        con.execute("""UPDATE incompat SET ref_membro = l.arquivo || ' (.bu/.logjez)' FROM logs l
            WHERE l.turno = incompat.turno AND l.uf = incompat.uf AND l.cd_municipio = incompat.cd_municipio
              AND l.nr_zona = incompat.nr_zona AND l.nr_secao = incompat.nr_secao""")
    dl = MANIFESTOS / "downloads.csv"
    if dl.exists():
        con.execute(f"""CREATE OR REPLACE TEMP VIEW bwv AS SELECT
            CAST(regexp_extract(url, 'bweb_(\\d)t_', 1) AS INT) turno, regexp_extract(url, 'bweb_\\dt_([A-Z]{{2}})_', 1) uf,
            regexp_extract(url, '[^/]+$') || ' (SHA-512 oficial confere: ' || coalesce(hash_oficial_confere, '?') || ')' ref
            FROM read_csv('{dl}', all_varchar=true) WHERE url LIKE '%eleicoes{ano}/buweb/bweb_%'""")
        con.execute("UPDATE incompat SET ref_bu_csv = b.ref FROM bwv b WHERE b.turno = incompat.turno AND b.uf = incompat.uf")


def executar(ano: int) -> dict:
    con = duckdb.connect()
    con.execute("SET enable_progress_bar=false")
    disp = preparar(con, ano)
    con.execute("""CREATE TABLE incompat (teste VARCHAR, turno INT, uf VARCHAR, cd_municipio INT, nr_zona INT,
        nr_secao INT, campo VARCHAR, valor_a BIGINT, fonte_a VARCHAR, valor_b BIGINT, fonte_b VARCHAR,
        diferenca BIGINT, situacao VARCHAR, classificacao VARCHAR DEFAULT 'Incompatibilidade documental',
        explicacao VARCHAR DEFAULT '')""")
    con.execute("""CREATE TABLE resumo (teste VARCHAR, descricao VARCHAR, campo VARCHAR, fonte_a VARCHAR,
        fonte_b VARCHAR, registros_comparados BIGINT, divergencias BIGINT, ausencias BIGINT,
        soma_abs_diferencas BIGINT)""")

    # B1/C1 — identidades contábeis dentro do próprio BU (Presidente)
    _diff(con, "B1", "Comparecimento = nominais + brancos + nulos (BU-CSV, Presidente)", "BWEB", "BWEB",
          f"SELECT {CHAVE}, * EXCLUDE (turno, uf, cd_municipio, nr_zona, nr_secao) FROM bweb",
          [("comparecimento_vs_soma_votos", "qt_comparecimento",
            "coalesce(votos_nominais,0)+coalesce(votos_brancos,0)+coalesce(votos_nulos,0)+coalesce(votos_outros_tipos,0)")])
    _diff(con, "C1", "Aptos = comparecimento + abstenções (BU-CSV)", "BWEB", "BWEB",
          f"SELECT {CHAVE}, * EXCLUDE (turno, uf, cd_municipio, nr_zona, nr_secao) FROM bweb",
          [("aptos_vs_comp_mais_abst", "qt_aptos", "qt_comparecimento + qt_abstencoes")])

    if "bubin" in disp:
        # B2 — BU publicado (CSV) x BU binário transmitido pela urna
        # 2022 (spec v1): qtdEleitoresLibCodigo; 2026 (spec v2): qtdEleitoresHabilitadosPorBiografia
        cols_bu = {r[0] for r in con.execute("DESCRIBE bubin").fetchall()}
        lib_expr = ("coalesce(u.bu_qtd_lib_codigo, u.bu_qtd_hab_biografia)" if "bu_qtd_hab_biografia" in cols_bu
                    else "u.bu_qtd_lib_codigo")
        _diff(con, "B2", "BU-CSV x BU binário (.bu)", "BWEB", "BUBIN",
              f"""SELECT b.turno, b.uf, b.cd_municipio, b.nr_zona, b.nr_secao,
                    b.qt_aptos a1, u.bu_qtd_aptos a2, b.qt_comparecimento c1, u.bu_qtd_comparecimento c2,
                    b.votos_nominais n1, u.bu_votos_nominais n2, b.votos_brancos br1, u.bu_votos_brancos br2,
                    b.votos_nulos nu1, u.bu_votos_nulos nu2,
                    b.qt_eleitores_biometria_nh nh, {lib_expr} lib,
                    list_sum(list_transform(map_keys(b.votos_candidato), lambda k: abs(b.votos_candidato[k]
                      - coalesce(list_sum(list_transform(list_filter(u.bu_votos_candidato, lambda e: e.k = k),
                                                        lambda e: e.v)), 0)))) dif_cand
                  FROM bweb b JOIN bubin u USING ({CHAVE})""",
              [("aptos", "a1", "a2"), ("comparecimento", "c1", "c2"), ("votos_nominais", "n1", "n2"),
               ("brancos", "br1", "br2"), ("nulos", "nu1", "nu2"),
               ("biometria_nh_vs_lib_codigo", "nh", "lib"),
               ("votos_por_candidato_soma_dif_abs", "dif_cand", "0")])
        # B2c — votos por candidato no binário que não aparecem no CSV
        _diff(con, "B2c", "Candidatos presentes no .bu e ausentes no BU-CSV", "BUBIN", "BWEB",
              f"""SELECT b.turno, b.uf, b.cd_municipio, b.nr_zona, b.nr_secao, b.votos_candidato, u.bu_votos_candidato
                  FROM bweb b JOIN bubin u USING ({CHAVE})""",
              [("votos_extra_no_bu", "coalesce(list_sum(list_transform(list_filter(bu_votos_candidato, lambda e: NOT list_contains(map_keys(votos_candidato), e.k)), lambda e: e.v)), 0)", "0")])
        # cobertura entre BWEB e BUBIN
        _diff(con, "A2", "Seção presente no BU-CSV e ausente no pacote de arquivos de urna (e vice-versa)", "BWEB", "BUBIN",
              f"""SELECT coalesce(b.turno,u.turno) turno, coalesce(b.uf,u.uf) uf, coalesce(b.cd_municipio,u.cd_municipio) cd_municipio,
                  coalesce(b.nr_zona,u.nr_zona) nr_zona, coalesce(b.nr_secao,u.nr_secao) nr_secao,
                  CASE WHEN b.nr_secao IS NULL THEN NULL ELSE 1 END pa, CASE WHEN u.nr_secao IS NULL THEN NULL ELSE 1 END pb
                  FROM bweb b FULL JOIN bubin u USING ({CHAVE})
                  WHERE (coalesce(b.turno,u.turno), coalesce(b.uf,u.uf)) IN (SELECT DISTINCT (turno, uf) FROM bubin)""",
              [("presenca", "pa", "pb")])
    if "logs" in disp:
        _diff(con, "B6", "BU-CSV x log da urna (contagens)", "BWEB", "LOG",
              f"""SELECT b.turno, b.uf, b.cd_municipio, b.nr_zona, b.nr_secao, b.qt_comparecimento, b.qt_eleitores_biometria_nh,
                  l.n_votos_computados, l.man_votou, l.n_voto_presidente, l.n_nulo_suspensao_presidente, l.tem_log
                  FROM bweb b JOIN logs l USING ({CHAVE}) WHERE l.tem_log""",
              [("comparecimento_vs_votos_computados", "qt_comparecimento", "n_votos_computados"),
               ("comparecimento_vs_votos_presidente_mais_nulos_suspensao", "qt_comparecimento",
                "n_voto_presidente + n_nulo_suspensao_presidente"),
               ("biometria_nh_vs_liberacao_manual_no_log", "qt_eleitores_biometria_nh", "man_votou")])
    if "dsec" in disp:
        _diff(con, "B3", "BU-CSV x Detalhe da apuração por seção", "BWEB", "DSEC",
              f"""SELECT b.turno, b.uf, b.cd_municipio, b.nr_zona, b.nr_secao, b.qt_aptos a1, d.qt_aptos a2,
                  b.qt_comparecimento c1, d.qt_comparecimento c2, b.qt_abstencoes ab1, d.qt_abstencoes ab2,
                  b.votos_nominais n1, d.votos_nominais n2, b.votos_brancos br1, d.votos_brancos br2,
                  b.votos_nulos nu1, d.votos_nulos nu2
                  FROM bweb b JOIN dsec d USING ({CHAVE})""",
              [("aptos", "a1", "a2"), ("comparecimento", "c1", "c2"), ("abstencoes", "ab1", "ab2"),
               ("votos_nominais", "n1", "n2"), ("brancos", "br1", "br2"), ("nulos", "nu1", "nu2")])
        _diff(con, "A3", "Seções no Detalhe por seção sem BU-CSV (e vice-versa)", "DSEC", "BWEB",
              f"""SELECT coalesce(d.turno,b.turno) turno, coalesce(d.uf,b.uf) uf, coalesce(d.cd_municipio,b.cd_municipio) cd_municipio,
                  coalesce(d.nr_zona,b.nr_zona) nr_zona, coalesce(d.nr_secao,b.nr_secao) nr_secao,
                  CASE WHEN d.nr_secao IS NULL THEN NULL ELSE 1 END pa, CASE WHEN b.nr_secao IS NULL THEN NULL ELSE 1 END pb
                  FROM dsec d FULL JOIN bweb b USING ({CHAVE})
                  WHERE coalesce(d.turno, b.turno) IN (SELECT DISTINCT turno FROM bweb)""",
              [("presenca", "pa", "pb")])
        if "vsec" in disp:
            # K2 — Detalhe por seção x Votação por seção (vale também para turnos sem BU em CSV)
            _diff(con, "K2", "Detalhe por seção x Votação por seção (soma dos votáveis)", "DSEC", "VSEC",
                  f"""WITH v AS (SELECT turno, uf, cd_municipio, nr_zona, nr_secao,
                         sum(qt_votos) FILTER (WHERE nr_votavel NOT IN (95,96,97,98)) nom,
                         sum(qt_votos) FILTER (WHERE nr_votavel = 95) br, sum(qt_votos) FILTER (WHERE nr_votavel = 96) nu
                       FROM vsec GROUP BY ALL)
                      SELECT d.turno, d.uf, d.cd_municipio, d.nr_zona, d.nr_secao,
                        d.votos_nominais n1, coalesce(v.nom, 0) n2, d.votos_brancos b1, coalesce(v.br, 0) b2,
                        d.votos_nulos u1, coalesce(v.nu, 0) u2
                      FROM dsec d LEFT JOIN v USING ({CHAVE})
                      WHERE d.ST_SECAO_INSTALADA NOT IN ('Não', 'N')""",
                  [("votos_nominais", "n1", "n2"), ("brancos", "b1", "b2"), ("nulos", "u1", "u2")])
    if "vsec" in disp:
        _diff(con, "K1", "BU-CSV x Votação por seção (caminho independente), por candidato", "BWEB", "VSEC",
              f"""WITH bl AS (SELECT turno, uf, cd_municipio, nr_zona, nr_secao, unnest(map_keys(votos_candidato)) k,
                         unnest(map_values(votos_candidato)) v FROM bweb
                  UNION ALL SELECT turno, uf, cd_municipio, nr_zona, nr_secao, 95, votos_brancos FROM bweb
                  UNION ALL SELECT turno, uf, cd_municipio, nr_zona, nr_secao, 96, votos_nulos FROM bweb)
                  SELECT coalesce(bl.turno,v.turno) turno, coalesce(bl.uf,v.uf) uf, coalesce(bl.cd_municipio,v.cd_municipio) cd_municipio,
                    coalesce(bl.nr_zona,v.nr_zona) nr_zona, coalesce(bl.nr_secao,v.nr_secao) nr_secao, bl.v, v.qt_votos,
                    coalesce(bl.k, v.nr_votavel) k
                  FROM bl FULL JOIN vsec v ON bl.turno=v.turno AND bl.uf=v.uf AND bl.cd_municipio=v.cd_municipio
                    AND bl.nr_zona=v.nr_zona AND bl.nr_secao=v.nr_secao AND bl.k=v.nr_votavel
                  WHERE (coalesce(bl.v,0) <> 0 OR coalesce(v.qt_votos,0) <> 0)
                    AND coalesce(bl.turno, v.turno) IN (SELECT DISTINCT turno FROM bweb)""",
              [("votos_votavel", "v", "qt_votos")])
    if "cmz" in disp:
        # B4 — soma das seções x votação por município e zona, por candidato
        con.execute(f"""CREATE OR REPLACE TEMP VIEW cmz AS SELECT CAST(NR_TURNO AS INT) turno, SG_UF uf,
              CAST(CD_MUNICIPIO AS INT) cd_municipio, CAST(NR_ZONA AS INT) nr_zona, CAST(NR_CANDIDATO AS INT) k,
              sum(CAST(QT_VOTOS_NOMINAIS AS BIGINT)) v FROM cmz_raw GROUP BY ALL""")
        _diff(con, "B4", "Soma das seções (BU-CSV) x Votação nominal por município e zona", "BWEB", "CMZ",
              """WITH bl AS (SELECT turno, uf, cd_municipio, nr_zona, k, sum(v) v FROM (
                      SELECT turno, uf, cd_municipio, nr_zona, unnest(map_keys(votos_candidato)) k,
                             unnest(map_values(votos_candidato)) v FROM bweb) GROUP BY ALL)
                 SELECT coalesce(bl.turno,c.turno) turno, coalesce(bl.uf,c.uf) uf, coalesce(bl.cd_municipio,c.cd_municipio) cd_municipio,
                   coalesce(bl.nr_zona,c.nr_zona) nr_zona, NULL::INT nr_secao, bl.v va, c.v vb
                 FROM bl FULL JOIN cmz c USING (turno, uf, cd_municipio, nr_zona, k)
                 WHERE coalesce(bl.v,0)<>0 OR coalesce(c.v,0)<>0""",
              [("votos_candidato_zona", "va", "vb")])
    if "dmz" in disp:
        con.execute("""CREATE OR REPLACE TEMP VIEW dmz AS SELECT CAST(NR_TURNO AS INT) turno, SG_UF uf,
              CAST(CD_MUNICIPIO AS INT) cd_municipio, CAST(NR_ZONA AS INT) nr_zona,
              sum(CAST(QT_APTOS AS BIGINT)) aptos, sum(CAST(QT_COMPARECIMENTO AS BIGINT)) comp,
              sum(CAST(QT_ABSTENCOES AS BIGINT)) abst, sum(CAST(QT_VOTOS_BRANCOS AS BIGINT)) brancos,
              sum(CAST(QT_TOTAL_VOTOS_NULOS AS BIGINT)) nulos, sum(CAST(QT_TOTAL_VOTOS_VALIDOS AS BIGINT)) validos
              FROM dmz_raw GROUP BY ALL""")
        _diff(con, "B5", "Soma das seções (BU-CSV) x Detalhe por município e zona", "BWEB", "DMZ",
              """WITH bl AS (SELECT turno, uf, cd_municipio, nr_zona, sum(qt_aptos) aptos, sum(qt_comparecimento) comp,
                    sum(qt_abstencoes) abst, sum(votos_brancos) brancos, sum(votos_nulos) nulos,
                    sum(votos_nominais) validos FROM bweb GROUP BY ALL)
                 SELECT coalesce(b.turno,d.turno) turno, coalesce(b.uf,d.uf) uf, coalesce(b.cd_municipio,d.cd_municipio) cd_municipio,
                   coalesce(b.nr_zona,d.nr_zona) nr_zona, NULL::INT nr_secao,
                   b.aptos a1, d.aptos a2, b.comp c1, d.comp c2, b.abst ab1, d.abst ab2, b.brancos br1, d.brancos br2,
                   b.nulos n1, d.nulos n2, b.validos v1, d.validos v2
                 FROM bl b FULL JOIN dmz d USING (turno, uf, cd_municipio, nr_zona)""",
              [("aptos", "a1", "a2"), ("comparecimento", "c1", "c2"), ("abstencoes", "ab1", "ab2"),
               ("brancos", "br1", "br2"), ("nulos", "n1", "n2"), ("validos", "v1", "v2")])

    explicar(con, disp)
    referencias(con, ano, disp)
    out = RESULTADOS / str(ano)
    out.mkdir(parents=True, exist_ok=True)
    con.execute(f"COPY (SELECT * FROM resumo ORDER BY teste, campo) TO '{out}/reconciliacao_resumo.csv' (HEADER)")
    con.execute(f"""COPY (SELECT * FROM incompat ORDER BY teste, campo, turno, uf, cd_municipio, nr_zona, nr_secao)
                    TO '{out}/incompatibilidades.csv' (HEADER)""")
    res = con.execute("SELECT * FROM resumo ORDER BY teste, campo").df()
    con.close()
    return {"disponiveis": disp, "resumo": res}
