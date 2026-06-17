import requests
import pandas as pd
import os

print("Script started...")

BASE_URL = "https://api.worldbank.org/v2/country/IN/indicator/"

INDICATORS = {
    "NY.GDP.MKTP.KD.ZG": "gdp_growth_rate",
    "FP.CPI.TOTL.ZG": "inflation_rate",
    "SL.UEM.TOTL.ZS": "unemployment_rate",
    "BX.KLT.DINV.WD.GD.ZS": "fdi_inflow",
    "GC.DOD.TOTL.GD.ZS": "government_debt"
}

def fetch_indicator(indicator_code, indicator_name):
    try:
        url = f"{BASE_URL}{indicator_code}?format=json&per_page=60&mrv=60"
        print(f"Fetching {indicator_name} from {url}")
        response = requests.get(url, timeout=10)
        print(f"Status code: {response.status_code}")
        data = response.json()
        records = data[1]
        rows = []
        for record in records:
            rows.append({
                "year": record["date"],
                "value": record["value"],
                "indicator": indicator_name
            })
        df = pd.DataFrame(rows)
        print(f"Got {len(df)} rows for {indicator_name}")
        return df
    except Exception as e:
        print(f"Error fetching {indicator_name}: {e}")
        return pd.DataFrame()

def fetch_all_indicators():
    all_data = []
    for code, name in INDICATORS.items():
        df = fetch_indicator(code, name)
        all_data.append(df)
    final_df = pd.concat(all_data, ignore_index=True)
    os.makedirs("data", exist_ok=True)
    final_df.to_csv("data/india_economy_raw.csv", index=False)
    print("Data saved successfully!")
    print(final_df.head(10))

if __name__ == "__main__":
    fetch_all_indicators()


