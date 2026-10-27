"""Triagem estatística, NÃO determinação de fraude ou de votos irregulares.

Opera somente em agregados por seção, a partir de BU-CSV ou DSEC+VSEC do TSE.
Não infere votos individuais; não compara pessoas/eleitores entre turnos.
Execução: python scripts/gerar_triagem_secoes.py --ano 2022 --ano 2026
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .config import PROCESSADOS, RESULTADOS, UFS_COM_EXTERIOR

TESTES = {
    "concentracao90": ("Candidato com 90% ou mais dos válidos", "Pelo menos 100 votos válidos na seção"),
    "concentracao95": ("Candidato com 95% ou mais dos válidos", "Pelo menos 100 votos válidos na seção"),
    "unanimidade": ("100% dos votos válidos para um candidato", "Inclui seções pequenas, identificadas pelo tamanho"),
    "pares25": ("Diferença de 25 p.p. ou mais frente às seções pares", "Mesmo local (preferencial) ou zona, nunca referência nacional"),
    "mudanca20": ("Mudança de 20 p.p. ou mais entre turnos", "Somente seções com bases comparáveis"),
    "mudanca30": ("Mudança de 30 p.p. ou mais entre turnos", "Somente seções com bases comparáveis"),
    "mudanca40": ("Mudança de 40 p.p. ou mais entre turnos", "Somente seções com bases comparáveis"),
    "virada13_22": ("Inversão da liderança relativa entre 13 e 22", "Não equivale necessariamente à troca do vencedor geral do 1º turno"),
    "comparecimento20": ("Mudança de 20 p.p. ou mais no comparecimento", "Aptos e local de votação devem ser comparáveis"),
    "brancos_nulos15": ("Mudança de 15 p.p. ou mais em brancos+nulos", "Base: votantes, não eleitores aptos"),
    "combinados": ("Dois ou mais grupos distintos de indicadores", "Triagem prioritária, não escore de fraude"),
    "qualquer": ("União de seções sinalizadas", "Cada seção contabilizada uma única vez neste teste"),
}
# Mínimo de votos válidos em testes de participação; 'unanimidade' não possui mínimo.
MIN_VALIDOS = 100
MIN_PARES_LOCAL = 2
MIN_VALIDOS_PARES_LOCAL = 200
MIN_PARES_ZONA = 5
MIN_VALIDOS_PARES_ZONA = 1000

@dataclass(frozen=True)
class Secao:
    turno: int
    uf: str
    municipio: int
    nome: str
    zona: int
    local: int
    secao: int
    aptos: int
    comparecimento: int
    validos: int
    brancos: int
    nulos: int
    votos_candidato: dict[int, int]
    fonte: str

    @property
    def chave(self):
        return (self.uf, self.municipio, self.zona, self.secao)

    def share(self, candidato: int) -> float | None:
        if self.validos <= 0:
            return None
        return 100 * self.votos_candidato.get(candidato, 0) / self.validos

    @property
    def comparecimento_pct(self) -> float | None:
        return 100 * self.comparecimento / self.aptos if self.aptos else None

    @property
    def brancos_nulos_pct(self) -> float | None:
        return 100 * (self.brancos + self.nulos) / self.comparecimento if self.comparecimento else None

    @property
    def max_candidato(self):
        return max(self.votos_candidato.items(), key=lambda item: (item[1], -item[0]), default=(None, 0))


def dados_confiaveis(s: Secao) -> bool:
    return (s.aptos >= s.comparecimento >= 0 and s.validos >= 0 and
            s.brancos >= 0 and s.nulos >= 0 and
            s.validos + s.brancos + s.nulos == s.comparecimento and
            sum(s.votos_candidato.values()) == s.validos)


def comparavel(s: Secao, anterior: Secao | None) -> bool:
    """Heurística de base estável; não é prova de eleitorado idêntico."""
    if anterior is None or s.turno != 2 or s.validos < MIN_VALIDOS or anterior.validos < MIN_VALIDOS:
        return False
    if s.aptos <= 0 or anterior.aptos <= 0 or s.local <= 0 or anterior.local <= 0:
        return False
    if s.local != anterior.local:
        return False
    return abs(s.aptos - anterior.aptos) <= max(10, .05 * max(s.aptos, anterior.aptos))


def obter_pares(s: Secao, por_local: dict, por_zona: dict) -> tuple[list[Secao], str]:
    if s.local > 0:
        local = [x for x in por_local.get((s.turno, s.uf, s.municipio, s.zona, s.local), ()) if x.chave != s.chave]
        if len(local) >= MIN_PARES_LOCAL and sum(x.validos for x in local) >= MIN_VALIDOS_PARES_LOCAL:
            return local, "mesmo_local"
    zona = [x for x in por_zona.get((s.turno, s.uf, s.municipio, s.zona), ()) if x.chave != s.chave]
    if len(zona) >= MIN_PARES_ZONA and sum(x.validos for x in zona) >= MIN_VALIDOS_PARES_ZONA:
        return zona, "mesma_zona"
    return [], "indisponivel"


def triagem_secao(s: Secao, anterior: Secao | None, pares: list[Secao], referencia: str) -> tuple[dict[str, float], dict]:
    """Retorna magnitudes de triagem, sem alegação causal ou p-valor."""
    saida = {}
    lider, max_votos = s.max_candidato
    concentracao = 100 * max_votos / s.validos if s.validos else None
    if s.validos >= MIN_VALIDOS and concentracao is not None:
        for nome, limite in (("concentracao90", 90), ("concentracao95", 95)):
            if concentracao >= limite:
                saida[nome] = concentracao
    if s.validos > 0 and max_votos == s.validos:
        saida["unanimidade"] = concentracao

    share13, share22 = s.share(13), s.share(22)
    peer_delta = None
    if s.validos >= MIN_VALIDOS and pares:
        den = sum(p.validos for p in pares)
        if den:
            peer_delta = max(abs(share13 - 100 * sum(p.votos_candidato.get(13, 0) for p in pares)/den),
                             abs(share22 - 100 * sum(p.votos_candidato.get(22, 0) for p in pares)/den))
            if peer_delta >= 25:
                saida["pares25"] = peer_delta

    d13 = d22 = dcomparecimento = dbn = None
    base_comparavel = comparavel(s, anterior)
    if base_comparavel:
        d13, d22 = share13 - anterior.share(13), share22 - anterior.share(22)
        maior = max(abs(d13), abs(d22))
        for nome, limite in (("mudanca20", 20), ("mudanca30", 30), ("mudanca40", 40)):
            if maior >= limite:
                saida[nome] = maior
        antes = anterior.votos_candidato.get(13, 0) - anterior.votos_candidato.get(22, 0)
        depois = s.votos_candidato.get(13, 0) - s.votos_candidato.get(22, 0)
        if antes * depois < 0:
            saida["virada13_22"] = maior
        dcomparecimento = s.comparecimento_pct - anterior.comparecimento_pct
        dbn = s.brancos_nulos_pct - anterior.brancos_nulos_pct
        if abs(dcomparecimento) >= 20:
            saida["comparecimento20"] = abs(dcomparecimento)
        if abs(dbn) >= 15:
            saida["brancos_nulos15"] = abs(dbn)

    grupos = sum((bool("pares25" in saida),
                  any(k in saida for k in ("mudanca20", "mudanca30", "mudanca40", "virada13_22")),
                  "comparecimento20" in saida,
                  "brancos_nulos15" in saida))
    if grupos >= 2:
        saida["combinados"] = float(grupos)
    if saida:
        saida["qualquer"] = float(len(saida))
    contexto = {
        "candidato_mais_votado": lider,
        "pct_mais_votado": concentracao,
        "pct_13": share13, "pct_22": share22,
        "pct_13_1t": anterior.share(13) if anterior else None,
        "pct_22_1t": anterior.share(22) if anterior else None,
        "delta_13_pp": d13, "delta_22_pp": d22,
        "delta_comparecimento_pp": dcomparecimento, "delta_brancos_nulos_pp": dbn,
        "desvio_pares_pp": peer_delta, "referencia_pares": referencia,
        "comparacao_entre_turnos_aplicavel": base_comparavel,
        "variacao_aptos": s.aptos - anterior.aptos if anterior else None,
    }
    return saida, contexto


def linhas_de_triagem(secoes: list[Secao]):
    """Função pura: permite testes sintéticos sem download nem manipulação de eleição."""
    unicas = {}
    invalidas = 0
    for s in secoes:
        chave = (s.turno, s.chave)
        if chave in unicas:
            raise ValueError(f"Seção duplicada (UF, município, zona, seção, turno): {chave}")
        if not dados_confiaveis(s):
            invalidas += 1
            continue
        unicas[chave] = s
    por_local, por_zona = defaultdict(list), defaultdict(list)
    for s in unicas.values():
        por_local[(s.turno, s.uf, s.municipio, s.zona, s.local)].append(s)
        por_zona[(s.turno, s.uf, s.municipio, s.zona)].append(s)
    out = []
    for s in unicas.values():
        old = unicas.get((1, s.chave)) if s.turno == 2 else None
        pares, referencia = obter_pares(s, por_local, por_zona)
        flags, ctx = triagem_secao(s, old, pares, referencia)
        out.append((s, flags, ctx))
    return out, invalidas


def _resumir(ano: int, registros, ano_turnos: dict, max_exemplos: int):
    resumo = []
    exemplos = []
    # Para BR há também votos do exterior; percentuais referem-se às seções, não aos votos suspeitos.
    for turno in sorted(ano_turnos):
        mesmo_turno = [x for x in registros if x[0].turno == turno]
        for uf in ["BR"] + UFS_COM_EXTERIOR:
            grupo = mesmo_turno if uf == "BR" else [x for x in mesmo_turno if x[0].uf == uf]
            if not grupo:
                continue
            total_validos = sum(s.validos for s, _, _ in grupo)
            fonte = ano_turnos[turno]
            for teste, (titulo, regra) in TESTES.items():
                elegiveis = [x for x in grupo if
                             (x[0].validos > 0 if teste in ("unanimidade", "qualquer") else
                              x[0].validos >= MIN_VALIDOS)
                             and (teste != "pares25" or x[2]["referencia_pares"] != "indisponivel")
                             and (teste not in {"mudanca20", "mudanca30", "mudanca40", "virada13_22",
                                               "comparecimento20", "brancos_nulos15", "combinados"}
                                  or x[2]["comparacao_entre_turnos_aplicavel"])]
                destacados = [x for x in grupo if teste in x[1]]
                votos_dest = sum(s.validos for s, _, _ in destacados)
                resumo.append({
                    "ano": ano, "turno": turno, "uf": uf, "teste": teste,
                    "descricao": titulo, "criterio": regra, "fonte": fonte,
                    "secoes_com_dados": len(grupo), "secoes_elegiveis": len(elegiveis),
                    "secoes_sinalizadas": len(destacados),
                    "pct_secoes_sinalizadas": round(100 * len(destacados)/len(elegiveis), 4) if elegiveis else None,
                    "votos_validos_no_recorte": total_validos,
                    "votos_validos_em_secoes_sinalizadas": votos_dest,
                    "pct_validos_em_secoes_sinalizadas": round(100*votos_dest/total_validos,4) if total_validos else None,
                    "cobertura": "agregado_por_secao; nao_equivale_a_votos_irregulares"
                })
                destacados.sort(key=lambda x: (x[1][teste], x[0].validos, x[0].chave), reverse=True)
                for s, flags, ctx in destacados[:max_exemplos]:
                    r = {"ano": ano, "turno": turno, "abrangencia": uf,
                         "uf": s.uf, "municipio": s.municipio, "nome_municipio": s.nome,
                         "zona": s.zona, "local": s.local, "secao": s.secao,
                         "teste": teste, "intensidade": round(flags[teste], 4),
                         "validos": s.validos, "comparecimento": s.comparecimento,
                         "aptos": s.aptos, "brancos_nulos": s.brancos+s.nulos}
                    r.update({k: round(v, 4) if isinstance(v, float) else v for k,v in ctx.items()})
                    exemplos.append(r)
    return resumo, exemplos


def _fontes(con, ano, pasta: Path):
    bweb = pasta / f"secoes_bu_{ano}.parquet"
    if not bweb.exists():
        raise FileNotFoundError(f"Sem dados por seção: {bweb}")
    turnos_bu = {int(x[0]) for x in con.execute(f"SELECT DISTINCT turno FROM read_parquet('{bweb}')").fetchall()}
    fontes = {}
    for turno in (1, 2):
        oficial = pasta / f"secoes_oficiais_{ano}_{turno}t.parquet"
        if turno in turnos_bu:
            fontes[turno] = (bweb, "BU-CSV")
        elif oficial.exists():
            fontes[turno] = (oficial, "DSEC+VSEC")
    return fontes


def executar(ano: int, max_exemplos: int = 15, processados: Path | None = None,
             resultados: Path | None = None) -> dict:
    """Recalcula dados estatísticos locais; não baixa arquivos nem modifica a main."""
    if ano not in (2022, 2026):
        raise ValueError("Ano permitido: 2022 ou 2026")
    if max_exemplos < 1 or max_exemplos > 50:
        raise ValueError("max_exemplos entre 1 e 50")
    import duckdb
    processados = Path(processados or PROCESSADOS)
    resultados = Path(resultados or RESULTADOS) / str(ano)
    con = duckdb.connect()
    fontes = _fontes(con, ano, processados)
    if not fontes:
        raise FileNotFoundError("Nenhum turno publicado")
    # Agregar incrementalmente por UF: jamais manter ~1 milhão de dicionários na memória.
    agregado = {}
    ranking = defaultdict(list)
    invalidas = 0
    incluidas = 0
    info = {}
    for uf in UFS_COM_EXTERIOR:
        secoes = []
        for turno, (caminho, fonte) in fontes.items():
            linhas = con.execute(f"""SELECT turno, uf, cd_municipio, nm_municipio, nr_zona,
                nr_local_votacao, nr_secao, qt_aptos, qt_comparecimento,
                votos_nominais, votos_brancos, votos_nulos, votos_candidato
                FROM read_parquet('{caminho}') WHERE turno = ? AND uf = ?""",
                [turno, uf]).fetchall()
            for row in linhas:
                t,u,mun,nome,zona,local,sec,aptos,comp,valid,branco,nulo,mapa = row
                candidato = {int(k): int(v) for k,v in (mapa or {}).items() if v is not None}
                secoes.append(Secao(int(t),str(u),int(mun),str(nome or ''),
                                     int(zona),int(local or 0),int(sec),int(aptos or 0),
                                     int(comp or 0),int(valid or 0),int(branco or 0),int(nulo or 0),
                                     candidato,fonte))
        if not secoes:
            continue
        amostra, excluidas = linhas_de_triagem(secoes)
        invalidas += excluidas
        incluidas += len(amostra)
        info[uf] = {"secoes_processadas": len(amostra), "secoes_quarentena": excluidas}
        parcial, amostras = _resumir(ano, amostra, {t:fonte for t,(path,fonte) in fontes.items()}, max_exemplos)
        for linha in parcial:
            chave=(linha["turno"],linha["uf"],linha["teste"])
            if chave not in agregado:
                agregado[chave]=dict(linha)
            else:
                target=agregado[chave]
                for campo in ("secoes_com_dados","secoes_elegiveis","secoes_sinalizadas",
                              "votos_validos_no_recorte","votos_validos_em_secoes_sinalizadas"):
                    target[campo] += linha[campo]
        for ex in amostras:
            chave=(ex["turno"],ex["abrangencia"],ex["teste"])
            ranking[chave].append(ex)
            ranking[chave].sort(key=lambda x: (x["intensidade"],x["validos"],x["uf"],x["secao"]), reverse=True)
            del ranking[chave][max_exemplos:]
        # Descarta as seções deste estado antes de seguir para o próximo.
        del amostra, secoes, parcial, amostras
    con.close()
    result=list(agregado.values())
    for linha in result:
        sinal=linha["secoes_sinalizadas"]
        elig=linha["secoes_elegiveis"]
        total=linha["votos_validos_no_recorte"]
        votos=linha["votos_validos_em_secoes_sinalizadas"]
        linha["pct_secoes_sinalizadas"]=round(100*sinal/elig,4) if elig else None
        linha["pct_validos_em_secoes_sinalizadas"]=round(100*votos/total,4) if total else None
    result.sort(key=lambda r: (r["turno"],r["uf"],r["teste"]))
    exemplos=[x for grupo in ranking.values() for x in grupo]
    exemplos.sort(key=lambda r:(r["turno"],r["abrangencia"],r["teste"],-r["intensidade"]))
    resultados.mkdir(parents=True, exist_ok=True)
    def gravar_csv(nome, linhas):
        destino = resultados / nome
        if not linhas:
            return
        with destino.open('w',encoding='utf-8',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(linhas[0]))
            writer.writeheader()
            writer.writerows(linhas)
    gravar_csv('triagem_secoes_resumo.csv',result)
    gravar_csv('triagem_secoes_exemplos.csv',exemplos)
    meta = {"ano":ano,"gerado_utc":datetime.now(timezone.utc).isoformat(),
            "fontes_por_turno": {str(t):fonte for t,(p,fonte) in fontes.items()},
            "cobertura_por_uf":info,"ufs_ausentes":[uf for uf in UFS_COM_EXTERIOR if uf not in info],
            "secoes_incluidas":incluidas,
            "secoes_excluidas_por_inconsistencia":invalidas,
            "criterios":"docs/triagem-secoes.md",
            "aviso":"Seção destacada NÃO significa voto irregular; votos nos recortes NÃO são votos afetados."}
    (resultados/'triagem_secoes_metadados.json').write_text(
        json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    return meta


def main():
    parser=argparse.ArgumentParser(description="Triagem exploratória por seção, baseada nos dados oficiais")
    parser.add_argument("--ano",type=int,action="append",choices=(2022,2026),required=True)
    parser.add_argument("--max-exemplos",type=int,default=15)
    args=parser.parse_args()
    for ano in sorted(set(args.ano)):
        print(json.dumps(executar(ano,max_exemplos=args.max_exemplos),ensure_ascii=False))


if __name__ == "__main__":
    main()
