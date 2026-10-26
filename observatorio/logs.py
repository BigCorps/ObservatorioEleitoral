"""Leitura e interpretação dos logs da urna (arquivos .logjez).

Cada .logjez é um pacote 7z com `logd.dat` (texto latin-1, campos separados por
TAB: data-hora, nível, identificador, aplicação, mensagem, código de verificação)
e, eventualmente, pacotes .jez aninhados (logs arquivados, por exemplo de urna
substituída/contingência), que são lidos recursivamente.

Princípios:
- Só são usados eventos cujo significado é inequívoco pelo texto da mensagem.
- Os horários são os do relógio interno da urna (hora local). A conversão para
  o horário de Brasília é feita em `fusos.py`, com o fuso legal do município.
- Linhas idênticas presentes em mais de um arquivo (cópias de log) são
  contadas uma única vez.
- Nada no log permite associar horário de voto a candidato; esta análise não
  tenta fazê-lo. Números de título de mesários que aparecem em mensagens NÃO
  são extraídos nem gravados.
"""
from __future__ import annotations

import io
from dataclasses import dataclass, field

import py7zr
from py7zr.io import BytesIOFactory

# Códigos de modalidade de habilitação (por eleitor habilitado)
HAB_BIOMETRICA = 1          # "Tipo de habilitação do eleitor [biométrica]"
HAB_SEM_BIOMETRIA = 2       # "O eleitor não possui biometria" (sem digital cadastrada)
HAB_MANUAL_APOS_FALHA = 3   # "Solicitação de dado pessoal do eleitor para habilitação manual"
HAB_INDETERMINADA = 0       # nenhuma das mensagens acima (ex.: urnas no exterior, sem leitor biométrico)

MODALIDADES = {
    HAB_BIOMETRICA: "biometrica",
    HAB_SEM_BIOMETRIA: "sem_biometria_cadastrada",
    HAB_MANUAL_APOS_FALHA: "manual_apos_falha_biometrica",
    HAB_INDETERMINADA: "sem_etapa_biometrica_no_log",
}

M_PRONTA = "Urna pronta para receber votos"
M_TITULO = "Título digitado pelo mesário"
M_AGUARDA_TITULO = "Aguardando digitação do título"
M_TIPO_BIO = "Tipo de habilitação do eleitor [biométrica]"
M_TIPO_PREFIXO = "Tipo de habilitação do eleitor ["
M_SEM_BIO = "O eleitor não possui biometria"
M_MANUAL = "Solicitação de dado pessoal do eleitor para habilitação manual"
M_HABILITADO = "Eleitor foi habilitado"
M_COMPUTADO = "O voto do eleitor foi computado"
M_VOTO_PRES = "Voto confirmado para [Presidente]"
M_NULO_SUSP_PRES = "Atribuido voto nulo por suspensão [Presidente]"
M_SUSPENSO = "Eleitor foi suspenso pelo mesário"
M_PARCIAL_SUSP = "Eleitor votou parcialmente e em seguida foi suspenso"
M_SUSP_SEM_VOTO = "Eleitor foi suspenso e não confirmou nenhum voto"
M_JA_VOTOU = "O eleitor identificado já votou"
M_HAB_CANCEL = "Habilitação cancelada"
M_INICIO_ENC = "Inicio do Encerramento"
M_ENC_CONFIRMADO = "Procedimento de encerramento confirmado"
M_ENC_APOS = "Encerramento só pode ser solicitado após as"
M_GERA_BU = "Gerando relatório [BU] [INÍCIO]"
M_ARQ_BU = "Gerando arquivo de resultado [.bu] + [Término]"
M_IMPRIME_BU1 = "Imprimindo relatório [BU] via nº [1]"
M_ZERESIMA = "Gerando relatório [ZERÉSIMA] [INÍCIO]"
M_LIGADA = "Urna ligada em"
M_MODELO = "Identificação do Modelo de Urna: "
M_CONTINGENCIA_MODO = "Modo de carga da UE - Urna de contingência"
M_CONTINGENCIA_OK = "Contingência executada com sucesso"
M_VOTACAO_SUSPENSA = "Votação suspensa"
M_DESLIGADA = "Urna desligada pela chave"
M_VERSAO = "Versão da aplicação: "


def extrair_7z(dados: bytes, profundidade: int = 0) -> list[tuple[str, bytes]]:
    """Retorna [(nome, conteúdo)] de um 7z, abrindo .jez aninhados recursivamente."""
    fab = BytesIOFactory(1 << 31)
    with py7zr.SevenZipFile(io.BytesIO(dados)) as z:
        z.extractall(factory=fab)
    saida = []
    for nome, bio in fab.products.items():
        bio.seek(0)
        conteudo = bio.read()
        if nome.lower().endswith(".jez") and profundidade < 3:
            try:
                for n2, c2 in extrair_7z(conteudo, profundidade + 1):
                    saida.append((f"{nome}/{n2}", c2))
                continue
            except Exception:
                pass
        saida.append((nome, conteudo))
    return saida


def hms(s: str) -> int:
    """'HH:MM:SS' -> segundos desde a meia-noite."""
    return int(s[0:2]) * 3600 + int(s[3:5]) * 60 + int(s[6:8])


@dataclass
class ResumoLog:
    """Eventos do dia da eleição extraídos de um log, em segundos (hora local da urna)."""
    arquivos: list[str] = field(default_factory=list)
    linhas_dia: int = 0
    linhas_dia_seguinte: int = 0
    linhas_duplicadas: int = 0
    linhas_malformadas: int = 0
    ids_urna: set = field(default_factory=set)
    modelos: set = field(default_factory=set)
    versoes: set = field(default_factory=set)
    eventos: dict = field(default_factory=dict)        # mensagem-chave -> lista de segundos
    votos_s: list = field(default_factory=list)        # "O voto do eleitor foi computado"
    hab_s: list = field(default_factory=list)          # "Eleitor foi habilitado"
    hab_mod: list = field(default_factory=list)        # modalidade de cada habilitação
    dur_voto: list = field(default_factory=list)       # habilitação -> voto computado (s)
    dur_voto_mod: list = field(default_factory=list)
    tipos_hab_outros: dict = field(default_factory=dict)
    retrocessos_relogio: int = 0
    maior_retrocesso_s: int = 0
    n_erro: int = 0
    n_alerta: int = 0

    def ev(self, chave: str, t: int) -> None:
        self.eventos.setdefault(chave, []).append(t)


CHAVES_SIMPLES = {
    M_PRONTA: "pronta", M_TITULO: "titulo", M_VOTO_PRES: "voto_presidente",
    M_NULO_SUSP_PRES: "nulo_suspensao_presidente", M_SUSPENSO: "suspenso",
    M_PARCIAL_SUSP: "parcial_suspenso", M_SUSP_SEM_VOTO: "suspenso_sem_voto",
    M_JA_VOTOU: "ja_votou", M_INICIO_ENC: "inicio_encerramento",
    M_ENC_CONFIRMADO: "encerramento_confirmado", M_GERA_BU: "gera_bu", M_ARQ_BU: "arquivo_bu",
    M_IMPRIME_BU1: "imprime_bu", M_ZERESIMA: "zeresima", M_CONTINGENCIA_MODO: "modo_contingencia",
    M_CONTINGENCIA_OK: "contingencia_ok", M_VOTACAO_SUSPENSA: "votacao_suspensa",
    M_DESLIGADA: "desligada", M_ENC_APOS: "tentativa_encerramento_antecipado",
}


def interpretar(arquivos: list[tuple[str, bytes]], data_eleicao: str, data_seguinte: str) -> ResumoLog:
    """Interpreta os logs de uma seção. `data_eleicao` no formato dd/mm/aaaa."""
    r = ResumoLog()
    vistos: set[str] = set()
    for nome, conteudo in arquivos:
        r.arquivos.append(nome)
        texto = conteudo.decode("latin-1")
        ult_abs = None
        estado_mod = None
        ultimo_hab = None
        ultimo_hab_mod = None
        for linha in texto.splitlines():
            dia = linha[:10]
            if dia == data_seguinte:
                r.linhas_dia_seguinte += 1
            if dia != data_eleicao and dia != data_seguinte:
                continue
            if linha in vistos:
                r.linhas_duplicadas += 1
                continue
            vistos.add(linha)
            p = linha.split("\t")
            if len(p) < 5 or len(p[0]) != 19:
                r.linhas_malformadas += 1
                continue
            try:
                t = hms(p[0][11:19])
            except ValueError:
                r.linhas_malformadas += 1
                continue
            if dia == data_seguinte:
                t += 86400
            else:
                r.linhas_dia += 1
            if ult_abs is not None and t < ult_abs:
                r.retrocessos_relogio += 1
                r.maior_retrocesso_s = max(r.maior_retrocesso_s, ult_abs - t)
            ult_abs = t
            nivel = p[1]
            if nivel == "ERRO":
                r.n_erro += 1
            elif nivel == "ALERTA":
                r.n_alerta += 1
            r.ids_urna.add(p[2])
            msg = p[4]
            app = p[3]
            if msg == M_COMPUTADO:
                r.votos_s.append(t)
                if ultimo_hab is not None:
                    r.dur_voto.append(t - ultimo_hab)
                    r.dur_voto_mod.append(ultimo_hab_mod)
                ultimo_hab = None
                continue
            if msg == M_HABILITADO:
                mod = estado_mod if estado_mod is not None else HAB_INDETERMINADA
                r.hab_s.append(t)
                r.hab_mod.append(mod)
                ultimo_hab, ultimo_hab_mod = t, mod
                estado_mod = None
                continue
            if msg == M_TITULO or msg == M_AGUARDA_TITULO:
                estado_mod = None
                if msg == M_TITULO:
                    r.ev("titulo", t)
                continue
            if msg.startswith(M_TIPO_PREFIXO):
                if msg == M_TIPO_BIO:
                    estado_mod = HAB_BIOMETRICA
                else:
                    r.tipos_hab_outros[msg] = r.tipos_hab_outros.get(msg, 0) + 1
                continue
            if msg == M_SEM_BIO:
                estado_mod = HAB_SEM_BIOMETRIA
                continue
            if msg == M_MANUAL:
                if estado_mod is None:
                    estado_mod = HAB_MANUAL_APOS_FALHA
                continue
            if msg.startswith(M_HAB_CANCEL):
                # não zera a modalidade: há casos em que o fluxo prossegue após o
                # cancelamento da captura da digital do mesário (ver docs/metodologia.md)
                r.ev("habilitacao_cancelada", t)
                continue
            ch = CHAVES_SIMPLES.get(msg)
            if ch is None and msg.startswith(M_ENC_APOS):
                ch = "tentativa_encerramento_antecipado"
            if ch is not None:
                r.ev(ch, t)
                if ch == "suspenso_sem_voto":
                    # eleitor suspenso sem nenhum voto não compõe o comparecimento
                    ultimo_hab = None
                continue
            if app == "LOGD" and msg.startswith(M_LIGADA):
                r.ev("ligada", t)
            elif msg.startswith(M_MODELO):
                r.modelos.add(msg[len(M_MODELO):].strip())
            elif msg.startswith(M_VERSAO):
                r.versoes.add(msg[len(M_VERSAO):].strip())
    return r
