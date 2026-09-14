from src.ingestion import ingest_data
from src.cleaning import clean_data
from src.transformation import transform_data

df = ingest_data()
df = clean_data(df)
df = transform_data(df)

text_columns = [
    "Order_ID",
    "Customer_ID",
    "Product_ID",
    "Payment_Method",
    "Source_File",
]

for column in text_columns:
    if column not in df.columns:
        continue

    values = df[column].fillna("").astype(str)

    print(f"\n--- {column} ---")
    print("Maximum length:", values.str.len().max())

    longest = df.loc[values.str.len().nlargest(10).index, [column]].assign(
        _length=values.loc[values.str.len().nlargest(10).index].values
    )

    print(longest.to_string(index=False))
