"""Diagnóstico de uma seção: baixa o .logjez do pacote oficial e resume por arquivo de log.

Uso: python scripts/diagnosticar_secao.py ANO TURNO UF ARQUIVO   (ex.: o00406-3195000340123)
Não imprime linhas brutas que contenham números de título (dados pessoais).
"""
import collections
import sys

sys.path.insert(0, ".")
from observatorio import logs as L  # noqa: E402
from observatorio.arquivos_urna import DATAS_ELEICAO, url_pacote  # noqa: E402
from observatorio.remotezip import ArquivoHTTP, extrair_de_bloco, fim_membro, listar_membros  # noqa: E402

ano, turno, uf, stem = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3], sys.argv[4]
d = DATAS_ELEICAO[(ano, turno)].strftime("%d/%m/%Y")
a = ArquivoHTTP(url_pacote(ano, turno, uf))
m = [x for x in listar_membros(a) if x.nome == stem + ".logjez"][0]
dados = extrair_de_bloco(a.faixa(m.offset_cabecalho, fim_membro(m)), m.offset_cabecalho, m)
for nome, cont in L.extrair_7z(dados):
    linhas = [l.split("\t") for l in cont.decode("latin-1").splitlines() if l[:10] == d]
    c = collections.Counter()
    ids = collections.Counter(p[2] for p in linhas if len(p) > 4)
    marcos = []
    for p in linhas:
        if len(p) < 5:
            continue
        msg = p[4]
        if msg in (L.M_COMPUTADO, L.M_HABILITADO, L.M_PRONTA, L.M_INICIO_ENC, L.M_VOTO_PRES):
            c[msg] += 1
        if (msg.startswith(("Urna ligada", "Modo de carga", "Identificação do Modelo", "Iniciando aplicação",
                            "Contingência", "Início do procedimento", "Urna pronta", "Inicio do Encerramento",
                            "Gerando relatório [BU] [INÍCIO]", "Votação suspensa", "Urna desligada",
                            "Serial de votação", "Log interno", "Município:", "Zona Eleitoral:", "Seção Eleitoral:"))
                or "ERRO" == p[1]):
            marcos.append(f"{p[0][11:]} {p[1]:6} {p[2]} {p[3]:5} {msg[:110]}")
    print(f"=== {nome}: {len(linhas)} linhas do dia; ids={dict(ids)}")
    print("   ", dict(c))
    for x in marcos[:60]:
        print("     ", x)
