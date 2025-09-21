import math
import pandas as pd 
import win32com.client as win32
import unicodedata
import os
import boto3

regiao = 'us-east-1'
nome_bucket_trusted = 'trusted-analise-voos-grupo02'

client = boto3.client('s3', region_name=regiao)

# Mapeamento de pastas locais para pastas do S3


pastas_para_enviar = {
    "dados/trusted/empresas_aereas/": "empresas_aereas/",
    "dados/trusted/reclamacoes/": "reclamacoes/",
    "dados/trusted/voos/": "voos/"
}




# Diretório onde o notebook está rodando
base_dir = os.getcwd()

caminho_xls = os.path.join(base_dir, "dados", "raw", "Dados Atividade", "aerodromospublicos.xls")
caminho_xlsx = os.path.join(base_dir, "dados", "raw", "Dados Atividade", "aerodromospublicos.xlsx")

print(caminho_xls)


def converter_xls_para_xlsx(caminho_relativo_xls):
    base_dir = os.getcwd()
    arquivo_xls = os.path.join(base_dir, caminho_relativo_xls)
    arquivo_xlsx = arquivo_xls.replace(".xls", ".xlsx")
    
    excel = win32.gencache.EnsureDispatch('Excel.Application')
    wb = excel.Workbooks.Open(arquivo_xls)
    wb.SaveAs(arquivo_xlsx, FileFormat=51)  # 51 = formato xlsx
    wb.Close()
    excel.Application.Quit()

    print(f"Conversão concluída: {arquivo_xlsx}")

# Exemplo de uso
converter_xls_para_xlsx(r"dados\raw\Dados Atividade\aerodromospublicos.xls")


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
    
    # Fórmula de Haversine
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c


def remover_acentos(texto):
    """Remove acentos de um texto e converte para maiúsculas"""
    if isinstance(texto, str):
        # Normaliza o texto (decompõe caracteres acentuados)
        texto = unicodedata.normalize('NFKD', texto)
        # Remove os diacríticos (acentos)
        texto = u"".join([c for c in texto if not unicodedata.combining(c)])
        # Converte para maiúsculas
        return texto.upper()
    return texto

# Carregar os dados
aeroportos = pd.read_excel(r"dados\raw\Dados Atividade\aerodromospublicos.xlsx", engine="openpyxl", skiprows=2)
empresas = pd.read_excel(r"dados\raw\Dados Atividade\Empresas Aereas.xlsx", engine="openpyxl")

# Padronizar nomes das colunas (maiúsculo, sem acentos, sem espaços)
aeroportos.columns = [remover_acentos(col.strip().replace(" ", "_")) for col in aeroportos.columns]
empresas.columns = [remover_acentos(col.strip().replace(" ", "_")) for col in empresas.columns]

# Aplicar a função em todas as colunas do tipo objeto (texto)
for col in aeroportos.select_dtypes(include=['object']).columns:
    aeroportos[col] = aeroportos[col].apply(remover_acentos)

for col in empresas.select_dtypes(include=['object']).columns:
    empresas[col] = empresas[col].apply(remover_acentos)

print("\nColunas do DataFrame aeroportos:")
print(aeroportos.columns.tolist())
print("\nColunas do DataFrame empresas:")
print(empresas.columns.tolist())

print("\nExemplo dos dados após remoção de acentos:")
print("\nAeroportos:")
print(aeroportos.head())
print("\nEmpresas:")
print(empresas.head())



# Função auxiliar para extrair valores de coordenadas em formato DMS
def extrair_dms(coord_str):
    """Extrai graus, minutos, segundos e direção de uma string no formato '8° 20' 55'' S'"""
    import re
    
    # Extrair números e direção
    match = re.match(r"(\d+)° (\d+)' (\d+)'' ([NSWE])", coord_str)
    if match:
        graus = int(match.group(1))
        minutos = int(match.group(2))
        segundos = int(match.group(3))
        direcao = match.group(4)
        return dms_para_dd(graus, minutos, segundos, direcao)
    return None

# Converter coordenadas sobrescrevendo as colunas existentes
if "LATITUDE" in aeroportos.columns and "LONGITUDE" in aeroportos.columns:
    aeroportos["LATITUDE"] = aeroportos["LATITUDE"].apply(extrair_dms)
    aeroportos["LONGITUDE"] = aeroportos["LONGITUDE"].apply(extrair_dms)
    
print("\nPrimeiros registros com coordenadas convertidas:")
print(aeroportos[["NOME", "LATITUDE", "LONGITUDE"]].head())


if "tipo_voo" in empresas.columns:
    empresas_domesticas = empresas[empresas["tipo_voo"] == "DOMESTICO"]
else:
    empresas_domesticas = empresas.copy()
    
    
if {"latitude", "longitude"}.issubset(aeroportos.columns):
    # Usar as coordenadas convertidas
    lat1 = aeroportos.loc[0, "latitude"]
    lon1 = aeroportos.loc[0, "longitude"]
    lat2 = aeroportos.loc[1, "latitude"]
    lon2 = aeroportos.loc[1, "longitude"]
    
    distancia = haversine(lat1, lon1, lat2, lon2)
    print(f"Distância entre {aeroportos.loc[0,'nome']} e {aeroportos.loc[1,'nome']}: {distancia:.2f} km")
    
# Debugging: verificar os valores e tipos de dados
print("Tipos de dados das colunas:")
print(aeroportos[["LATITUDE", "LONGITUDE"]].dtypes)
print("\nPrimeiros registros:")
print(aeroportos[["NOME", "LATITUDE", "LONGITUDE"]].head())


aeroportos.to_excel("dados/trusted/empresas_aereas/aeroportos_tratados.xlsx", index=False)
empresas_domesticas.to_excel("dados/trusted/empresas_aereas/empresas_domesticas_tratadas.xlsx", index=False)

print("✅ Tratamento concluído! Arquivos exportados:")
print("- dados/trusted/empresas_aereas/aeroportos_tratados.xlsx")
print("- dados/trusted/empresas_aereas/empresas_domesticas_tratadas.xlsx")


def limpar_texto(texto):
    """Remove acentos, converte para maiúscula e limpa espaços"""
    if not isinstance(texto, str) or texto == 'nan':
        return texto
    texto = unicodedata.normalize('NFKD', texto)
    texto = ''.join(c for c in texto if not unicodedata.combining(c))
    return texto.upper().strip()

print("✅ Bibliotecas carregadas e função auxiliar definida!")



# TRATAMENTO - RECLAMAÇÕES
print(" Processando reclamações...")

# Carregar e tratar em uma etapa
reclamacoes = pd.read_csv(
    r"dados\raw\Dados Atividade\dadosconsumidor2024.csv", 
    sep=';', encoding='utf-8', skiprows=1
)
# Padronizar colunas e dados
reclamacoes.columns = [limpar_texto(col.replace(' ', '_')) for col in reclamacoes.columns]

# Aplicar limpeza apenas em colunas de texto (exceto datas)
for col in reclamacoes.select_dtypes(include=['object']).columns:
    if not any(x in col.lower() for x in ['data', 'hora']):
        reclamacoes[col] = reclamacoes[col].apply(limpar_texto)

# Converter datas
date_cols = [col for col in reclamacoes.columns if 'DATA' in col]
for col in date_cols:
    if 'HORA' in col:
        reclamacoes[col] = pd.to_datetime(reclamacoes[col], errors='coerce').dt.strftime('%d/%m/%Y %H:%M:%S')
    else:
        reclamacoes[col] = pd.to_datetime(reclamacoes[col], errors='coerce').dt.strftime('%d/%m/%Y')

# Filtrar apenas dados aéreos
aereo = reclamacoes[(reclamacoes['AREA'] == 'TRANSPORTES') & (reclamacoes['ASSUNTO'] == 'AEREO')].copy()

print(f" {len(aereo)} reclamações aéreas processadas")


# TRATAMENTO COMPLETO - VOOS
print(" Processando voos...")

# Carregar voos 
voos = pd.read_csv(
    r"dados\raw\Dados Atividade\VRA_2024.csv", 
    sep=';', encoding='utf-8', nrows=100000  # Limitar para demonstração
)

# Padronizar colunas
voos.columns = [limpar_texto(col.replace(' ', '_')) for col in voos.columns]

# Aplicar limpeza em colunas de texto (exceto datas)
for col in voos.select_dtypes(include=['object']).columns:
    if not any(x in col.lower() for x in ['partida', 'chegada', 'prevista', 'real']):
        voos[col] = voos[col].apply(limpar_texto)

# Converter datas/horas
datetime_cols = [col for col in voos.columns if any(x in col.upper() for x in ['PARTIDA', 'CHEGADA'])]
for col in datetime_cols:
    voos[col] = pd.to_datetime(voos[col], errors='coerce').dt.strftime('%d/%m/%Y %H:%M:%S')

# Filtrar voos domésticos (códigos ICAO brasileiros começam com 'SB')
domesticos = voos[
    (voos['SIGLA_ICAO_AEROPORTO_ORIGEM'].str.startswith('SB', na=False)) &
    (voos['SIGLA_ICAO_AEROPORTO_DESTINO'].str.startswith('SB', na=False))
].copy()

print(f" {len(domesticos)} voos domésticos processados ({len(domesticos)/len(voos)*100:.1f}%)")



# PARTICIONAMENTO MENSAL
print(" Iniciando particionamento mensal...")

def particionar_por_mes(df, nome_base, coluna_data, formato_data='%d/%m/%Y'):
    """Função para particionar dados por mês em pastas específicas"""
    df_temp = df.copy()
    df_temp['DATA_TEMP'] = pd.to_datetime(df_temp[coluna_data], format=formato_data, errors='coerce')
    df_temp = df_temp.dropna(subset=['DATA_TEMP'])
    df_temp['ANO_MES'] = df_temp['DATA_TEMP'].dt.strftime('%Y%m')
    
    # Definir pasta de saída com base no nome_base
    if 'reclamacao' in nome_base.lower():
        pasta_destino = os.path.join("dados", "trusted", "reclamacoes")
    else:
        pasta_destino = os.path.join("dados", "trusted", "voos")
    
    # Criar pasta caso não exista
    os.makedirs(pasta_destino, exist_ok=True)

    arquivos = []
    for mes in sorted(df_temp['ANO_MES'].unique()):
        dados_mes = df_temp[df_temp['ANO_MES'] == mes].drop(['DATA_TEMP', 'ANO_MES'], axis=1)
        nome_arquivo = f"{nome_base}_{mes}.csv"
        caminho_arquivo = os.path.join(pasta_destino, nome_arquivo)
        dados_mes.to_csv(caminho_arquivo, index=False, sep=',', encoding='utf-8')
        arquivos.append(caminho_arquivo)
        print(f" {caminho_arquivo}: {len(dados_mes)} registros")
    
    return arquivos

# Particionar reclamações
coluna_data_rec = next((col for col in aereo.columns if 'DATA' in col), None)
rec_files = particionar_por_mes(aereo, 'reclamacao', coluna_data_rec)

# Particionar voos 
coluna_data_voo = 'PARTIDA_PREVISTA' if 'PARTIDA_PREVISTA' in domesticos.columns else 'PARTIDA_REAL'
voo_files = particionar_por_mes(domesticos, 'dados_voo', coluna_data_voo, '%d/%m/%Y %H:%M:%S')

print(f"\n RESUMO: {len(rec_files)} reclamações + {len(voo_files)} voos = {len(rec_files) + len(voo_files)} arquivos")


def subir_arquivo(bucket_name, file_path_local, file_path_s3):
    """
    Sobe um arquivo para um bucket S3.
    :param bucket_name: Nome do bucket de destino.
    :param file_path_local: Caminho completo do arquivo local.
    :param file_path_s3: Caminho e nome do arquivo no S3 (ex: 'pasta/nome_arquivo.csv').
    """
    try:
        print(f"Enviando '{file_path_local}' para S3 em '{file_path_s3}'...")
        client.upload_file(file_path_local, bucket_name, file_path_s3)
        print(f"Upload de '{file_path_local}' concluído!")
    except Exception as e:
        print(f"Erro ao enviar o arquivo '{file_path_local}': {e}")


for pasta_local, pasta_s3 in pastas_para_enviar.items():
        # Verifica se o diretório local existe
        if not os.path.isdir(pasta_local):
            print(f"Aviso: Diretório local '{pasta_local}' não encontrado. Pulando...")
            continue

        for nome_arquivo in os.listdir(pasta_local):
            # Filtra apenas arquivos (não subdiretórios)
            if os.path.isfile(os.path.join(pasta_local, nome_arquivo)):
                caminho_local_completo = os.path.join(pasta_local, nome_arquivo)
                
                # Monta o caminho de destino no S3
                caminho_s3_completo = os.path.join(pasta_s3, nome_arquivo).replace("\\", "/")
                
                # Chama a função para subir o arquivo
                subir_arquivo(nome_bucket_trusted, caminho_local_completo, caminho_s3_completo)

print("\nProcesso de upload concluído.")