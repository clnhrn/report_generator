import os
from typing import Union
import pandas as pd


def load_excel_file(path: Union[str, os.PathLike]) -> pd.DataFrame:
    with open(path, "rb") as excelfile:
        df = pd.read_excel(excelfile, engine="openpyxl", sheet_name=0)

    return df


def select_columns_by_index(
    df, columns: list = None, correct_headers: bool = True
) -> pd.DataFrame:
    if correct_headers == False:
        # select row to be used as headers
        df.columns = df.iloc[1]
        df = df[1:]
        df = df.reindex(df.index.drop(1)).reset_index(drop=True)

    df = df.iloc[:, columns]

    return df


def select_columns_by_name(
    df, columns: list = None, correct_headers: bool = True
) -> pd.DataFrame:
    if correct_headers == False:
        # select row to be used as headers
        df.columns = df.iloc[1]
        df = df[1:]
        df = df.reindex(df.index.drop(1)).reset_index(drop=True)

    df = df[columns]

    return df
