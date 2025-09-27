import math
import pandas as pd 
import os
import numpy as np

caminho_dos_arquivos = r'dados/trusted/voos/'

nomes_dos_arquivos = [
    "dados_voo_202406.csv",
    "dados_voo_202407.csv",
    "dados_voo_202408.csv",
    "dados_voo_202409.csv",
    "dados_voo_202410.csv",
    "dados_voo_202411.csv",
    "dados_voo_202412.csv"
]

lista_de_dfs = [pd.read_csv(os.path.join(caminho_dos_arquivos, arquivo)) for arquivo in nomes_dos_arquivos]

df_final = pd.concat(lista_de_dfs, ignore_index=True)

df_final.head(5)
print(f"\nNúmero total de linhas no DataFrame final: {len(df_final)}")

df_final

df_final.isnull().sum().sort_values(ascending=False)

print(len(df_final))

novos_nomes = {
    'SIGLA ICAO AEROPORTO DESTINO' : 'SIGLA AEROPORTO DESTINO',
    'MUNICIPIO ATENDIDO ORIG' : 'MUNICIPIO ORIG',
    'MUNICIPIO ATENDIDO DEST' : 'MUNICIPIO DEST',
    'SIGLA ICAO AEROPORTO ORIGEM' : 'SIGLA AEROPORTO ORIGEM',
}

df_final.rename(columns=novos_nomes, inplace=True)

df_final = df_final[
    (df_final['UF ORIG'] == 'SP') & 
    (df_final['MUNICIPIO ORIG'] == 'SAO PAULO') & 
    (df_final['MUNICIPIO DEST'] == 'RIO DE JANEIRO') & 
    (df_final['UF DEST'] == 'RJ')
].copy()

print(f"\nNúmero total de voos de São Paulo para Rio de Janeiro: {len(df_final)}")

df_final['PARTIDA REAL'] = pd.to_datetime(df_final['PARTIDA REAL'], format='%d/%m/%Y %H:%M', errors='coerce')

df_final['HORA PARTIDA REAL'] = df_final['PARTIDA REAL'].dt.time

def mapear_cluster_hora(hora_integer):
    if 0 <= hora_integer < 2:
        return 1
    elif 2 <= hora_integer < 4:
        return 2
    elif 4 <= hora_integer < 6:
        return 3
    elif 6 <= hora_integer < 8:
        return 4
    elif 8 <= hora_integer < 10:
        return 5
    elif 10 <= hora_integer < 12:
        return 6
    elif 12 <= hora_integer < 14:
        return 7
    elif 14 <= hora_integer < 16:
        return 8
    elif 16 <= hora_integer < 18:
        return 9
    elif 18 <= hora_integer < 20:
        return 10
    elif 20 <= hora_integer < 22:
        return 11
    elif 22 <= hora_integer <= 23:
        return 12
    else:
        return np.nan

df_final['CLUSTER_HORA'] = df_final['PARTIDA REAL'].dt.hour.apply(mapear_cluster_hora)

df_final['AQO'] = df_final['NUMERO DE ASSENTOS'] * df_final['DISTANCIA KM']

df_final

caminho_dos_arquivos = r'dados/trusted/reclamacoes/'

nomes_dos_arquivos = [
    "reclamacoes202406.csv",
    "reclamacoes202407.csv",
    "reclamacoes202408.csv",
    "reclamacoes202409.csv",
    "reclamacoes202410.csv",
    "reclamacoes202411.csv",
    "reclamacoes202412.csv"
]

lista_de_dfs = [pd.read_csv(os.path.join(caminho_dos_arquivos, arquivo)) for arquivo in nomes_dos_arquivos]

df_rec = pd.concat(lista_de_dfs, ignore_index=True)

df_rec.head(5)
print(f"\nNúmero total de linhas no DataFrame de reclamações: {len(df_rec)}")

df_rec

df_final.sample(10)

combinacoes_unicas = df_final[['SIGLA ICAO EMPRESA AEREA', 'EMPRESA AEREA']].drop_duplicates()
combinacoes_unicas = combinacoes_unicas.sort_values(by='EMPRESA AEREA').reset_index(drop=True)
combinacoes_unicas

combinacoes_unicas_rec = df_rec[['NOME FANTASIA']].drop_duplicates()
combinacoes_unicas_rec = combinacoes_unicas_rec.sort_values(by='NOME FANTASIA').reset_index(drop=True)
combinacoes_unicas_rec

map_antigo_para_novo = {
    'AZUL CONECTA LTDA. (EX TWO TAXI AEREO LTDA)': 'AZUL CONECTA LTDA',
    'AZUL LINHAS AEREAS BRASILEIRAS S/A': 'AZUL LINHAS AEREAS',
    'GOL LINHAS AEREAS S.A. (EX- VRG LINHAS AEREAS S.A.)': 'GOL LINHAS AEREAS',
    'TAM LINHAS AEREAS S.A.': 'LATAM AIRLINES (TAM)',
    'PASSAREDO TRANSPORTES AEREOS S.A.': 'VOEPASS LINHAS AEREAS'
}

map_novo_para_sigla = {
    'AZUL LINHAS AEREAS': 'AZU',
    'GOL LINHAS AEREAS': 'GLO',
    'LATAM AIRLINES (TAM)': 'TAM',
    'VOEPASS LINHAS AEREAS': 'PTB'
}

df_final['EMPRESA AEREA'] = df_final['EMPRESA AEREA'].replace(map_antigo_para_novo)

df_rec['SIGLA ICAO EMPRESA AEREA'] = df_rec['NOME FANTASIA'].map(map_novo_para_sigla)

combinacoes_unicas = df_final[['SIGLA ICAO EMPRESA AEREA', 'EMPRESA AEREA']].drop_duplicates()
combinacoes_unicas = combinacoes_unicas.sort_values(by='EMPRESA AEREA').reset_index(drop=True)
combinacoes_unicas

df_rec = df_rec.dropna(subset=['SIGLA ICAO EMPRESA AEREA'])

df_final.to_csv('dados/refined/voos_sp_rj_2406_2412.csv', index=False)

df_rec.to_csv('dados/refined/reclamacoes_2406_2412.csv', index=False)


