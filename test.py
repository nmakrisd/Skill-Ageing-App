import pandas as pd

df = pd.read_csv("monthly_top100_timeseries.csv")
print(df.columns.tolist())
