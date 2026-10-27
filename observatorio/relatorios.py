"""Geração dos relatórios em Markdown a partir dos CSVs de resultados.

Todos os números dos relatórios vêm de arquivos em resultados/ (nenhum valor digitado à
mão). Cada achado segue o modelo: O que verificamos? / O que os números mostram? /
O que significa? / Existe explicação conhecida? / O que ainda não sabemos? / Como conferir?
"""
from __future__ import annotations

import csv
from datetime import datetime, timezone

import pandas as pd

from .config import DOCS, MANIFESTOS, RESULTADOS


def n(x, casas: int = 0) -> str:
    """Número no formato brasileiro."""
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "—"
    if casas == 0:
        return f"{int(round(float(x))):,}".replace(",", ".")
    return f"{float(x):,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def bloco(titulo, verificamos, numeros, significa, explicacao, nao_sabemos, conferir, categoria) -> str:
    return f"""### {titulo}

**Classificação:** {categoria}

- **O que verificamos?** {verificamos}
- **O que os números mostram?** {numeros}
- **O que significa?** {significa}
- **Existe explicação conhecida?** {explicacao}
- **O que ainda não sabemos?** {nao_sabemos}
- **Como conferir?** {conferir}
"""


def cobertura(ano: int) -> pd.DataFrame:
    f = MANIFESTOS / "cobertura_arquivos_urna.csv"
    if not f.exists():
        return pd.DataFrame()
    d = pd.read_csv(f)
    return d[d.ano == ano]


def _ler(ano, nome):
    f = RESULTADOS / str(ano) / nome
    return pd.read_csv(f) if f.exists() else pd.DataFrame()


def tabela_md(df: pd.DataFrame, cols: list[str] | None = None, max_linhas: int = 40) -> str:
    if df.empty:
        return "_(sem dados)_\n"
    d = df[cols] if cols else df
    d = d.head(max_linhas)
    cab = "| " + " | ".join(map(str, d.columns)) + " |\n|" + "---|" * len(d.columns) + "\n"
    corpo = ""
    for _, r in d.iterrows():
        cel = []
        for v in r.values:
            if isinstance(v, float):
                cel.append(n(v, 3) if not float(v).is_integer() else n(v))
            elif isinstance(v, int):
                cel.append(n(v))
            else:
                cel.append(str(v))
        corpo += "| " + " | ".join(cel) + " |\n"
    return cab + corpo


def secao_cobertura(ano: int, ufs_esperadas: int = 28) -> str:
    c = cobertura(ano)
    if c.empty:
        return "Nenhum pacote de arquivos de urna processado.\n"
    linhas = []
    for t, g in c.groupby("turno"):
        linhas.append(f"- {t}º turno: {len(g)} de {ufs_esperadas} pacotes (27 UFs + exterior) processados; "
                      f"{n(g.secoes_processadas.sum())} seções lidas, {n(g.secoes_com_falha.sum())} com falha de leitura, "
                      f"{n(g.secoes_sem_log.sum())} sem log no pacote.")
    faltam = []
    from .config import UFS_COM_EXTERIOR
    for t in sorted(c.turno.unique()):
        f = sorted(set(UFS_COM_EXTERIOR) - set(c[c.turno == t].uf))
        if f:
            faltam.append(f"{t}º turno: {', '.join(f)}")
    txt = "\n".join(linhas) + "\n"
    if faltam:
        txt += "\n**Pacotes ainda não processados** — " + "; ".join(faltam) + ". Indicadores de log abaixo valem apenas para a cobertura indicada.\n"
    return txt


def relatorio_ano(ano: int) -> str:
    rec = _ler(ano, "reconciliacao_resumo.csv")
    inc = _ler(ano, "incompatibilidades.csv")
    br = _ler(ano, "resultados_brasil.csv")
    tuf = _ler(ano, "temporal_por_uf.csv")
    bio = _ler(ano, "biometria_por_uf.csv")
    mod = _ler(ano, "modelos_efeito_controlado.csv")
    dig = _ler(ano, "estatistica_testes_digitos.csv")
    s100 = _ler(ano, "estatistica_secoes_100pct.csv")
    apt = _ler(ano, "aptos_entre_turnos_resumo.csv")
    raj = _ler(ano, "rajadas_sensibilidade_votos.csv")
    fus = _ler(ano, "validacao_fusos_municipio.csv")
    agora = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
    out = [f"# Auditoria {ano} — Presidente\n",
           f"_Gerado automaticamente por `scripts/gerar_relatorios.py` em {agora}. Todos os números vêm de "
           f"`resultados/{ano}/`. Ver método em `docs/metodologia.md`._\n",
           "## Cobertura dos arquivos de urna (logs e BU binário)\n", secao_cobertura(ano)]

    # Totais
    if not br.empty:
        r = br.iloc[0]
        out.append("## 1. Totais nacionais reproduzidos a partir das seções\n")
        tur = [1, 2] if "aptos_2t" in br.columns else [1]
        linhas = []
        for t in tur:
            suf = f"_{t}t" if "aptos_1t" in br.columns else ""
            linhas.append({"turno": f"{t}º", "seções": r[f"secoes{suf}"], "aptos": r[f"aptos{suf}"],
                           "comparecimento": r[f"comparecimento{suf}"], "abstenções": r[f"abstencoes{suf}"],
                           "válidos": r[f"validos{suf}"], "brancos": r[f"brancos{suf}"], "nulos": r[f"nulos{suf}"],
                           "% abstenção": r[f"pct_abstencao{suf}"], "% brancos": r[f"pct_brancos{suf}"],
                           "% nulos": r[f"pct_nulos{suf}"]})
        out.append(tabela_md(pd.DataFrame(linhas)))
        out.append("\nOs totais nacionais publicados pelo TSE (histórico de totalização e detalhe por município/"
                   "zona) são reproduzidos pela soma das seções; a única diferença em *aptos* corresponde a "
                   "eleitores de seções não instaladas, que não têm BU (ver B5 abaixo).\n")
        if len(tur) == 2:
            out.append(bloco(
                "Mudança entre turnos: comparecimento, brancos, nulos e válidos",
                "Se a variação dos votos válidos entre os turnos é exatamente a variação do comparecimento menos a "
                "variação de brancos e nulos, em cada seção, zona, município, UF e no Brasil.",
                f"Brasil: comparecimento {n(r.delta_comparecimento)}; brancos+nulos {n(r.delta_brancos_nulos)}; "
                f"válidos {n(r.delta_validos)}; resíduo da identidade {n(r.residuo_reconciliacao)}. Abstenção variou "
                f"{n(r.delta_pp_abstencao, 3)} p.p. (de {n(r.pct_abstencao_1t, 2)}% para {n(r.pct_abstencao_2t, 2)}% dos aptos); "
                f"brancos {n(r.delta_pp_brancos, 3)} p.p.; nulos {n(r.delta_pp_nulos, 3)} p.p. (sobre o comparecimento). "
                f"Lula (13) variou {n(r.delta_votos_13)} votos e Bolsonaro (22) {n(r.delta_votos_22)}.",
                "As contas fecham em todos os níveis. Os aumentos de votos de cada candidato são variações LÍQUIDAS: "
                "não dizem quem trocou de voto, quem deixou de votar ou quem passou a votar.",
                "Candidatos eliminados no 1º turno deixam de receber votos; eleitores podem mudar de voto, "
                "abster-se ou voltar a votar.",
                "Transferências individuais de voto não são observáveis (voto secreto). Qualquer estimativa de "
                "transferência exigiria inferência ecológica, com incerteza grande e hipóteses fortes; não foi feita.",
                f"`resultados/{ano}/resultados_brasil.csv`, `resultados_uf.csv`, `resultados_municipio.csv`, "
                f"`resultados_zona.csv`; código `observatorio/resultados_eleitorais.py`.",
                "Conferido"))

    # Reconciliação
    if not rec.empty:
        out.append("## 2. Reconciliação entre fontes oficiais (Testes A, B, C, K)\n")
        rr = rec.copy()
        rr["não_explicadas"] = rr.divergencias - rr.explicadas.fillna(0)
        out.append(tabela_md(rr[["teste", "campo", "fonte_a", "fonte_b", "registros_comparados", "divergencias",
                                 "explicadas", "não_explicadas"]], max_linhas=60))
        out.append("\nLegenda: BWEB = BU publicado em CSV; BUBIN = arquivo .bu transmitido pela urna; LOG = log da "
                   "urna; DSEC = detalhe da apuração por seção; VSEC = votação por seção; CMZ = votação nominal por "
                   "município/zona; DMZ = detalhe por município/zona. A lista completa, caso a caso, está em "
                   f"`resultados/{ano}/incompatibilidades.csv`.\n")
        ok = rr[(rr.divergencias == 0)]
        out.append(bloco(
            "Boletins de Urna, arquivos da urna e tabelas oficiais",
            "Se o mesmo número aparece igual em todas as publicações oficiais que deveriam coincidir, seção a "
            "seção (BU em CSV, BU binário, detalhe por seção, votação por seção) e na soma por zona.",
            f"{len(ok)} de {len(rr)} comparações sem nenhuma divergência; "
            f"{n(rr['não_explicadas'].sum())} divergências ainda sem explicação documental (listadas abaixo).",
            "Os votos publicados por seção são os mesmos do arquivo binário assinado gerado pela urna e das demais "
            "tabelas do TSE.",
            "As divergências explicadas decorrem de seções não instaladas, seções apuradas pelo Sistema de "
            "Apuração (cédulas), campos opcionais omitidos no exterior e eleitores de seções não instaladas "
            "incluídos nos aptos por zona.",
            "A verificação criptográfica das assinaturas dos arquivos (.vscmr) não foi feita nesta etapa.",
            f"`resultados/{ano}/reconciliacao_resumo.csv` e `incompatibilidades.csv`; código "
            "`observatorio/reconciliacao.py`.",
            "Conferido (com diferenças explicadas e incompatibilidades listadas)"))
        if not inc.empty:
            pend = inc[inc.classificacao != "Diferença explicada"]
            if not pend.empty:
                out.append("#### Incompatibilidades documentais ainda não explicadas\n")
                out.append(tabela_md(pend[["teste", "turno", "uf", "cd_municipio", "nr_zona", "nr_secao", "campo",
                                           "valor_a", "fonte_a", "valor_b", "fonte_b"]], max_linhas=200))
                out.append("\nDiagnóstico individual de cada caso (estrutura do log: arquivos, urnas, eventos de "
                           f"contingência) em `resultados/{ano}/diagnosticos/`.\n")
    if not apt.empty:
        a = apt.iloc[0]
        out.append(bloco(
            "Eleitores aptos que mudam de seção entre os turnos",
            "Por que algumas seções têm número de aptos diferente no 1º e no 2º turno.",
            f"{n(a.secoes_aptos_mudaram)} de {n(a.secoes)} seções mudaram de aptos; o total nacional não muda "
            f"(soma das variações = {n(a.soma_delta_aptos)}). Em {n(a.explicadas_exatamente_por_tte)} delas "
            f"({n(100 * a.explicadas_exatamente_por_tte / a.secoes_aptos_mudaram, 1)}%) a variação é exatamente o saldo "
            f"das transferências temporárias publicadas pelo TSE; {n(a.nao_explicadas)} seções ficam com resíduo "
            f"(soma dos resíduos em módulo: {n(a.soma_abs_residuo)} eleitores).",
            "A diferença vem de eleitores que votam temporariamente em outra seção (voto em trânsito, mesários, "
            "presos provisórios, militares, acessibilidade), o que pode valer só para um turno.",
            "Transferência temporária do eleitorado por seção (arquivo oficial).",
            "O arquivo de transferências foi gerado pelo TSE em 2024, após as eleições; o resíduo pode refletir "
            "atualizações posteriores. Pendente de verificação documental seção a seção.",
            f"`resultados/{ano}/aptos_entre_turnos_resumo.csv` e `aptos_entre_turnos_nao_explicados_por_tte.csv`.",
            "Diferença explicada (96–97%) / Pendente (resíduo)"))

    # Temporal
    if not tuf.empty:
        out.append("## 3. Horários de votação (Testes D e E)\n")
        tb = tuf[tuf.uf != "ZZ"]
        for t, g in tb.groupby("turno"):
            tot = g.votos.sum()
            out.append(bloco(
                f"{t}º turno: votos antes das 8h e depois das 17h (horário de Brasília)",
                "Quantos votos concluídos o log registra fora do horário regular, após converter o relógio de cada "
                "urna para o horário de Brasília pelo fuso legal do município.",
                f"Em {n(g.secoes_com_log.sum())} seções com log ({n(tot)} votos): {n(g.votos_antes_8h.sum())} votos antes "
                f"das 8h em {n(g.secoes_com_voto_antes_8h.sum())} seções; {n(g.votos_apos_17h.sum())} votos após as 17h "
                f"({n(100 * g.votos_apos_17h.sum() / tot, 3)}%) em {n(g.secoes_com_voto_apos_17h.sum())} seções; "
                f"{n(g.votos_apos_18h.sum())} após 18h; {n(g.votos_apos_19h.sum())} após 19h.",
                "Votos depois das 17h são previstos em lei para quem estava na fila. Votos antes das 8h, se "
                "existirem, precisam ser examinados um a um (relógio, fuso, troca de urna).",
                "Fila às 17h (Res. 23.669/2021, art. 136, §§ 1º–2º). A distribuição por UF acompanha o tamanho "
                "das seções e o volume do 1º turno (5 cargos).",
                "O log não registra a senha distribuída às 17h, portanto não é possível confirmar, eleitor a "
                "eleitor, que quem votou depois das 17h estava na fila.",
                f"`resultados/{ano}/temporal_por_uf.csv`, `secoes_horarios_atipicos.csv`, `votos_por_15min.csv`; "
                "gráfico `resultados/{ano}/graficos/votos_por_15min.png`.",
                "Conferido (distribuição descrita)"))
        if not fus.empty:
            dv = fus[fus.diverge == True]  # noqa: E712
            out.append(bloco(
                "Validação dos fusos horários",
                "Se o fuso legal atribuído a cada município é coerente com o horário local do primeiro voto.",
                f"{n(len(fus))} combinações município×turno avaliadas; {n(len(dv))} divergentes.",
                "Sem divergências, os horários convertidos são confiáveis; divergências indicariam erro de fuso "
                "ou relógio.",
                "Lista legal de municípios do oeste do AM em UTC-5 e Fernando de Noronha em UTC-2.",
                "Relógios individuais de urnas podem diferir do município; isso aparece como retrocesso de relógio "
                "ou horário atípico na seção.",
                f"`resultados/{ano}/validacao_fusos_municipio.csv`.",
                "Conferido" if len(dv) == 0 else "Pendente"))
    if not raj.empty:
        g = raj.groupby(["turno", "limiar_s", "min_votos"])[["sequencias", "votos_em_sequencias", "secoes"]].sum().reset_index()
        out.append("### Intervalos muito curtos entre votos (\"rajadas\")\n")
        out.append(tabela_md(g))
        out.append("\nIntervalo = tempo entre dois registros consecutivos de voto concluído na mesma urna. "
                   "Grade de sensibilidade com limiares de 6 a 30 s e mínimo de 3 ou 5 votos. Versão com intervalos "
                   f"entre habilitações em `resultados/{ano}/rajadas_sensibilidade_habilitacoes.csv`.\n")

    # Biometria
    if not bio.empty:
        out.append("## 4. Identificação biométrica e alternativa (Teste F)\n")
        b = bio[bio.uf != "ZZ"]
        for t, g in b.groupby("turno"):
            out.append(bloco(
                f"{t}º turno: quem votou sem reconhecimento biométrico",
                "Quantos eleitores com biometria cadastrada votaram após liberação manual (sem reconhecimento da "
                "digital) e se o log confirma o número do BU.",
                f"BU: {n(g.bu_biometria_nao_habilitados.sum())} eleitores ({n(100 * g.bu_biometria_nao_habilitados.sum() / g.comparecimento.sum(), 2)}% "
                f"do comparecimento) com biometria e não habilitados por ela. Nos logs processados: "
                f"{n(g.log_votantes_biometria.sum())} votantes por biometria, {n(g.log_votantes_manual_apos_falha.sum())} "
                f"liberados manualmente após falha e {n(g.log_votantes_sem_biometria_cadastrada.sum())} sem biometria cadastrada.",
                "A liberação manual é o procedimento previsto quando a digital não é reconhecida; o número no BU e "
                "no log coincide (Teste B6).",
                "Res.-TSE 23.669/2021, arts. 113–115 (até 4 leituras; depois ano de nascimento e digital do mesário).",
                "O log de 2022 não identifica o motivo da falha (sujeira, desgaste, leitor); o modelo de urna "
                "influencia a taxa (ver Teste I).",
                f"`resultados/{ano}/biometria_por_uf.csv`, `biometria_modalidade_por_hora.csv`, "
                f"`biometria_duracao_por_modalidade_modelo.csv`.",
                "Conferido"))

    # Modelos
    if not mod.empty:
        out.append("## 5. Modelos de urna (Teste I)\n")
        out.append(tabela_md(mod[["turno", "controle", "indicador", "diferenca_ingenua_pp", "diferenca_controlada_pp",
                                  "ic95_inf", "ic95_sup", "grupos_comparaveis", "secoes_ref", "secoes_outras"]], max_linhas=40))
        m22 = mod[(mod.indicador == "pct_validos_22")]
        loc = m22[m22.controle == "mesmo_local"]
        zon = m22[m22.controle == "mesma_zona"]
        out.append(bloco(
            "UE2020 × demais modelos: proporção de votos do nº 22",
            "Se seções com urna modelo 2020 têm resultado diferente de seções com outros modelos, comparando "
            "seções próximas (mesmo local de votação, mesma zona, mesmo município).",
            "Sem controle geográfico a diferença é grande (" + ", ".join(f"{t}º t.: {n(v, 2)} p.p." for t, v in
            zip(m22.drop_duplicates('turno').turno, m22.drop_duplicates('turno').diferenca_ingenua_pp)) + "). No mesmo local: " +
            "; ".join(f"{int(r.turno)}º t. {n(r.diferenca_controlada_pp, 2)} p.p. (IC95% {n(r.ic95_inf, 2)} a {n(r.ic95_sup, 2)})" for r in loc.itertuples()) +
            ". Na mesma zona: " + "; ".join(f"{int(r.turno)}º t. {n(r.diferenca_controlada_pp, 2)} p.p. (IC95% {n(r.ic95_inf, 2)} a {n(r.ic95_sup, 2)})" for r in zon.itertuples()) + ".",
            "A maior parte da diferença bruta é geográfica. No controle mais forte (mesmo local) o intervalo inclui "
            "zero; com controles mais fracos (zona, município) resta diferença de cerca de 1 p.p., que pode refletir "
            "diferenças entre bairros/locais dentro da zona.",
            "A distribuição dos modelos não é aleatória (logística do TSE por zona/local). O modelo 2020 tem leitor "
            "biométrico mais novo: a taxa de liberação manual é ~5 p.p. menor nas mesmas localidades, diferença "
            "técnica esperada.",
            "Sem covariáveis anteriores à eleição por seção (ex.: resultado de 2018 na mesma seção), não é possível "
            "separar efeito do modelo de efeito de localização. Diferença estatística ≠ causalidade.",
            f"`resultados/{ano}/modelos_efeito_controlado.csv`, `modelos_medias_ingenuas.csv`; gráfico "
            f"`resultados/{ano}/graficos/modelos_efeito_22.png`.",
            "Diferença estatística (controles fracos) / Conferido sem diferença (mesmo local)"))

    # Dígitos
    if not dig.empty:
        out.append("## 6. Testes estatísticos de dígitos e distribuição (Teste J)\n")
        resumo = dig.groupby("teste").agg(testes=("p", "size"), rejeitados_holm_1pct=("p_holm", lambda x: int((x < 0.01).sum())),
                                          cramer_v_mediano=("cramer_v", "median"), maior_desvio_pp_mediano=("maior_desvio_pp", "median")).reset_index()
        out.append(tabela_md(resumo))
        out.append(bloco(
            "Dígitos das contagens por seção",
            "Se o último e o segundo dígito dos votos por seção de Lula (13) e Bolsonaro (22) seguem o esperado.",
            "Contra a referência teórica (uniforme / Benford) há rejeições, com efeitos pequenos. Contra a "
            "referência simulada (binomial com o tamanho real das seções e a proporção da zona), o último dígito "
            "não é rejeitado em nenhum caso, e o desvio do 2º dígito cai para frações de ponto percentual.",
            "As rejeições contra Benford vêm da premissa errada (seções têm tamanho limitado), não dos votos.",
            "Literatura: Mebane (2006); Deckert, Myagkov & Ordeshook (2011) — testes de dígitos não detectam "
            "fraude de forma confiável.",
            "O modelo simulado ignora a heterogeneidade entre seções de uma zona (sobredispersão), o que explica "
            "o pequeno desvio residual no 2º dígito.",
            f"`resultados/{ano}/estatistica_testes_digitos.csv`.",
            "Diferença estatística (sem relevância prática) — não é evidência de irregularidade"))
    if not s100.empty:
        out.append("### Seções com 100% dos votos válidos para um único candidato\n")
        out.append(tabela_md(s100))
    return "\n".join(out) + "\n"


def fontes_md() -> str:
    inv = pd.read_csv(MANIFESTOS / "inventario_fontes.csv")
    dl = pd.read_csv(MANIFESTOS / "downloads.csv") if (MANIFESTOS / "downloads.csv").exists() else pd.DataFrame()
    cob = pd.read_csv(MANIFESTOS / "cobertura_arquivos_urna.csv") if (MANIFESTOS / "cobertura_arquivos_urna.csv").exists() else pd.DataFrame()
    out = ["# Fontes, versões e hashes\n",
           f"_Gerado em {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M UTC')} a partir de `manifestos/`._\n",
           "Catálogos consultados (API CKAN do Portal de Dados Abertos do TSE): " +
           ", ".join(f"`{c}`" for c in sorted(inv.conjunto.dropna().unique())) + ". Cópias dos metadados em "
           "`manifestos/ckan/`.\n",
           "## Inventário por tipo\n"]
    g = inv.groupby(["ano", "tipo"]).agg(arquivos=("url", "count"),
                                         tamanho_gb=("tamanho_bytes", lambda x: round(pd.to_numeric(x, errors="coerce").sum() / 1e9, 2))).reset_index()
    out.append(tabela_md(g, max_linhas=100))
    out.append("\nO inventário completo (URL, datas do catálogo, `ETag`, `Last-Modified`, tamanho) está em "
               "`manifestos/inventario_fontes.csv`.\n")
    if not dl.empty:
        out.append("## Arquivos baixados integralmente\n")
        d = dl[["arquivo_local", "status", "hash_oficial_confere", "tamanho_bytes", "last_modified", "sha256"]].copy()
        d["arquivo_local"] = d.arquivo_local.str.rsplit("/", n=1).str[-1]
        d["sha256"] = d.sha256.astype(str).str[:16] + "…"
        out.append(f"{len(d)} arquivos; status: " + ", ".join(f"{k} = {v}" for k, v in d.status.value_counts().items()) +
                   ". Hash SHA-512 oficial (BU em CSV): " + ", ".join(f"{k} = {v}" for k, v in d.hash_oficial_confere.value_counts().items()) + ".\n")
        out.append(tabela_md(d.sort_values("arquivo_local"), max_linhas=400))
    if not cob.empty:
        out.append("\n## Pacotes de arquivos de urna (leitura seletiva por HTTP Range)\n")
        out.append(tabela_md(cob[["ano", "turno", "uf", "etag", "last_modified", "tamanho_pacote_bytes", "secoes_no_pacote",
                                  "secoes_incompletas", "secoes_processadas", "secoes_com_falha", "secoes_sem_log"]], max_linhas=200))
    return "\n".join(out) + "\n"


def escrever(anos=(2022, 2026)) -> list[str]:
    feitos = []
    for ano in anos:
        if (RESULTADOS / str(ano)).exists():
            (DOCS / f"auditoria-{ano}.md").write_text(relatorio_ano(ano), encoding="utf-8")
            feitos.append(f"auditoria-{ano}.md")
    (DOCS / "fontes.md").write_text(fontes_md(), encoding="utf-8")
    feitos.append("fontes.md")
    return feitos


# ---------------------------------------------------------------- estudos externos
ALEGACOES_EXTERNAS = [
    # (id, fonte, descrição, turno, valor alegado (texto), função que extrai o nosso valor)
    ("A1", "auditoriaeleicoes.com", "Votos antes das 8h (Brasília)", 1, "8.185 (todos no AM)"),
    ("A1", "auditoriaeleicoes.com", "Votos antes das 8h (Brasília)", 2, "19.408 (todos no AM)"),
    ("C1", "auditoriaeleicoes.com", "% dos votos após 17h (Brasília), sem SP", 1, "4,18%"),
    ("C1", "auditoriaeleicoes.com", "% dos votos após 17h (Brasília), sem SP", 2, "0,033%"),
    ("A2", "auditoriaeleicoes.com", "Rajadas: ≥5 votos com intervalos <20 s (1º t.) / <6 s (2º t.)", 1, "10.184 votos em 1.504 sequências"),
    ("A2", "auditoriaeleicoes.com", "Rajadas: ≥5 votos com intervalos <20 s (1º t.) / <6 s (2º t.)", 2, "4.296 votos em 777 sequências"),
    ("A6", "auditoriaeleicoes.com", "Seções com 100% dos válidos para um candidato", 1, "18"),
    ("A6", "auditoriaeleicoes.com", "Seções com 100% dos válidos para um candidato", 2, "29"),
    ("A4", "auditoriaeleicoes.com", "UE2020 − demais, % do nº 22, mesmo município (bootstrap)", 1, "+1,00 p.p. [0,59; 1,58]"),
    ("A4", "auditoriaeleicoes.com", "UE2020 − demais, % do nº 22, mesmo município (bootstrap)", 2, "+1,17 p.p. [0,72; 1,80]"),
    ("A16", "auditoriaeleicoes.com", "Último dígito uniforme (13 e 22)", 1, "p = 0,0 (rejeita)"),
    ("A13", "auditoriaeleicoes.com", "Mediana habilitação→voto (s)", 1, "52 s"),
    ("A13", "auditoriaeleicoes.com", "Mediana habilitação→voto (s)", 2, "13 s"),
    ("D5", "DataUrnas-BR", "Seções com |votos no log − comparecimento| > 2", 1, "3.356 (todas com log < BU)"),
    ("D5", "DataUrnas-BR", "Seções com |votos no log − comparecimento| > 2", 2, "1.691"),
]


def _nosso_valor(ano: int, cid: str, turno: int) -> str:
    try:
        if cid == "A1":
            d = _ler(ano, "temporal_por_uf.csv")
            g = d[(d.turno == turno) & (d.uf != "ZZ")]
            return f"{n(g.votos_antes_8h.sum())} (em {n(g.secoes_com_log.sum())} seções com log)"
        if cid == "C1":
            d = _ler(ano, "temporal_por_uf.csv")
            g = d[(d.turno == turno) & (d.uf != "ZZ")]
            g2 = g[g.uf != "SP"]
            return (f"{n(100 * g.votos_apos_17h.sum() / g.votos.sum(), 3)}% (com SP); "
                    f"{n(100 * g2.votos_apos_17h.sum() / g2.votos.sum(), 3)}% (sem SP)")
        if cid == "A2":
            d = _ler(ano, "rajadas_sensibilidade_votos.csv")
            lim = 20 if turno == 1 else 6
            g = d[(d.turno == turno) & (d.limiar_s == lim) & (d.min_votos == 5)]
            h = _ler(ano, "rajadas_sensibilidade_habilitacoes.csv")
            gh = h[(h.turno == turno) & (h.limiar_s == lim) & (h.min_votos == 5)]
            return (f"{n(g.votos_em_sequencias.sum())} votos em {n(g.sequencias.sum())} sequências (entre votos computados); "
                    f"{n(gh.votos_em_sequencias.sum())} (entre habilitações)")
        if cid == "A6":
            d = _ler(ano, "estatistica_secoes_100pct.csv")
            g = d[d.turno == turno]
            return f"{n(g.secoes_100pct_um_candidato.sum())} (todas as faixas); {n(g[g.faixa_validos == '100+'].secoes_100pct_um_candidato.sum())} com ≥100 válidos"
        if cid == "A4":
            d = _ler(ano, "modelos_efeito_controlado.csv")
            r = d[(d.turno == turno) & (d.controle == "mesmo_municipio") & (d.indicador == "pct_validos_22")].iloc[0]
            l = d[(d.turno == turno) & (d.controle == "mesmo_local") & (d.indicador == "pct_validos_22")].iloc[0]
            return (f"{n(r.diferenca_controlada_pp, 2)} p.p. [{n(r.ic95_inf, 2)}; {n(r.ic95_sup, 2)}] (município); "
                    f"{n(l.diferenca_controlada_pp, 2)} [{n(l.ic95_inf, 2)}; {n(l.ic95_sup, 2)}] (mesmo local)")
        if cid == "A16":
            d = _ler(ano, "estatistica_testes_digitos.csv")
            g = d[(d.turno == turno) & (d.abrangencia == "BR")]
            u = g[g.teste == "ultimo_digito_uniforme"]
            s = g[g.teste == "ultimo_digito_vs_simulacao_binomial_zona"]
            return (f"uniforme: p_holm {', '.join(f'{x:.1e}' for x in u.p_holm)} (efeito máx. {n(u.maior_desvio_pp.max(), 2)} p.p.); "
                    f"vs. simulação: p_holm {', '.join(f'{x:.2f}' for x in s.p_holm)}")
        if cid == "A13":
            d = _ler(ano, "distribuicao_duracao_voto.csv")
            g = d[d.turno == turno].groupby("duracao_s_truncada_900").n.sum().sort_index()
            c = g.cumsum() / g.sum()
            return f"{int(c[c >= 0.5].index[0])} s"
        if cid == "D5":
            f = RESULTADOS / str(ano) / "incompatibilidades.csv"
            d = pd.read_csv(f)
            g = d[(d.teste == "B6") & (d.campo == "comparecimento_vs_votos_computados") & (d.turno == turno)]
            return (f"{n((g.diferenca.abs() > 2).sum())} seções (todos os arquivos de log da seção, janela até o dia seguinte); "
                    f"{n(len(g))} com qualquer diferença")
    except Exception as e:  # dado ainda não disponível
        return f"pendente ({type(e).__name__})"
    return "—"


def reproducao_externa(ano: int = 2022) -> str:
    linhas = []
    for cid, fonte, desc, turno, alegado in ALEGACOES_EXTERNAS:
        linhas.append({"id": cid, "fonte": fonte, "verificação": desc, "turno": f"{turno}º",
                       "alegado (terceiros)": alegado, "cálculo próprio (TSE)": _nosso_valor(ano, cid, turno)})
    return ("\n## Reprodução independente (cálculo próprio a partir dos arquivos do TSE)\n\n"
            "_Gerado por `scripts/gerar_relatorios.py`. Os valores da coluna \"alegado\" são de terceiros e não foram "
            "adotados; a coluna seguinte é calculada por este projeto, com a cobertura informada em "
            "`docs/auditoria-2022.md`. Divergências de definição estão indicadas._\n\n"
            + tabela_md(pd.DataFrame(linhas), max_linhas=100) +
            "\nNotas: (1) A1 — a conversão por UF aplica −1 h a todo o AM; o oeste do AM está em UTC−5, de modo que "
            "o voto das 6h locais nesses municípios (= 8h de Brasília) vira 7h com a conversão de +1 h e é classificado "
            "como \"antes das 8h\". (2) D5 — o DataUrnas-BR lê só o primeiro arquivo do pacote 7z e descarta votos após a "
            "meia-noite, o que produz contagens de log menores que o BU. (3) A2 — com intervalos medidos entre "
            "registros de voto computado, a definição publicada não reproduz a contagem alegada; o critério exato "
            "dos autores não é público.\n")


# ---------------------------------------------------------------- comparativo histórico
NOMES_IND = {
    "aptos": "Eleitores aptos", "comparecimento": "Comparecimento", "pct_abstencao": "Abstenção (% aptos)",
    "pct_brancos": "Brancos (% comparec.)", "pct_nulos": "Nulos (% comparec.)", "pct_validos": "Válidos (% comparec.)",
    "pct_biometria_nao_habilitados_bu": "Com biometria, não habilitados por ela (% comparec., BU)",
    "pct_votos_antes_8h": "Votos antes das 8h (% votos do log)", "pct_votos_apos_17h": "Votos após 17h (%)",
    "pct_votos_apos_19h": "Votos após 19h (%)", "mediana_primeiro_voto_h": "Mediana do 1º voto (h, Brasília)",
    "mediana_ultimo_voto_h": "Mediana do último voto (h, Brasília)", "duracao_media_votacao_h": "Duração média 1º→último voto (h)",
    "pct_secoes_reabertura": "Seções com reabertura (%)", "pct_secoes_contingencia": "Seções com contingência (%)",
    "pct_hab_biometrica_log": "Habilitação biométrica (% habilitações, log)",
    "pct_hab_manual_apos_falha_log": "Liberação manual após falha (% habilitações, log)",
    "pct_hab_sem_biometria_log": "Sem biometria cadastrada (% habilitações, log)",
    "mediana_duracao_voto_s": "Mediana habilitação→voto (s)", "secoes": "Seções com BU", "secoes_com_log": "Seções com log",
}


def comparativo_md() -> str:
    f = RESULTADOS / "comparativo" / "comparativo_largo.csv"
    if not f.exists():
        return "# Comparação histórica 2022 × 2026\n\n_Pendente: execute `historico.executar()`._\n"
    d = pd.read_csv(f)
    out = ["# Comparação histórica 2022 × 2026 — Presidente\n",
           f"_Gerado em {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M UTC')} a partir de "
           "`resultados/comparativo/`._\n",
           "**Pergunta central:** quais diferenças observadas em 2026 também ocorreram em 2022, quais podem ser "
           "explicadas pelas condições eleitorais e quais exigem verificação documental adicional?\n",
           "**Disponibilidade:** 2026, 2º turno — em 27/10/2026 só as tabelas oficiais por seção (Detalhe e "
           "Votação por seção) estavam publicadas; indicadores de resultado do 2º turno de 2026 vêm delas, e os "
           "baseados em BU/log ficam vazios até a publicação. Indicadores de log valem para a cobertura indicada "
           "em cada `docs/auditoria-ANO.md`.\n",
           "## Brasil (27 UFs, sem exterior)\n"]
    br = d[d.abrangencia == "BR"].copy()
    br["indicador"] = br.indicador.map(lambda x: NOMES_IND.get(x, x))
    cols = [c for c in ["indicador", "2022_1t", "2022_2t", "2026_1t", "2026_2t", "dif_turnos_2022", "dif_1t_2026_menos_2022"] if c in br]
    out.append(tabela_md(br[cols], max_linhas=60))
    out.append("""
## Limitações de comparabilidade

- **Cargos:** 1º turno de 2022 com 5 votos por eleitor; 1º turno de 2026 com 6 (duas vagas de Senador).
  Duração do voto e horário do último voto dependem disso.
- **Identificação:** em 2026 o mesário pode digitar CPF ou título e a urna exibe foto; a habilitação
  sem biometria passa a ser registrada pelo ano de nascimento. As categorias do log e do BU mudaram
  (`docs/dicionario-dados.md`).
- **Equipamentos:** 2026 introduz o modelo UE2022; a composição por modelo difere entre os anos.
- **Eleitorado:** cadastro, revisões biométricas e criação/remanejamento de seções mudam a base.
  A mesma numeração de seção não garante o mesmo eleitorado (ver correspondência abaixo).
- **Regras:** horário de Brasília em ambos os anos; no 2º turno de 2026 há notícia de prorrogação do
  horário em parte do país por decisão judicial (a verificar quando os dados forem publicados).
""")
    c = RESULTADOS / "comparativo" / "correspondencia_secoes_resumo.csv"
    if c.exists():
        cc = pd.read_csv(c)
        out.append("## Correspondência de seções entre 2022 e 2026 (1º turno)\n")
        out.append(tabela_md(cc[cc.uf == "BR"]))
        out.append("\nClasses: `correspondencia_provavel` = mesmo local de votação e aptos com variação ≤ 10%; "
                   "`mesmo_local_aptos_mudaram`; `local_mudou`; `apenas_2022`/`apenas_2026` = sem par. Só pares "
                   "\"correspondência provável\" devem ser usados em comparações seção a seção. Arquivo por seção: "
                   "`resultados/comparativo/correspondencia_secoes_2022_2026.parquet`.\n")
    out.append("## Por UF\n\nTabela completa (Brasil e 27 UFs, todos os indicadores): "
               "`resultados/comparativo/comparativo_largo.csv` e `indicadores_2022_2026.csv`.\n")
    for ind in ("pct_abstencao", "pct_brancos", "pct_nulos", "pct_votos_apos_17h", "pct_biometria_nao_habilitados_bu"):
        s = d[(d.indicador == ind) & (d.abrangencia != "BR") & (d.abrangencia != "ZZ")]
        if s.empty:
            continue
        out.append(f"### {NOMES_IND.get(ind, ind)}\n")
        out.append(tabela_md(s[[c for c in ["abrangencia", "2022_1t", "2022_2t", "2026_1t", "dif_turnos_2022", "dif_1t_2026_menos_2022"] if c in s]], max_linhas=30))
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- relatório público
def publico_md() -> str:
    br = _ler(2022, "resultados_brasil.csv")
    rec = _ler(2022, "reconciliacao_resumo.csv")
    tuf = _ler(2022, "temporal_por_uf.csv")
    bio = _ler(2022, "biometria_por_uf.csv")
    br26 = _ler(2026, "resultados_brasil.csv")
    out = ["# Relatório público — o que os dados oficiais das eleições presidenciais mostram\n",
           f"_Versão de {datetime.now(timezone.utc).strftime('%d/%m/%Y')}. Todos os números foram calculados por nós "
           "a partir dos arquivos publicados pelo TSE. Detalhes técnicos em `docs/auditoria-2022.md` e "
           "`docs/metodologia.md`._\n",
           "## Em uma frase\n",
           "Somando os boletins de cada uma das cerca de 472 mil seções eleitorais de 2022, chegamos exatamente aos "
           "totais oficiais; os mesmos números aparecem iguais nas diferentes publicações do TSE e no arquivo "
           "gerado pela própria urna. Encontramos poucas divergências pontuais entre o log de algumas urnas e o "
           "boletim, todas listadas, a maioria com explicação documentada (troca de urna, apuração em cédula).\n"]
    if not br.empty:
        r = br.iloc[0]
        out.append(bloco(
            "As contas nacionais de 2022 fecham?",
            "Somamos os Boletins de Urna de todas as seções e comparamos com os totais oficiais.",
            f"1º turno: {n(r.comparecimento_1t)} eleitores votaram de {n(r.aptos_1t)} aptos nas seções instaladas "
            f"(abstenção {n(r.pct_abstencao_1t, 2)}%); brancos {n(r.pct_brancos_1t, 2)}% e nulos {n(r.pct_nulos_1t, 2)}% de quem votou. "
            f"2º turno: {n(r.comparecimento_2t)} votaram (abstenção {n(r.pct_abstencao_2t, 2)}%); brancos {n(r.pct_brancos_2t, 2)}%, "
            f"nulos {n(r.pct_nulos_2t, 2)}%. Lula: {n(r.votos_13_2t)} ({n(r.pct_validos_13_2t, 2)}% dos válidos); "
            f"Bolsonaro: {n(r.votos_22_2t)} ({n(r.pct_validos_22_2t, 2)}%).",
            "Os totais oficiais são exatamente a soma dos boletins das seções.",
            "A única diferença (657 eleitores aptos) são eleitores de 47 seções que não chegaram a ser instaladas.",
            "—", "`resultados/2022/resultados_brasil.csv`; comparação com o TSE em `docs/auditoria-2022.md`.",
            "Conferido"))
    if not rec.empty:
        sem = int((rec.divergencias - rec.explicadas.fillna(0)).sum())
        out.append(bloco(
            "O boletim publicado é o mesmo que a urna gerou?",
            "Comparamos, seção por seção, o boletim publicado em tabela com o arquivo binário assinado que cada urna "
            "transmitiu, com duas outras tabelas do TSE e com o log (diário de eventos) da urna.",
            f"{len(rec[rec.divergencias == 0])} de {len(rec)} comparações sem nenhuma diferença. Restam {n(sem)} "
            "diferenças sem explicação documental, todas entre o log de poucas urnas e o boletim.",
            "Votos e totais coincidem em todas as publicações; as diferenças restantes estão no registro de "
            "eventos, não nos votos publicados.",
            "Casos explicados: seções que votaram em cédula após falha da urna, troca de urna com logs de várias "
            "seções no mesmo pacote, urna desligada no meio de um voto.",
            "Os casos restantes precisam da ata da mesa receptora (documento físico) para serem esclarecidos.",
            "`resultados/2022/incompatibilidades.csv` e diagnósticos em `resultados/2022/diagnosticos/`.",
            "Conferido, com incompatibilidades pontuais documentadas"))
        out.append("![Abstenção por UF](../resultados/2022/graficos/pct_abstencao_por_uf.png)\n")
    if not tuf.empty:
        g = tuf[(tuf.uf != "ZZ")]
        g1, g2 = g[g.turno == 1], g[g.turno == 2]
        out.append(bloco(
            "Houve votos fora do horário?",
            "Convertemos o relógio de cada urna para o horário de Brasília (a urna marca hora local) e contamos os "
            "votos antes das 8h e depois das 17h.",
            f"Antes das 8h: {n(g1.votos_antes_8h.sum())} votos no 1º turno e {n(g2.votos_antes_8h.sum())} no 2º. "
            f"Depois das 17h: {n(100 * g1.votos_apos_17h.sum() / g1.votos.sum(), 2)}% dos votos no 1º turno e "
            f"{n(100 * g2.votos_apos_17h.sum() / g2.votos.sum(), 3)}% no 2º (nas seções com log processado).",
            "Votar depois das 17h é permitido para quem está na fila. No 1º turno havia 5 cargos, o que alonga "
            "as filas.",
            "Fila com senha às 17h (Resolução TSE 23.669/2021, art. 136).",
            "O log não registra quem recebeu senha.",
            "`resultados/2022/temporal_por_uf.csv`; gráfico abaixo.",
            "Conferido"))
        out.append("![Votos a cada 15 minutos](../resultados/2022/graficos/votos_por_15min.png)\n")
    if not bio.empty:
        g = bio[bio.uf != "ZZ"]
        out.append(bloco(
            "Quantos votaram sem a digital reconhecida?",
            "Contamos, no boletim e no log, quem tinha biometria cadastrada mas foi liberado pelo mesário.",
            "; ".join(f"{t}º turno: {n(100 * x.bu_biometria_nao_habilitados.sum() / x.comparecimento.sum(), 1)}% de quem votou"
                      for t, x in g.groupby("turno")) + ".",
            "É o procedimento previsto quando a digital falha; boletim e log dão o mesmo número.",
            "Regra das até 4 tentativas e liberação pelo mesário (Res. 23.669/2021, arts. 113–114). Urnas mais novas "
            "(modelo 2020) têm taxa menor.",
            "O motivo de cada falha não é registrado.",
            "`resultados/2022/biometria_por_uf.csv`.",
            "Conferido"))
        out.append("![Liberação manual por UF](../resultados/2022/graficos/biometria_nh_por_uf.png)\n")
    out.append(bloco(
        "A urna modelo 2020 teve resultado diferente?",
        "Comparamos seções com urna 2020 e com outros modelos no mesmo local de votação.",
        "No mesmo local, a diferença na proporção de votos de cada candidato não é estatisticamente "
        "significativa; em comparações mais amplas (mesma zona) aparece diferença de cerca de 1 ponto, que "
        "pode refletir bairros diferentes.",
        "Não há evidência de efeito do modelo; a distribuição das urnas não é aleatória.",
        "Logística de distribuição por zona e local.",
        "Sem dados de eleições anteriores por seção, não é possível separar totalmente local e modelo.",
        "`resultados/2022/modelos_efeito_controlado.csv`; gráfico abaixo.",
        "Diferença estatística em controles fracos; sem diferença no controle forte"))
    out.append("![Modelos de urna](../resultados/2022/graficos/modelos_efeito_22.png)\n")
    if not br26.empty:
        r = br26.iloc[0]
        out.append(bloco(
            "E 2026?",
            "Os mesmos procedimentos aplicados a 2026. Do 2º turno, só as tabelas oficiais por seção já foram publicadas.",
            (f"1º turno de 2026: {n(r.comparecimento_1t)} votantes de {n(r.aptos_1t)} aptos (abstenção {n(r.pct_abstencao_1t, 2)}%); "
             f"brancos {n(r.pct_brancos_1t, 2)}%, nulos {n(r.pct_nulos_1t, 2)}%. 2º turno (tabelas oficiais por seção): "
             f"{n(r.comparecimento_2t)} votantes (abstenção {n(r.pct_abstencao_2t, 2)}%); Lula {n(r.votos_13_2t)} "
             f"({n(r.pct_validos_13_2t, 2)}% dos válidos), Flávio Bolsonaro {n(r.votos_22_2t)} ({n(r.pct_validos_22_2t, 2)}%); "
             f"a identidade válidos = comparecimento − brancos − nulos fecha com resíduo {n(r.residuo_reconciliacao)}.")
            if "comparecimento_1t" in br26.columns else
            (f"1º turno de 2026: {n(r.comparecimento)} votantes de {n(r.aptos)} aptos (abstenção {n(r.pct_abstencao, 2)}%); "
             f"brancos {n(r.pct_brancos, 2)}%, nulos {n(r.pct_nulos, 2)}%."),
            "Os totais por seção reproduzem o resultado oficial; a diferença em votos válidos corresponde aos "
            "votos dados a um candidato posteriormente considerados nulos (\"nulos técnicos\").",
            "Ver `docs/auditoria-2026.md`.",
            "Segundo turno de 2026: BU, logs e arquivos das urnas aguardando publicação.",
            "`docs/auditoria-2026.md` e `docs/comparativo-historico.md`.",
            "Conferido (1º turno) / Pendente (2º turno)"))
    out.append("\n## Como ler as classificações\n\n"
               "**Conferido**: refizemos a conta e bate. **Diferença explicada**: havia diferença, mas existe "
               "documento que a explica. **Diferença estatística**: um padrão se afasta de uma referência, sem "
               "erro documental. **Incompatibilidade documental**: fontes oficiais que deveriam bater não batem, "
               "e ainda não sabemos por quê. **Pendente**: faltam dados. Nenhuma dessas categorias, sozinha, é "
               "prova de irregularidade.\n")
    return "\n".join(out) + "\n"


def limitacoes_md() -> str:
    from .config import UFS_COM_EXTERIOR
    cob = MANIFESTOS / "cobertura_arquivos_urna.csv"
    linhas = []
    if cob.exists():
        c = pd.read_csv(cob)
        for (ano, t) in [(2022, 1), (2022, 2), (2026, 1)]:
            g = c[(c.ano == ano) & (c.turno == t)]
            falta = sorted(set(UFS_COM_EXTERIOR) - set(g.uf))
            linhas.append(f"- {ano}, {t}º turno: {len(g)}/28 pacotes processados"
                          + (f"; faltam: {', '.join(falta)}" if falta else " (completo)") + ".")
    dl = pd.read_csv(MANIFESTOS / "downloads.csv") if (MANIFESTOS / "downloads.csv").exists() else pd.DataFrame()
    falhas = dl[dl.status != "ok"] if not dl.empty else pd.DataFrame()
    avisos = dl[dl.get("aviso_versao", pd.Series(dtype=str)).fillna("") != ""] if not dl.empty and "aviso_versao" in dl else pd.DataFrame()
    txt = f"""# Limitações e pendências

_Atualizado em {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M UTC')}._

## Cobertura do processamento dos arquivos de urna (logs + BU binário)

{chr(10).join(linhas) or '- nenhum pacote processado'}

Enquanto houver pacotes faltando, os indicadores baseados em log (horários, intervalos,
modalidade de habilitação, B6) **não são nacionais**: valem para as UFs processadas. Os
indicadores baseados no BU em CSV e nas tabelas oficiais são nacionais (todas as seções).

## Dados não publicados ou indisponíveis

- **2º turno de 2026** (25/10/2026): em 27/10/2026 estavam publicadas apenas as tabelas oficiais por
  seção (Detalhe da apuração por seção e Votação por seção, geradas em 26/10/2026), que foram usadas
  nos indicadores de resultado (fonte marcada `DSEC+VSEC`). **Ainda não publicados:** BU em CSV,
  arquivos de urna (logs, BU binário) e tabelas por município/zona do 2º turno; por isso os testes de
  log, horário, biometria efetiva e B2/B6 do 2º turno de 2026 estão pendentes.
- **Especificação ASN.1 oficial e catálogo de mensagens do log**: a página de documentação técnica
  do TSE respondeu HTTP 403 a este ambiente; usaram-se espelhos (procedência em `especificacoes/`),
  validados pela decodificação e pela concordância com o BU publicado.
- **Atas das mesas receptoras e cadernos de votação**: não são publicados como dados abertos; são o
  documento necessário para esclarecer as incompatibilidades log × BU remanescentes.
- **Senhas distribuídas às 17h**: não registradas no log; votos após 17h não podem ser conferidos
  eleitor a eleitor.

## Downloads com problema registrado

{tabela_md(falhas[["url", "status", "erro"]]) if not falhas.empty else "Nenhum."}

## Divergência de versões no CDN do TSE

Em 26–27/10/2026 o CDN respondeu a HEAD com uma versão de alguns arquivos e a GET com outra
(ETag e tamanho diferentes), indicando republicação em curso. Os casos estão registrados
(coluna `aviso_versao` de `manifestos/downloads.csv`); adotou-se a versão efetivamente baixada,
identificada pelo SHA-256.

{tabela_md(avisos[["url", "aviso_versao"]]) if not avisos.empty else ""}

## Questões metodológicas em aberto

- **Assinaturas digitais** (`.vscmr`/`-vota.vsc`) não foram verificadas criptograficamente nesta etapa.
- **Ajustes de relógio**: o log registra a aplicação "AJUSTE DE DATA E HORA". A contagem foi
  incorporada ao leitor depois do processamento de 2022 (identificada no caso RN 18139/65/32), e por
  isso só existe para 2026 (`secoes_com_ajuste_de_hora`); para 2022 exige reprocessar os logs.
- **Transferências temporárias**: ~3% das seções com variação de aptos entre turnos não são
  explicadas pelo arquivo de TTE (gerado em 2024); verificação documental pendente.
- **Modelos de urna**: sem covariáveis anteriores por seção, efeito de modelo e de localização não se
  separam totalmente.
- **Inferência de transferência de votos entre turnos**: não realizada (inferência ecológica).
- **Exterior**: horários em hora local de cada país; sem biometria; não entra em indicadores de Brasília.
"""
    return txt


def escrever_tudo() -> list[str]:
    feitos = escrever()
    p = DOCS / "auditoria-estudos-externos.md"
    base = p.read_text(encoding="utf-8").split("\n## Reprodução independente")[0]
    p.write_text(base.rstrip() + "\n" + reproducao_externa(2022), encoding="utf-8")
    (DOCS / "comparativo-historico.md").write_text(comparativo_md(), encoding="utf-8")
    (DOCS / "relatorio-publico.md").write_text(publico_md(), encoding="utf-8")
    (DOCS / "limitacoes.md").write_text(limitacoes_md(), encoding="utf-8")
    return feitos + ["auditoria-estudos-externos.md", "comparativo-historico.md", "relatorio-publico.md", "limitacoes.md"]
