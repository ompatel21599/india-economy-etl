import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

engine = create_engine(
    f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
)

print("Connecting to PostgreSQL...")

df = pd.read_csv(r"C:\Users\Dell\OneDrive - Sahana System Limited\Desktop\india-economy-etl\data\india_economy_clean.csv")

print(f"Loaded {len(df)} rows from CSV")

df.to_sql(
    'india_economy_data',
    engine,
    if_exists='replace',
    index=False
)

print("Data loaded to PostgreSQL successfully!")

with engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM india_economy_data"))
    count = result.fetchone()[0]
    print(f"Total rows in database: {count}")

print("\nFirst 5 rows in database:")
df_check = pd.read_sql("SELECT * FROM india_economy_data LIMIT 5", engine)
print(df_check)