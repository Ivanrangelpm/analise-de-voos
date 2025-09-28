# %% [markdown]
# ### Atividade 
# 
# #### Parte Ivan
# 
# - Criar arquivo terraform para criação de 3 buckets (raw, trusted e refined) e lambda para enviar arquivos de Raw para Trusted 
# - Criar código para subir dados para bucket 
# - criar código para enviar de lambda raw para trusted 
# - Criar a rotina para reprocessamento
# - Entregar arquivo PDF com a descrição dos tratamento e particionamentos realizados 
# - Entregar arquivo ZIP com os dados Tratados
# - Entregar arquivo ZIP com o script Python utilizado
# 
# 
# 
# 
# #### Parte Gustavo e Luis
# 
# 1) Separar quais arquivos cada um vai tratar
# 
# 2) Analisar os Arquivos e considerar as transformações necessárias para limpeza,
# padronização, enriquecimento de dados e reprocessamento dos dados 
# - Sugestão de padronização no sumário abaixo (podém mudar o que preferirem, só alinhem entre si pois os arquivos tem que ter o mesmo tratamento)
# - Converter dados de latitude e longitude que estão em graus para decimais (se for o arquivo que tem essa coluna, o professor disponibilizou o codigo)
# - Somente considerar voos domésticos
#  
# 3) Os arquivos de Voos e de Reclamações precisam passar por tratamento para que
# sejam armazenados no Bucket Trusted de forma que facilitem reprocessamentos
# 4) Particionar por mes, ou seja, criar um arquivo csv para cada mes, nesse formato que o professor pediu : 
# - dados_voo_YYYYMM
# - reclamação_YYYYMM
# 
# 
# ### Avisos:
# 
# - Os arquivos csv são muito grandes para mandar p github então podem colocar em uma pasta chamada "dados", eu adicionei um .env que não vai mandar para o git, eu colocaria os dados em uma subpasta chamada raw e mandaria para outra subpasta chamada trusted, mas podem deixar que eu arrumo no final
# 
# 
# - Para acessar e rodar os arquivos ipynb usar a extensão do VSCode jupyter notebook da Microsoft
# - Esta Prática servirá de base para a nossa próxima aula
# - Para o tratamento dos dados podem usar como base o nosso arquivo tratamento.ipynb no github https://github.com/BeiraMar-G2/beira-mar-data-analytics tem muita coisa que pode ser reaproveitada
# - A Atividade pode ser feita em Grupo, não esqueça de informar Nome e RA
# - Entrega
# - Sugestão para nome de arquivo     
# - Não esqueça de documentar também o reprocessamento dos arquivos dos meses
# de Novembro e Dezembro de 2024

# %% [markdown]
# ### Sumário de padrões para tratamento de dados:
# 
# - Data: DD/MM/YYYY
# 
# - Data hora: DD/MM/YYYY HH:MM:SS
# 
# - Binário: 0 ou 1
# 
# - Strings e colunas: Maiusculas e sem acento: 
# 
# - Espaços: Manter apenas um espaço no intervalo entre palavras
# 
# - Sexo: M e F
# 
# - Delimitador: Vírgula
# 
# - Armazenar dados em arquivos csv

# %%
import math
import pandas as pd 
import win32com.client as win32
import unicodedata
import os
import re

# %% [markdown]
# ### Funções para padronização:

# %%
# Formato em 2016-04-29T18:38:08Z
def padronizar_data_hora(df, coluna):

  df[coluna] = pd.to_datetime(df[coluna])
  
  df[coluna] = df[coluna].dt.strftime('%d/%m/%Y %H:%M:%S')
  
  return df


# %%
#Formato em MM/DD/AA
def padronizar_data(df, coluna):

  df[coluna] = pd.to_datetime(df[coluna], format='%m/%d/%Y')
  
  df[coluna] = df[coluna].dt.strftime('%d/%m/%Y')
  
  return df

# %%
def padronizar_data02(df, coluna):
    # Converte a coluna para o tipo datetime, tratando erros
    df[coluna] = pd.to_datetime(df[coluna], format='%Y-%m-%d', errors='coerce')
    
    # Formata as datas válidas, deixando os NaNs como estão
    df[coluna] = df[coluna].dt.strftime('%d/%m/%Y')
    
    return df


# %%
def padronizar_colunas(df):

    df.columns = df.columns.str.upper()
    
    return df

# %%
def converter_para_binario(df, coluna):
    mapeamento = {'Yes': 1, 'No': 0}
    df[coluna].replace(mapeamento, inplace=True)
    return df

# %%
def funcao_apoio_remover_acentos(texto):
    """Remove apenas os acentos de uma string."""
    if not isinstance(texto, str):
        return texto 

    texto_normalizado = unicodedata.normalize('NFKD', texto)
    texto_sem_acentos = "".join(
        [c for c in texto_normalizado if not unicodedata.combining(c)]
    )
    return texto_sem_acentos

# %%
def remover_acentos_no_df(df):
    """
    Remove acentos do cabeçalho e de colunas de texto no DataFrame.
    """
    df.columns = [funcao_apoio_remover_acentos(col) for col in df.columns]
    colunas_de_texto = df.select_dtypes(include=['object'])
    
    for coluna in colunas_de_texto.columns:
        df[coluna] = df[coluna].apply(funcao_apoio_remover_acentos)

    return df

# %%
def remover_acentos(df):
    for coluna in df.columns:
        if df[coluna].dtype == 'object':
            df[coluna] = df[coluna].astype(str).str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')
    return df


# %%
def padronizar_maiusculo(df):
    for coluna in df.columns:
        if df[coluna].dtype == 'object':
            df[coluna] = df[coluna].astype(str).str.upper()
    return df

# %%

def padronizar_espacos_colunas(df: pd.DataFrame) -> pd.DataFrame:

    novas_colunas = []
    for coluna in df.columns:
        coluna_sem_acento = ''.join(c for c in unicodedata.normalize('NFD', coluna) 
                                    if unicodedata.category(c) != 'Mn')

        coluna_normalizada = coluna_sem_acento.lower().replace(' ', '_').replace('-', '_')
        novas_colunas.append(coluna_normalizada)
    
    df.columns = novas_colunas
    return df


# %%
def dms_para_dd(graus, minutos, segundos, direcao):
    """
    Converte coordenadas de Graus/Minutos/Segundos (DMS) para Graus Decimais (DD).
    Exemplo: dms_para_dd(8, 20, 55, 'S') -> -8.348611
    """
    decimal = graus + (minutos / 60) + (segundos / 3600)
    if direcao in ['S', 'W']:
        decimal = -decimal
    return decimal


def haversine(lat1, lon1, lat2, lon2):
    """
    Calcula a distância entre dois pontos na Terra (em km)
    a partir de suas coordenadas em graus decimais.
    """
    R = 6371.0  # raio médio da Terra em km
    
    # Converter para radianos
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Diferenças
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    

    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c


# %% [markdown]
# ### Tratando bases:

# %%

base_dir = os.getcwd()

caminho_xls = os.path.join(base_dir, "dados", "raw", "Dados Atividade", "aerodromospublicos.xls")
caminho_xlsx = os.path.join(base_dir, "dados", "raw", "Dados Atividade", "aerodromospublicos.xlsx")

print(caminho_xls)

# %%
def converter_xls_para_xlsx(caminho_relativo_xls):
    base_dir = os.getcwd()
    arquivo_xls = os.path.join(base_dir, caminho_relativo_xls)
    arquivo_xlsx = arquivo_xls.replace(".xls", ".xlsx")
    
    excel = win32.gencache.EnsureDispatch('Excel.Application')
    wb = excel.Workbooks.Open(arquivo_xls)
    wb.SaveAs(arquivo_xlsx, FileFormat=51) 
    wb.Close()
    excel.Application.Quit()

    print(f"Conversão concluída: {arquivo_xlsx}")

# Exemplo de uso
converter_xls_para_xlsx(r"dados\raw\Dados Atividade\aerodromospublicos.xls")

# %%
df_aero = pd.read_excel('dados/raw/Dados Atividade/aerodromospublicos.xlsx',  header=2)

# %%
df_aero

# %%
df_aero = padronizar_colunas(df_aero)
df_aero = remover_acentos_no_df(df_aero)
df_aero = padronizar_maiusculo(df_aero)
df_aero = padronizar_espacos_colunas(df_aero)

# %%
df_empresas = pd.read_excel('dados/raw/Dados Atividade/Empresas Aereas.xlsx', engine='openpyxl')

# %%
df_empresas = padronizar_colunas(df_empresas)
df_empresas = remover_acentos_no_df(df_empresas)
df_empresas = padronizar_maiusculo(df_empresas)
df_empresas = padronizar_espacos_colunas(df_empresas)
padronizar_data_hora(df_empresas,'DATA DECISAO OPERACIONAL')
padronizar_data_hora(df_empresas,'VALIDADE OPERACIONAL')



# %%
df_vra = pd.read_csv('dados/raw/Dados Atividade/VRA_2024.csv', sep=';')
df_vra11 = pd.read_csv('dados/raw/Dados Voos Atualizados/VRA_2024_11.csv', sep=';')
df_vra12 = pd.read_csv('dados/raw/Dados Voos Atualizados/VRA_2024_12.csv', sep=';')

# %%
df_vra = padronizar_colunas(df_vra)
df_vra = remover_acentos_no_df(df_vra)
df_vra = padronizar_maiusculo(df_vra)
df_vra = padronizar_espacos_colunas(df_vra)
df_vra = padronizar_data02(df_vra,'REFERENCIA')
df_vra = df_vra[df_vra['SIGLA ICAO AEROPORTO DESTINO'].str.startswith('SB')]
df_vra = df_vra[df_vra['SIGLA ICAO AEROPORTO ORIGEM'].str.startswith('SB')]

# %%
df_vra11 = padronizar_colunas(df_vra11  )
df_vra11 = remover_acentos_no_df(df_vra11)
df_vra11 = padronizar_maiusculo(df_vra11)
df_vra11 = padronizar_espacos_colunas(df_vra11)
df_vra11 = padronizar_data02(df_vra11,'REFERENCIA')
df_vra11 = df_vra11[df_vra11['SIGLA ICAO AEROPORTO DESTINO'].str.startswith('SB')]
df_vra11 = df_vra11[df_vra11['SIGLA ICAO AEROPORTO ORIGEM'].str.startswith('SB')]

# %%
df_vra12 = padronizar_colunas(df_vra12  )
df_vra12 = remover_acentos_no_df(df_vra12)
df_vra12 = padronizar_maiusculo(df_vra12)
df_vra12 = padronizar_espacos_colunas(df_vra12)
df_vra12 = padronizar_data02(df_vra12,'REFERENCIA')
df_vra12 = df_vra12[df_vra12['SIGLA ICAO AEROPORTO DESTINO'].str.startswith('SB')]
df_vra12 = df_vra12[df_vra12['SIGLA ICAO AEROPORTO ORIGEM'].str.startswith('SB')]

# %%
#verificando se coluna é unica, ou seja, ID
df_vra['NUMERO VOO'].nunique() == len(df_vra)

# %%
df_main = pd.concat([df_vra, df_vra11, df_vra12], ignore_index=True)

# %%
print(len(df_main))

# %%
chaves_unicas = [
    'SIGLA ICAO EMPRESA AEREA',
    'NUMERO VOO',
    'PARTIDA REAL' 
]

df_main = df_main.drop_duplicates(
    subset=chaves_unicas,
    keep='first'
)

# %%
print(len(df_main))

# %%
df_aero

# %%
colunas_aero = ['CODIGO OACI', 'CIAD', 'NOME', 'MUNICIPIO ATENDIDO', 'UF', 'LATITUDE', 'LONGITUDE']
df_aero_filtrado = df_aero[colunas_aero].copy()    

# %%
# --- PASSO 1: JUNÇÃO PARA AEROPORTOS DE ORIGEM ---
# Primeiro, renomeia as colunas do df_aero_filtrado para forçar o sufixo ORIG
df_aero_orig = df_aero_filtrado.copy()
colunas_para_renomear = [col for col in df_aero_orig.columns if col != 'CODIGO OACI']
df_aero_orig = df_aero_orig.rename(columns={col: col + ' ORIG' for col in colunas_para_renomear})

df_main = pd.merge(
    df_main,
    df_aero_orig,
    how='left',
    left_on='SIGLA ICAO AEROPORTO ORIGEM',
    right_on='CODIGO OACI'
)

# --- PASSO 2: JUNÇÃO PARA AEROPORTOS DE DESTINO ---
# Renomeia as colunas do df_aero_filtrado para forçar o sufixo DEST
df_aero_dest = df_aero_filtrado.copy()
colunas_para_renomear = [col for col in df_aero_dest.columns if col != 'CODIGO OACI']
df_aero_dest = df_aero_dest.rename(columns={col: col + ' DEST' for col in colunas_para_renomear})

df_main = pd.merge(
    df_main,
    df_aero_dest,
    how='left',
    left_on='SIGLA ICAO AEROPORTO DESTINO',
    right_on='CODIGO OACI'
)

# %%
df_main

# %%
def extrair_e_converter(coord_str):
    """Extrai os valores da string DMS e converte para graus decimais."""
    # Garante que o valor não seja nulo ou inválido
    if pd.isna(coord_str) or not isinstance(coord_str, str):
        return None
    
    # Usa uma expressão regular para extrair os números e a direção
    match = re.match(r"(\d+)°\s*(\d+)'\s*(\d+)''\s*([NSWE])", coord_str)
    if match:
        graus = int(match.group(1))
        minutos = int(match.group(2))
        segundos = int(match.group(3))
        direcao = match.group(4)
        return dms_para_dd(graus, minutos, segundos, direcao)
    return None



# %%
colunas_para_converter = [
    'LATITUDE ORIG', 'LONGITUDE ORIG', 
    'LATITUDE DEST', 'LONGITUDE DEST'
]

for col in colunas_para_converter:
    df_main[col] = df_main[col].apply(extrair_e_converter)


# %%
df_main['DISTANCIA KM'] = df_main.apply(
    lambda row: haversine(
        row['LATITUDE ORIG'], 
        row['LONGITUDE ORIG'], 
        row['LATITUDE DEST'], 
        row['LONGITUDE DEST']
    ), 
    axis=1
)


# %%
df_main

# %%
df_main.columns

# %%
df_main.drop(columns=['DESCRICAO AEROPORTO ORIGEM', 'DESCRICAO AEROPORTO DESTINO'], inplace=True)

# %%
# Converte a coluna para o tipo datetime para permitir o particionamento
df_main['PARTIDA PREVISTA'] = pd.to_datetime(df_main['PARTIDA PREVISTA'], format='%d/%m/%Y %H:%M')

# Extrai o ano do DataFrame
ano = df_main['PARTIDA PREVISTA'].dt.year.iloc[0]

# %%
df_main

# %%
novos_nomes = {
    'SIGLA ICAO AEROPORTO DESTINO' : 'SIGLA AEROPORTO DESTINO',
    'MUNICIPIO ATENDIDO ORIG' : 'MUNICIPIO ORIG',
    'MUNICIPIO ATENDIDO DEST' : 'MUNICIPIO DEST',
    'SIGLA ICAO AEROPORTO ORIGEM' : 'SIGLA AEROPORTO ORIGEM',
}

df_main.rename(columns=novos_nomes, inplace=True)

# %%
df_rec = pd.read_csv('dados/raw/Dados Atividade/dadosconsumidor2024.csv', sep=';', header=1)

# %%
df_rec

# %%
df_rec = padronizar_colunas(df_rec)
df_rec = remover_acentos_no_df(df_rec)
df_rec = padronizar_maiusculo(df_rec)
df_rec = padronizar_espacos_colunas(df_rec)
df_rec = padronizar_data02(df_rec,'DATA ABERTURA')
df_rec = padronizar_data_hora(df_rec,'DATA E HORA RESPOSTA')
df_rec = padronizar_data02(df_rec,'DATA FINALIZACAO')
df_rec = padronizar_data02(df_rec,'PRAZO RESPOSTA')


# %%
df_rec.isnull().sum().sort_values(ascending=False)

# %%
print(len(df_rec))

# %%
df_rec = df_rec.drop(columns=['PRAZO ANALISE GESTOR (EM DIAS)'])

# %% [markdown]
# ## Exportando Arquivos tratados

# %%
for mes in range(1, 13):
    mes_str = f"{mes:02d}"  # Formato com 2 dígitos, preenchendo com zero à esquerda
   
    # Filtra o DataFrame para o mês atual
    df_mes = df_main[df_main['PARTIDA PREVISTA'].dt.month == mes].copy()
   
    if not df_mes.empty:
        # AQUI ESTÁ A CHAVE: converte a coluna de volta para string no formato desejado
        df_mes['PARTIDA PREVISTA'] = df_mes['PARTIDA PREVISTA'].dt.strftime('%d/%m/%Y %H:%M')
       
        # Salva o DataFrame filtrado em um arquivo CSV
        nome_arquivo = f'dados/trusted/voos/dados_voo_{int(ano)}{mes_str}.csv'  # Convertendo ano para int
        df_mes.to_csv(nome_arquivo, index=False)
       
        print(f"Arquivo '{nome_arquivo}' criado com sucesso.")
    else:
        print(f"Não há dados para o mês {mes_str}.")

# %%
# 1. Converte a coluna para o formato de data para podermos agrupar
df_rec['DATA ABERTURA'] = pd.to_datetime(df_rec['DATA ABERTURA'], format='%d/%m/%Y')

# 2. Agrupa o DataFrame por mês
grouped = df_rec.groupby(df_rec['DATA ABERTURA'].dt.to_period('M'))

# 3. Itera sobre cada grupo (cada mês)
for period, group_df in grouped:
    # Cria uma cópia para evitar o SettingWithCopyWarning
    df_mes = group_df.copy()

    # --- LINHA ADICIONADA AQUI ---
    # 4. Re-formata a coluna de data para o padrão DD/MM/AAAA antes de salvar
    df_mes['DATA ABERTURA'] = df_mes['DATA ABERTURA'].dt.strftime('%d/%m/%Y')
    
    # 5. Cria o nome do arquivo
    filename = f"dados/trusted/reclamacoes/reclamacoes{period.strftime('%Y%m')}.csv"

    # 6. Salva o grupo de dados no arquivo CSV
    df_mes.to_csv(filename, index=False)
    print(f"Arquivo '{filename}' criado com sucesso.")


# %%
df_empresas.to_csv('dados/trusted/empresas/empresas_tratadas.csv', index=False)


