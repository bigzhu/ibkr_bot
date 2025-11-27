  WITH
  h1 AS (
      SELECT
        date(time) AS date,
        COUNT(*) AS order_count,
        SUM(COALESCE(CAST(profit AS REAL), 0)) AS total_profit,
        SUM(COALESCE(CAST(commission AS REAL), 0)) AS total_commission
      FROM filled_orders_1h_buy_interval
      GROUP BY date(time)
  ),
  h4 AS (
      SELECT
        date(time) AS date,
        COUNT(*) AS order_count,
        SUM(COALESCE(CAST(profit AS REAL), 0)) AS total_profit,
        SUM(COALESCE(CAST(commission AS REAL), 0)) AS total_commission
      FROM filled_orders_4h_buy_interval
      GROUP BY date(time)
  )
  SELECT *
  FROM (
  SELECT
      COALESCE(h4.date, h1.date)                                        AS date,
      COALESCE(h4.total_profit, 0) - COALESCE(h1.total_profit, 0)       AS diff_profit,
      COALESCE(h4.total_profit, 0)                                      AS h4_total_profit,
      COALESCE(h1.total_profit, 0)                                      AS h1_total_profit,
      COALESCE(h4.order_count, 0)                                       AS h4_order_count,
      COALESCE(h1.order_count, 0)                                       AS h1_order_count,
      COALESCE(h4.total_commission, 0)                                  AS h4_total_commission,
      COALESCE(h1.total_commission, 0)                                  AS h1_total_commission
  FROM h4
  LEFT JOIN h1 ON h1.date = h4.date

  UNION ALL

  SELECT
      COALESCE(h4.date, h1.date)                                        AS date,
      COALESCE(h4.total_profit, 0) - COALESCE(h1.total_profit, 0)       AS diff_profit,
      COALESCE(h4.total_profit, 0)                                      AS h4_total_profit,
      COALESCE(h1.total_profit, 0)                                      AS h1_total_profit,
      COALESCE(h4.order_count, 0)                                       AS h4_order_count,
      COALESCE(h1.order_count, 0)                                       AS h1_order_count,
      COALESCE(h4.total_commission, 0)                                  AS h4_total_commission,
      COALESCE(h1.total_commission, 0)                                  AS h1_total_commission
  FROM h1
  LEFT JOIN h4 ON h4.date = h1.date
  WHERE h4.date IS NULL
  ) t;



select  sum(profit)-sum(commission) as p, sum(commission) as c from filled_orders_1h_buy_interval; --7718.571575870001
select  sum(profit)-sum(commission) as p, sum(commission) as c from filled_orders_4h_buy_interval; --6430.359264809999
select  sum(profit)-sum(commission) as p, sum(commission) as c from filled_orders_6h_buy_interval; --5806.5732183499995  min_usdc: 4.028130000017626
select  sum(profit)-sum(commission) as p, sum(commission) as c from filled_orders_8h_buy_interval; --5148.1412303
select  sum(profit)-sum(commission) as p, sum(commission) as c from filled_orders_24h_buy_interval; --3378.9674061200003  min_usdc: 4691.892270000014


create table filled_orders_6h_buy_interval as select * from filled_orders;
create table trading_logs_6h as select * from trading_logs;

select min(user_balance ) from trading_logs where side = 'BUY' 
