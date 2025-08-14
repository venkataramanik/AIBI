CREATE DATABASE IF NOT EXISTS scm;

CREATE TABLE IF NOT EXISTS scm.fact_shipments
(
  tenant_id String,
  shipment_id String,
  ship_date Date,
  pickup_ts DateTime64(3),
  delivery_ts DateTime64(3),
  origin_id String,
  dest_id String,
  miles Float64,
  mode LowCardinality(String),
  carrier_id String,
  status LowCardinality(String),
  cost_total Float64,
  weight Float64,
  volume Float64
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(ship_date)
ORDER BY (tenant_id, ship_date, carrier_id);

CREATE TABLE IF NOT EXISTS scm.fact_inventory
(
  tenant_id String,
  sku_id String,
  location_id String,
  as_of_date Date,
  on_hand Float64,
  reserved Float64,
  inbound Float64,
  unit_cost Float64
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(as_of_date)
ORDER BY (tenant_id, as_of_date, sku_id);

CREATE TABLE IF NOT EXISTS scm.fact_orders
(
  tenant_id String,
  order_id String,
  order_ts DateTime64(3),
  promised_ts DateTime64(3),
  ship_ts DateTime64(3),
  item_id String,
  qty Float64,
  revenue Float64,
  warehouse_id String,
  carrier_id String
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(toDate(order_ts))
ORDER BY (tenant_id, toDate(order_ts), carrier_id);

CREATE TABLE IF NOT EXISTS scm.dim_location
(
  tenant_id String,
  location_id String,
  name String,
  type LowCardinality(String),
  city String,
  state String,
  country String,
  lat Float64,
  lon Float64
)
ENGINE = ReplacingMergeTree()
ORDER BY (tenant_id, location_id);

CREATE TABLE IF NOT EXISTS scm.dim_carrier
(
  tenant_id String,
  carrier_id String,
  scac String,
  name String,
  mode LowCardinality(String)
)
ENGINE = ReplacingMergeTree()
ORDER BY (tenant_id, carrier_id);

CREATE TABLE IF NOT EXISTS scm.dim_item
(
  tenant_id String,
  sku_id String,
  sku String,
  category LowCardinality(String),
  uom LowCardinality(String)
)
ENGINE = ReplacingMergeTree()
ORDER BY (tenant_id, sku_id);

CREATE OR REPLACE VIEW scm.vw_carrier_kpi AS
SELECT
  s.tenant_id,
  toDate(s.delivery_ts) AS ship_date,
  c.name AS carrier_name,
  avg( if(timestampDiff('hour', s.pickup_ts, s.delivery_ts) <= 72, 1, 0) ) AS on_time_rate,
  avg( s.cost_total / nullIf(s.miles, 0) ) AS cost_per_mile,
  count() AS shipments
FROM scm.fact_shipments s
LEFT JOIN scm.dim_carrier c
  ON c.tenant_id = s.tenant_id AND c.carrier_id = s.carrier_id
GROUP BY s.tenant_id, ship_date, carrier_name;

CREATE OR REPLACE VIEW scm.vw_lane_perf AS
SELECT
  s.tenant_id,
  o.state AS origin_state,
  d.state AS dest_state,
  avg(s.cost_total / nullIf(s.miles, 0)) AS avg_cost_mi,
  quantileExactWeighted(0.95)(timestampDiff('hour', s.pickup_ts, s.delivery_ts), 1) AS p95_transit,
  count() AS volume
FROM scm.fact_shipments s
LEFT JOIN scm.dim_location o
  ON o.tenant_id = s.tenant_id AND o.location_id = s.origin_id
LEFT JOIN scm.dim_location d
  ON d.tenant_id = s.tenant_id AND d.location_id = s.dest_id
GROUP BY s.tenant_id, origin_state, dest_state;

CREATE OR REPLACE VIEW scm.vw_inventory_health AS
WITH usage AS (
  SELECT tenant_id, item_id AS sku_id, greatest(avg(qty), 0.0001) AS avg_daily
  FROM scm.fact_orders
  GROUP BY tenant_id, sku_id
)
SELECT
  i.tenant_id,
  toDate(i.as_of_date) AS as_of_date,
  it.sku,
  i.location_id,
  (i.on_hand + i.inbound - i.reserved) / nullIf(u.avg_daily, 0) AS days_of_supply,
  365.0 * sum(i.on_hand) / greatest(sum(i.unit_cost), 0.0001) AS turns,
  if( (i.on_hand + i.inbound - i.reserved) / nullIf(u.avg_daily, 0) < 10, 1, 0) AS risk_flag
FROM scm.fact_inventory i
LEFT JOIN usage u USING (tenant_id, sku_id)
LEFT JOIN scm.dim_item it USING (tenant_id, sku_id)
GROUP BY i.tenant_id, as_of_date, it.sku, i.location_id, u.avg_daily, i.on_hand, i.inbound, i.reserved, i.unit_cost;
