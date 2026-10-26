"""Decodificação dos arquivos .bu (Boletim de Urna binário, ASN.1/BER).

Especificação: especificacoes/asn1_2022/bu.asn1 (ver PROCEDENCIA.md).
Estrutura: EntidadeEnvelopeGenerico{conteudo} -> EntidadeBoletimUrna.
"""
from __future__ import annotations

from functools import lru_cache

import asn1tools

from .config import RAIZ

SPECS = {2022: RAIZ / "especificacoes" / "asn1_2022" / "bu.asn1",
         2026: RAIZ / "especificacoes" / "asn1_2026" / "bu.asn1"}


@lru_cache(maxsize=4)
def _conv(ano: int = 2022):
    return asn1tools.compile_files([str(SPECS[ano])], codec="ber")


def _str(v):
    return v[1] if isinstance(v, tuple) else v


def decodificar(dados: bytes, ano: int = 2022) -> dict:
    """Retorna um resumo plano do BU, apenas com o cargo Presidente detalhado."""
    c = _conv(ano)
    env = c.decode("EntidadeEnvelopeGenerico", dados)
    bu = c.decode("EntidadeBoletimUrna", env["conteudo"])
    urna = bu.get("urna", {})
    corr = urna.get("correspondenciaResultado", {})
    carga = corr.get("carga", {})
    sec = bu.get("identificacaoSecao", {})
    out = {
        "bu_fase": _str(bu.get("fase")),
        "bu_tipo_urna": _str(urna.get("tipoUrna")),
        "bu_numero_serie_fv": urna.get("numeroSerieFV", b"").hex() if isinstance(urna.get("numeroSerieFV"), (bytes, bytearray)) else str(urna.get("numeroSerieFV", "")),
        "bu_tipo_arquivo": _str(urna.get("tipoArquivo")),
        "bu_numero_interno_urna": carga.get("numeroInternoUrna"),
        "bu_codigo_carga": str(carga.get("codigoCarga", "")),
        "bu_data_hora_carga": str(carga.get("dataHoraCarga", "")),
        "bu_municipio": sec.get("municipioZona", {}).get("municipio"),
        "bu_zona": sec.get("municipioZona", {}).get("zona"),
        "bu_local": sec.get("local"),
        "bu_secao": sec.get("secao"),
        "bu_data_hora_emissao": str(bu.get("dataHoraEmissao", "")),
        "bu_qtd_lib_codigo": bu.get("qtdEleitoresLibCodigo"),
        "bu_qtd_comp_biometrico": bu.get("qtdEleitoresCompBiometrico"),
        "bu_n_historico_correspondencias": len(bu.get("historicoCorrespondencias", []) or []),
    }
    if ano >= 2026:
        det = bu.get("detalhamentoComparecimento") or {}
        out.update(
            bu_qtd_compareceram=bu.get("qtdEleitoresCompareceram"),
            bu_qtd_sem_biometria=det.get("qtdEleitoresCompareceramSemBiometria"),
            bu_qtd_hab_biometria=det.get("qtdEleitoresHabilitadosPorBiometria"),
            bu_qtd_hab_biografia=det.get("qtdEleitoresHabilitadosPorBiografia"),
            bu_n_historico_codigos_carga=len(bu.get("historicoCodigosCarga") or []),
            bu_versao_votacao=urna.get("versaoVotacao"),
        )
    dados_sa = bu.get("dadosSecaoSA")
    if isinstance(dados_sa, tuple):
        out["bu_dados_secao_sa"] = dados_sa[0]
        if isinstance(dados_sa[1], dict):
            out["bu_data_hora_abertura"] = str(dados_sa[1].get("dataHoraAbertura", ""))
            out["bu_data_hora_encerramento"] = str(dados_sa[1].get("dataHoraEncerramento", ""))
    for el in bu.get("resultadosVotacaoPorEleicao", []):
        for rv in el.get("resultadosVotacao", []):
            for tc in rv.get("totaisVotosCargo", []):
                cargo = tc.get("codigoCargo")
                cargo = cargo[1] if isinstance(cargo, tuple) else cargo
                if cargo != "presidente":
                    continue
                out["bu_id_eleicao"] = el.get("idEleicao")
                out["bu_qtd_aptos"] = el.get("qtdEleitoresAptos")
                out["bu_qtd_aptos_secao"] = el.get("qtdEleitoresAptosSecao")
                out["bu_qtd_aptos_tte"] = el.get("qtdEleitoresAptosTTE")
                out["bu_qtd_comparecimento"] = rv.get("qtdComparecimento")
                votos = {}
                brancos = nulos = nominais = outros = 0
                for vv in tc.get("votosVotaveis", []):
                    tipo = _str(vv.get("tipoVoto"))
                    q = vv.get("quantidadeVotos", 0)
                    if tipo == "nominal":
                        cod = vv.get("identificacaoVotavel", {}).get("codigo")
                        votos[int(cod)] = votos.get(int(cod), 0) + q
                        nominais += q
                    elif tipo == "branco":
                        brancos += q
                    elif tipo == "nulo":
                        nulos += q
                    else:
                        outros += q
                out.update(bu_votos_nominais=nominais, bu_votos_brancos=brancos, bu_votos_nulos=nulos,
                           bu_votos_outros=outros, bu_votos_candidato=votos)
    return out


def decodificar_zip(caminho_zip, saida_parquet, ano: int | None = None) -> int:
    """Decodifica todos os .bu de um ZIP local e grava Parquet (uma linha por seção)."""
    import zipfile

    import pyarrow as pa
    import pyarrow.parquet as pq

    if ano is None:
        ano = int(str(caminho_zip).rsplit("/", 1)[-1][:4])
    linhas = []
    with zipfile.ZipFile(caminho_zip) as z:
        for n in z.namelist():
            base = {"arquivo": n.rsplit(".", 1)[0]}
            try:
                d = decodificar(z.read(n), ano)
                d["bu_votos_candidato"] = [{"k": k, "v": v} for k, v in d.get("bu_votos_candidato", {}).items()]
                linhas.append({**base, **d, "erro_bu": ""})
            except Exception as e:  # registra erro real, sem descartar a seção
                linhas.append({**base, "erro_bu": repr(e)[:300]})
    saida_parquet.parent.mkdir(parents=True, exist_ok=True)
    chaves = list(dict.fromkeys(k for l in linhas for k in l))  # união das chaves
    pq.write_table(pa.Table.from_pylist([{k: l.get(k) for k in chaves} for l in linhas]),
                   saida_parquet, compression="zstd")
    return len(linhas)
