"""Executa todas as análises de um ano a partir dos dados já baixados/processados.

Uso: python scripts/executar_analises.py ANO [--sem-oficiais]
Etapas (cada uma registra o próprio resultado; falha de uma não interrompe as demais):
  oficiais -> bweb -> bu binário -> reconciliação -> resultados -> temporais ->
  rajadas -> biometria -> modelos -> estatística -> diagnósticos -> gráficos
"""
import subprocess
import sys
import traceback

sys.path.insert(0, ".")
from observatorio import (bweb, biometria, estatistica, graficos, modelos, oficiais,  # noqa: E402
                          reconciliacao, resultados_eleitorais, temporal)
from observatorio.config import PROCESSADOS, RESULTADOS  # noqa: E402

ano = int(sys.argv[1])
(RESULTADOS / str(ano)).mkdir(parents=True, exist_ok=True)


def etapa(nome, f):
    print(f"== {nome}", flush=True)
    try:
        r = f()
        print("   ok", (str(r)[:300] if r is not None else ""), flush=True)
    except Exception:
        print("   ERRO", traceback.format_exc()[-1500:], flush=True)


T = PROCESSADOS / "tabelas"
if "--sem-oficiais" not in sys.argv:
    for nome, f in (("detalhe_secao", oficiais.detalhe_secao), ("detalhe_munzona", oficiais.detalhe_munzona),
                    ("candidato_munzona", oficiais.candidato_munzona), ("votacao_secao", oficiais.votacao_secao),
                    ("perfil_secao", oficiais.perfil_secao)):
        alvo = T / (f"{nome}_{ano}.parquet" if nome not in ("votacao_secao", "perfil_secao") else nome)
        if nome in ("votacao_secao", "perfil_secao"):
            existe = alvo.exists() and any(alvo.glob(f"{ano}_*.parquet"))
        else:
            existe = alvo.exists()
        if not existe:
            etapa(f"oficiais.{nome}", lambda f=f: f(ano))
    if ano == 2022 and not (T / "secoes_agregadas_2022.parquet").exists():
        etapa("oficiais.secoes_agregadas", lambda: oficiais.secoes_agregadas(ano))
etapa("bweb.consolidar", lambda: bweb.consolidar(ano))
etapa("bu binário", lambda: subprocess.run([sys.executable, "scripts/decodificar_bus.py"], check=True).returncode)
etapa("reconciliação", lambda: reconciliacao.executar(ano)["resumo"].divergencias.sum())
etapa("resultados eleitorais", lambda: resultados_eleitorais.executar(ano))
if ano == 2022:
    etapa("aptos x TTE", lambda: resultados_eleitorais.aptos_vs_transferencias(ano))
etapa("temporal", lambda: temporal.tabelas(ano))
etapa("rajadas (votos)", lambda: len(temporal.rajadas(ano, "votos_s")))
etapa("rajadas (habilitações)", lambda: len(temporal.rajadas(ano, "hab_s")))
etapa("biometria", lambda: biometria.executar(ano)["ok"])
etapa("modelos", lambda: len(modelos.executar(ano)))
etapa("estatística", lambda: len(estatistica.executar(ano)))
etapa("diagnósticos", lambda: subprocess.run([sys.executable, "scripts/diagnosticar_incompatibilidades.py", str(ano)],
                                              check=True).returncode)
etapa("gráficos", lambda: graficos.gerar(ano))
