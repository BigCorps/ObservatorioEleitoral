"""Baixa o perfil do eleitorado por seção (TSE) por UF, agrega faixa etária e escolaridade por seção
e apaga o zip em seguida (os arquivos brutos somam ~3,6 GB).

Uso: python scripts/baixar_perfil_idade_secao.py 2022 2026
Saída: dados/processados/tabelas/perfil_idade_secao/{ano}_{UF}.parquet (fora do Git). Retomável.
"""
import sys, zipfile, os, time, subprocess
import pyarrow as pa, pyarrow.csv as pc, pyarrow.compute as C, pyarrow.parquet as pq
import pandas as pd
RAIZ=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D=os.path.join(RAIZ,'dados','brutos','tmp_perfil_secao')
OUT=os.path.join(RAIZ,'dados','processados','tabelas','perfil_idade_secao')
os.makedirs(OUT, exist_ok=True); os.makedirs(D, exist_ok=True)
UFS="AC AL AM AP BA CE DF ES GO MA MG MS MT PA PB PE PI PR RJ RN RO RR RS SC SE SP TO ZZ".split()
def faixa(cod):
    i=cod//100
    return ('16_17' if i<18 else '18_24' if i<25 else '25_44' if i<45 else '45_59' if i<60 else '60_69' if i<70 else '70_mais')
def processa(ano, uf):
    destino=f'{OUT}/{ano}_{uf}.parquet'
    if os.path.exists(destino): return 'ja'
    url=f'https://cdn.tse.jus.br/estatistica/sead/odsele/perfil_eleitor_secao/perfil_eleitor_secao_{ano}_{uf}.zip'
    z=f'{D}/{ano}_{uf}.zip'
    for t in range(5):
        r=subprocess.run(['curl','-sS','-f','--retry','3','-o',z,url]); 
        if r.returncode==0: break
        time.sleep(2**t)
    else: raise SystemExit(f'falha {url}')
    zf=zipfile.ZipFile(z); nome=[n for n in zf.namelist() if n.endswith('.csv')][0]
    qt='QT_ELEITORES_PERFIL' if ano<=2024 else 'QT_ELEITORES'
    cols=['SG_UF','CD_MUNICIPIO','NR_ZONA','NR_SECAO','CD_FAIXA_ETARIA','CD_GRAU_ESCOLARIDADE',qt,'QT_ELEITORES_BIOMETRIA']
    leitor=pc.open_csv(zf.open(nome), read_options=pc.ReadOptions(encoding='latin-1', block_size=64<<20),
                       parse_options=pc.ParseOptions(delimiter=';'),
                       convert_options=pc.ConvertOptions(include_columns=cols, column_types={'CD_MUNICIPIO':pa.int64(),'NR_ZONA':pa.int64(),'NR_SECAO':pa.int64(),'CD_FAIXA_ETARIA':pa.int64(),'CD_GRAU_ESCOLARIDADE':pa.int64(),qt:pa.int64(),'QT_ELEITORES_BIOMETRIA':pa.int64()}))
    partes=[]
    for b in leitor:
        df=b.to_pandas()
        df['faixa']=df.CD_FAIXA_ETARIA.map(faixa)
        # escolaridade: 1 analfabeto, 2 lê e escreve, 3 fundamental incompleto
        df['baixa_esc']=df.CD_GRAU_ESCOLARIDADE.isin([1,2,3])
        g=df.groupby(['CD_MUNICIPIO','NR_ZONA','NR_SECAO'])
        a=df.pivot_table(index=['CD_MUNICIPIO','NR_ZONA','NR_SECAO'],columns='faixa',values=qt,aggfunc='sum',fill_value=0)
        a['eleitores']=g[qt].sum(); a['com_biometria']=g['QT_ELEITORES_BIOMETRIA'].sum()
        a['baixa_escolaridade']=df[df.baixa_esc].groupby(['CD_MUNICIPIO','NR_ZONA','NR_SECAO'])[qt].sum()
        partes.append(a.fillna(0))
    r=pd.concat(partes).groupby(level=[0,1,2]).sum().reset_index()
    r.insert(0,'uf',uf); r.insert(0,'ano',ano)
    r.to_parquet(destino,index=False)
    zf.close(); os.remove(z)
    return len(r)
for ano in map(int, sys.argv[1:]):
    for uf in UFS:
        t=time.time(); print(ano, uf, processa(ano, uf), round(time.time()-t), flush=True)
print('FIMPERFIL')
