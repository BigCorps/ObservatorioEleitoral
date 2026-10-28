"""Baixa "Perfil do comparecimento e abstenção" (TSE, Dados Abertos) de 2022 e 2026 e agrega por
ano, turno, UF, município e faixa etária. Os zips (~430 MB) são apagados ao final.

Uso: python scripts/baixar_comparecimento_idade.py
Saída: dados/processados/tabelas/comparecimento_faixa_etaria_municipio.parquet (fora do Git).
Atenção: em 28/10/2026 o arquivo de 2026 (Last-Modified 21/10/2026) só contém o 1º turno.
"""
import os, subprocess
import zipfile, sys
import pyarrow as pa, pyarrow.csv as pc
import pandas as pd
RAIZ=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D=os.path.join(RAIZ,'dados','brutos','tmp_comparecimento'); os.makedirs(D, exist_ok=True)
OUT=os.path.join(RAIZ,'dados','processados','tabelas')
URL='https://cdn.tse.jus.br/estatistica/sead/odsele/perfil_comparecimento_abstencao/perfil_comparecimento_abstencao_{a}.zip'
for a in (2022, 2026):
    if not os.path.exists(f'{D}/pca_{a}.zip'):
        subprocess.run(['curl','-sS','-f','--retry','3','-o',f'{D}/pca_{a}.zip',URL.format(a=a)], check=True)
num=['QT_APTOS','QT_COMPARECIMENTO','QT_ABSTENCAO','QT_COMPAREC_FACULTATIVO','QT_ABST_FACULTATIVO']
partes=[]
for a in (2022,2026):
    z=zipfile.ZipFile(f'{D}/pca_{a}.zip'); n=[x for x in z.namelist() if 'BRASIL' in x][0]
    cols=['NR_TURNO','SG_UF','CD_MUNICIPIO','CD_FAIXA_ETARIA','DS_FAIXA_ETARIA']+num
    r=pc.open_csv(z.open(n), read_options=pc.ReadOptions(encoding='latin-1', block_size=64<<20),
        parse_options=pc.ParseOptions(delimiter=';'),
        convert_options=pc.ConvertOptions(include_columns=cols, column_types={c:pa.int64() for c in num+['NR_TURNO','CD_FAIXA_ETARIA']}))
    acc=[]
    for b in r:
        df=b.to_pandas(); df['DS_FAIXA_ETARIA']=df.DS_FAIXA_ETARIA.str.strip()
        acc.append(df.groupby(['NR_TURNO','SG_UF','CD_MUNICIPIO','CD_FAIXA_ETARIA','DS_FAIXA_ETARIA'])[num].sum())
    t=pd.concat(acc).groupby(level=[0,1,2,3,4]).sum().reset_index(); t.insert(0,'ANO',a)
    print(a, t.groupby('NR_TURNO')[num].sum().to_string(), flush=True)
    partes.append(t)
pd.concat(partes).to_parquet(f'{OUT}/comparecimento_faixa_etaria_municipio.parquet', index=False)
for a in (2022, 2026):
    os.remove(f'{D}/pca_{a}.zip')
print('FIMABST')
