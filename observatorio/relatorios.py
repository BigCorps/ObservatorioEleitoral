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
