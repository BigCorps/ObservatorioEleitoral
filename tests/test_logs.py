"""Testes do interpretador de logs com um log sintético (sem dados pessoais)."""
import io

import py7zr

from observatorio import logs as L

D = "02/10/2022"


def linha(hora, msg, nivel="INFO", app="VOTA"):
    return f"{D} {hora}\t{nivel}\t67305985\t{app}\t{msg}\tABCDEF0123456789"


LOG = "\n".join([
    "01/10/2022 10:00:00\tINFO\t67305985\tVOTA\tO voto do eleitor foi computado\tX",  # outro dia: ignorar
    linha("06:59:00", "Urna ligada em 02/10/2022 às 06:58:00", app="LOGD"),
    linha("07:00:00", "Identificação do Modelo de Urna: UE2020", app="GAP"),
    linha("07:55:00", "Urna pronta para receber votos"),
    # eleitor 1: biometria reconhecida
    linha("08:00:10", "Título digitado pelo mesário"),
    linha("08:00:15", "Tipo de habilitação do eleitor [biométrica]"),
    linha("08:00:16", "Eleitor foi habilitado"),
    linha("08:00:40", "Voto confirmado para [Presidente]"),
    linha("08:00:42", "O voto do eleitor foi computado"),
    # eleitor 2: sem biometria cadastrada
    linha("08:01:00", "Título digitado pelo mesário"),
    linha("08:01:02", "O eleitor não possui biometria", nivel="ALERTA"),
    linha("08:01:05", "Eleitor foi habilitado"),
    linha("08:01:50", "Voto confirmado para [Presidente]"),
    linha("08:01:52", "O voto do eleitor foi computado"),
    # eleitor 3: falha biométrica -> habilitação manual, com cancelamento intermediário
    linha("08:02:00", "Título digitado pelo mesário"),
    linha("08:02:30", "Solicitação de dado pessoal do eleitor para habilitação manual"),
    linha("08:02:40", "Habilitação cancelada durante a captura de digital do mesário", nivel="ALERTA"),
    linha("08:02:50", "Eleitor foi habilitado"),
    linha("08:03:20", "Atribuido voto nulo por suspensão [Presidente]"),
    linha("08:03:20", "Eleitor votou parcialmente e em seguida foi suspenso"),
    linha("08:03:21", "O voto do eleitor foi computado"),
    # eleitor 4: suspenso sem votar (não compõe comparecimento)
    linha("08:04:00", "Título digitado pelo mesário"),
    linha("08:04:01", "Tipo de habilitação do eleitor [biométrica]"),
    linha("08:04:02", "Eleitor foi habilitado"),
    linha("08:05:00", "Eleitor foi suspenso e não confirmou nenhum voto"),
    linha("17:00:00", "Inicio do Encerramento"),
    linha("17:00:30", "Gerando relatório [BU] [INÍCIO]"),
    "linha malformada sem tabs",
    "03/10/2022 00:10:00\tINFO\t67305985\tVOTA\tGerando arquivo de resultado [.bu] + [Término]\tY",
])


def _arqs(texto=LOG):
    return [("logd.dat", texto.encode("latin-1"))]


def test_contagens_e_modalidades():
    r = L.interpretar(_arqs(), D, "03/10/2022")
    assert len(r.votos_s) == 3                   # votos computados (eleitor 4 não votou)
    assert len(r.hab_s) == 4
    assert r.hab_mod == [L.HAB_BIOMETRICA, L.HAB_SEM_BIOMETRIA, L.HAB_MANUAL_APOS_FALHA, L.HAB_BIOMETRICA]
    # pares habilitação -> voto: 3, com a modalidade do eleitor que votou
    assert r.dur_voto_mod == [L.HAB_BIOMETRICA, L.HAB_SEM_BIOMETRIA, L.HAB_MANUAL_APOS_FALHA]
    assert r.dur_voto == [26, 47, 31]
    assert r.modelos == {"UE2020"}
    assert len(r.eventos["voto_presidente"]) == 2 and len(r.eventos["nulo_suspensao_presidente"]) == 1
    assert r.eventos["arquivo_bu"] == [86400 + 600]  # dia seguinte somado em +24h


def test_linhas_duplicadas_em_varios_arquivos_contam_uma_vez():
    r = L.interpretar(_arqs() + [("copia.jez/logd.dat", LOG.encode("latin-1"))], D, "03/10/2022")
    assert len(r.votos_s) == 3
    assert r.linhas_duplicadas > 0


def test_retrocesso_de_relogio_detectado():
    t = "\n".join([linha("10:00:00", "Tecla indevida pressionada"), linha("09:00:00", "Tecla indevida pressionada")])
    r = L.interpretar(_arqs(t), D, "03/10/2022")
    assert r.retrocessos_relogio == 1 and r.maior_retrocesso_s == 3600


def test_extrair_7z_aninhado():
    interno = io.BytesIO()
    with py7zr.SevenZipFile(interno, "w") as z:
        z.writestr(LOG.encode("latin-1"), "logd.dat")
    externo = io.BytesIO()
    with py7zr.SevenZipFile(externo, "w") as z:
        z.writestr(interno.getvalue(), "antigo-01.jez")
        z.writestr(b"x", "logd.dat")
    nomes = [n for n, _ in L.extrair_7z(externo.getvalue())]
    assert "antigo-01.jez/logd.dat" in nomes and "logd.dat" in nomes


def test_ajuste_de_hora_registrado():
    t = linha("08:55:15", "Iniciando aplicação AJUSTE DE DATA E HORA - Sem fase", app="GAP")
    r = L.interpretar(_arqs(t), D, "03/10/2022")
    assert r.eventos["ajuste_hora"] == [8 * 3600 + 55 * 60 + 15]
