import io, pandas as pd
from .deps import ch_query

TABLES={
  "shipments": "fact_shipments",
  "inventory": "fact_inventory",
  "orders": "fact_orders",
  "locations": "dim_location",
  "carriers": "dim_carrier",
  "items": "dim_item",
}

def ingest_csv(kind: str, tenant_id: str, file_bytes: bytes)->int:
    if kind not in TABLES: raise ValueError("Unknown kind")
    df=pd.read_csv(io.BytesIO(file_bytes))
    df.insert(0, "tenant_id", tenant_id)
    for col in df.columns:
        if col.endswith(("_ts","_date")) or col in ("ship_date",):
            try: df[col]=pd.to_datetime(df[col])
            except: pass
    table=TABLES[kind]
    cols=",".join(df.columns)
    def to_tsv_row(values):
        import pandas as pd
        return "\t".join("" if pd.isna(x) else str(x) for x in values)
    values = "\n".join([to_tsv_row(row) for row in df.itertuples(index=False, name=None)])
    sql=f"INSERT INTO scm.{table} ({cols}) FORMAT TSV\n"+values
    ch_query(sql); return len(df)
