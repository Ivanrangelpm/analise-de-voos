  ''' QUERY 1  '''
select * from datamart01

  ''' QUERY 2  '''

SELECT
  "empresa aerea" AS metrica,
  AVG("numero de assentos") AS "Capacidade Média"
FROM 
  voos
GROUP BY 
  "empresa aerea"
ORDER BY 
  "Capacidade Média" DESC


  ''' QUERY 3  '''

SELECT
  -- Soma dos seus assentos, multiplica por 100, e divide pelo total de assentos de todas as empresas
  (SUM(CASE WHEN "empresa aerea" = 'LATAM AIRLINES (TAM)' THEN "numero de assentos" ELSE 0 END) * 100.0) / SUM("numero de assentos")
FROM
  voos


  '''QUERY 4 '''

  SELECT
  -- Coloque o nome da sua empresa aqui dentro das aspas simples
  (COUNT(CASE WHEN "empresa aerea" = 'LATAM AIRLINES (TAM)' THEN 1 END) * 100.0) / COUNT("numero voo")
FROM
  voos

  '''QUERY 5'''

  SELECT
  -- Conta voos que NÃO foram cancelados, multiplica por 100, e divide pelo total de voos da sua empresa
  (COUNT(CASE WHEN "situacao voo" != 'CANCELADO' THEN 1 END) * 100.0) / COUNT(*)
FROM
  voos
WHERE
  "empresa aerea" = 'LATAM AIRLINES (TAM)'