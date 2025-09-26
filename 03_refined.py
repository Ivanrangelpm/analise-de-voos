# %%
import math
import pandas as pd 
import os
import numpy as np

# %%
caminho_dos_arquivos = r'dados/trusted/voos/'

# %%
nomes_dos_arquivos = [
    "dados_voo_202406.csv",
    "dados_voo_202407.csv",
    "dados_voo_202408.csv",
    "dados_voo_202409.csv",
    "dados_voo_202410.csv",
    "dados_voo_202411.csv",
    "dados_voo_202412.csv"
]

# %%
lista_de_dfs = [pd.read_csv(os.path.join(caminho_dos_arquivos, arquivo)) for arquivo in nomes_dos_arquivos]

df_final = pd.concat(lista_de_dfs, ignore_index=True)

df_final.head(5)
print(f"\nNúmero total de linhas no DataFrame final: {len(df_final)}")

# %%
df_final

# %%
df_final.isnull().sum().sort_values(ascending=False)

# %%
print(len(df_final))

# %%
novos_nomes = {
    'SIGLA ICAO AEROPORTO DESTINO' : 'SIGLA AEROPORTO DESTINO',
    'MUNICIPIO ATENDIDO ORIG' : 'MUNICIPIO ORIG',
    'MUNICIPIO ATENDIDO DEST' : 'MUNICIPIO DEST',
    'SIGLA ICAO AEROPORTO ORIGEM' : 'SIGLA AEROPORTO ORIGEM',
}

df_final.rename(columns=novos_nomes, inplace=True)

# %%
df_final = df_final[
    (df_final['UF ORIG'] == 'SP') & 
    (df_final['MUNICIPIO ORIG'] == 'SAO PAULO') & 
    (df_final['MUNICIPIO DEST'] == 'RIO DE JANEIRO') & 
    (df_final['UF DEST'] == 'RJ')
].copy()

print(f"\nNúmero total de voos de São Paulo para Rio de Janeiro: {len(df_final)}")

# %%

df_final['PARTIDA REAL'] = pd.to_datetime(df_final['PARTIDA REAL'], format='%d/%m/%Y %H:%M', errors='coerce')

df_final['HORA PARTIDA REAL'] = df_final['PARTIDA REAL'].dt.time


# %%

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


# %%

df_final['AQO'] = df_final['NUMERO DE ASSENTOS'] * df_final['DISTANCIA KM']


# %%
df_final

# %%
df_final.to_csv('dados/refined/voos_sp_rj_2406_2412.csv', index=False)


