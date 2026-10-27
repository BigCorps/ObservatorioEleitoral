"""Gráficos estáticos (PNG) para os relatórios. Cada gráfico informa escala, unidade,
denominador e cobertura no título/rodapé. Paleta categórica de referência validada
(azul = 1º turno, laranja = 2º turno); sequencial em um único matiz."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from .config import RESULTADOS  # noqa: E402

COR = {1: "#2a78d6", 2: "#eb6834"}
# codificação secundária (o par azul/laranja fica na faixa 6–8 de ΔE para daltonismo)
LS = {1: "-", 2: "--"}
MK = {1: "o", 2: "s"}
TXT, TXT2, GRADE = "#0b0b0b", "#52514e", "#e4e3df"


def _estilo(ax, titulo, xl, yl, fonte):
    ax.set_title(titulo, loc="left", fontsize=11, color=TXT)
    ax.set_xlabel(xl, color=TXT2, fontsize=9)
    ax.set_ylabel(yl, color=TXT2, fontsize=9)
    ax.grid(axis="y", color=GRADE, linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRADE)
    ax.tick_params(colors=TXT2, labelsize=8)
    ax.figure.text(0.01, 0.01, fonte, fontsize=7, color=TXT2)


def _salvar(fig, pasta, nome):
    pasta.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(pasta / nome, dpi=130, facecolor="#fcfcfb")
    plt.close(fig)


def gerar(ano: int, cobertura_txt: str = "") -> list[str]:
    r = RESULTADOS / str(ano)
    g = r / "graficos"
    feitos = []
    fonte = f"Fonte: TSE, dados abertos {ano}; cálculo próprio (Observatório Eleitoral). {cobertura_txt}"
    # 1. Votos por faixa de 15 minutos (horário de Brasília)
    f = r / "votos_por_15min.csv"
    if f.exists():
        d = pd.read_csv(f)
        d = d[d.abrangencia.str.startswith("BR")]
        fig, ax = plt.subplots(figsize=(9, 4))
        for t, sub in d.groupby("turno"):
            ax.plot(sub.minuto_do_dia / 60, 100 * sub.votos / sub.votos.sum(), color=COR[t], lw=2, ls=LS[t],
                    label=f"{t}º turno (n = {sub.votos.sum():,.0f} votos)".replace(",", "."))
        ax.axvline(8, color=TXT2, lw=0.8, ls=":")
        ax.axvline(17, color=TXT2, lw=0.8, ls=":")
        ax.set_xlim(5, 21)
        ax.legend(frameon=False, fontsize=8)
        _estilo(ax, "Votos registrados no log por faixa de 15 min (horário de Brasília)",
                "hora (Brasília)", "% dos votos do turno", fonte)
        _salvar(fig, g, "votos_por_15min.png")
        feitos.append("votos_por_15min.png")
    # 2. Abstenção, brancos e nulos por UF
    f = r / "resultados_uf.csv"
    if f.exists():
        d = pd.read_csv(f).sort_values("pct_abstencao_1t")
        for col, nome in (("pct_abstencao", "abstenção (% dos aptos)"), ("pct_brancos_nulos", "brancos + nulos (% do comparecimento)")):
            fig, ax = plt.subplots(figsize=(7, 7))
            y = range(len(d))
            ax.scatter(d[f"{col}_1t"], y, color=COR[1], s=30, label="1º turno", zorder=3)
            ax.scatter(d[f"{col}_2t"], y, color=COR[2], marker="s", s=30, label="2º turno", zorder=3)
            ax.set_yticks(list(y), d.uf)
            ax.legend(frameon=False, fontsize=8)
            _estilo(ax, f"Presidente {ano}: {nome}, por UF", "%", "", fonte)
            ax.grid(axis="x", color=GRADE)
            _salvar(fig, g, f"{col}_por_uf.png")
            feitos.append(f"{col}_por_uf.png")
    # 3. Intervalos entre votos consecutivos
    f = r / "distribuicao_intervalos.csv"
    if f.exists():
        d = pd.read_csv(f)
        fig, ax = plt.subplots(figsize=(9, 4))
        for t, sub in d.groupby("turno"):
            sub = sub[sub.intervalo_s_truncado_600 <= 300]
            ax.plot(sub.intervalo_s_truncado_600, 100 * sub.n / d[d.turno == t].n.sum(), color=COR[t], lw=2, ls=LS[t], label=f"{t}º turno")
        ax.legend(frameon=False, fontsize=8)
        _estilo(ax, "Intervalo entre votos consecutivos na mesma urna", "segundos (até 300)", "% dos intervalos", fonte)
        _salvar(fig, g, "intervalos_entre_votos.png")
        feitos.append("intervalos_entre_votos.png")
    # 4. Biometria: liberação manual por UF
    f = r / "biometria_por_uf.csv"
    if f.exists():
        d = pd.read_csv(f)
        d = d[d.uf != "ZZ"].pivot(index="uf", columns="turno", values="pct_bu_nh_sobre_comparecimento").sort_values(1)
        fig, ax = plt.subplots(figsize=(7, 7))
        y = range(len(d))
        for t in d.columns:
            ax.scatter(d[t], y, color=COR[int(t)], marker=MK[int(t)], s=30, label=f"{t}º turno", zorder=3)
        ax.set_yticks(list(y), d.index)
        ax.legend(frameon=False, fontsize=8)
        _estilo(ax, "Eleitores com biometria habilitados sem ela (% do comparecimento)", "%", "", fonte)
        ax.grid(axis="x", color=GRADE)
        _salvar(fig, g, "biometria_nh_por_uf.png")
        feitos.append("biometria_nh_por_uf.png")
    # 5. Modelos de urna: diferenças com IC95
    f = r / "modelos_efeito_controlado.csv"
    if f.exists():
        d = pd.read_csv(f)
        d = d[d.indicador == "pct_validos_22"].reset_index(drop=True)
        fig, ax = plt.subplots(figsize=(8, 3.8))
        rot = [f"{t}º t. – {c.replace('_', ' ')}" for t, c in zip(d.turno, d.controle)]
        for i, row in d.iterrows():
            ax.plot([row.ic95_inf, row.ic95_sup], [i, i], color=COR[int(row.turno)], lw=2)
            ax.scatter([row.diferenca_controlada_pp], [i], color=COR[int(row.turno)], s=30, zorder=3)
            ax.scatter([row.diferenca_ingenua_pp], [i], color=TXT2, marker="x", s=25, zorder=3)
        ax.axvline(0, color=TXT2, lw=0.8)
        ax.set_yticks(range(len(d)), rot)
        _estilo(ax, "UE2020 − demais modelos: % dos válidos do nº 22 (IC 95%; x = sem controle)",
                "pontos percentuais", "", fonte)
        ax.grid(axis="x", color=GRADE)
        _salvar(fig, g, "modelos_efeito_22.png")
        feitos.append("modelos_efeito_22.png")
    # 6. Impressão digital (comparecimento x proporção), 2º turno
    f = r / "estatistica_impressao_digital.csv"
    if f.exists():
        d = pd.read_csv(f)
        col = [c for c in d.columns if c.startswith("pct_candidato_")][0]
        for t, sub in d.groupby("turno"):
            m = sub.pivot_table(index=col, columns="pct_comparecimento", values="secoes", aggfunc="sum").fillna(0)
            fig, ax = plt.subplots(figsize=(6, 5))
            im = ax.imshow(m.values, origin="lower", aspect="auto", cmap="Blues",
                           extent=(m.columns.min(), m.columns.max() + 1, m.index.min(), m.index.max() + 1))
            fig.colorbar(im, ax=ax, label="nº de seções")
            _estilo(ax, f"{t}º turno: comparecimento × % do candidato {col.split('_')[-1]} por seção",
                    "comparecimento (% dos aptos)", f"% dos válidos para o nº {col.split('_')[-1]}", fonte)
            ax.grid(False)
            _salvar(fig, g, f"impressao_digital_{t}t.png")
            feitos.append(f"impressao_digital_{t}t.png")
    return feitos
