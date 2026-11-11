# -*- coding: utf-8 -*-
""" use package polaris"""

import logging
import string
import sys
from pathlib import Path

import polars as pl

# Excel-файл ищется в той же папке, где лежит эта программа
FILE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "lab5_variant18.xlsx"
if not FILE.exists():
    sys.exit(f"Файл не найден: {FILE}\nПоложите lab5_variant18.xlsx в папку {Path(__file__).parent}")
SHEET = "Числа"


def read_sheet(path):
    """Читает лист без строки заголовков и даёт колонкам имена букв Excel
    (A, B, C, ...), чтобы к ним можно было обращаться как в таблице."""
    # Пустая колонка D вызывает предупреждение библиотеки fastexcel
    # ("Could not determine dtype ..."), которое печатается через logging.
    # На результат оно не влияет, поэтому на время чтения его отключаем.
    logging.disable(logging.WARNING)
    try:
        df = pl.read_excel(path, sheet_name=SHEET, has_header=False,
                           drop_empty_rows=False, drop_empty_cols=False)
    except TypeError:
        # старые версии polars не знают drop_empty_rows/drop_empty_cols
        df = pl.read_excel(path, sheet_name=SHEET, has_header=False)
    finally:
        logging.disable(logging.NOTSET)
    letters = list(string.ascii_uppercase)
    if df.width == 25:
        # пустая колонка D была отброшена при чтении
        names = letters[:3] + letters[4:26]
    else:
        names = letters[:df.width]
    return df.rename(dict(zip(df.columns, names)))


df = read_sheet(FILE)

# ---------- B1:C2 — без границ ----------
# только строки 1-2: колонка A у них пустая (у строк X1..X12 в A стоит "X1 =" ...)
top = df.filter(pl.col("A").is_null() & pl.col("B").is_in(["A =", "C ="])).select("B", "C")
for label, value in top.iter_rows():
    print(f"{label} {int(float(value))}")
print()

# ---------- A4:Y15 без колонки F — с границами ----------
bit_cols = [c for c in string.ascii_uppercase[6:25]]   # G..Y
table = (
    df.filter(pl.col("A").cast(pl.Utf8).str.starts_with("X"))   # строки X1..X12
      .select(["A", "B", "C", "E"] + bit_cols)                  # F не выбираем
      .with_columns(
          pl.col("C").cast(pl.Float64).cast(pl.Int64),
          # биты 0/1 приводим к целым, точки-разделители оставляем строками
          *[pl.col(c).cast(pl.Utf8).str.replace(r"\.0$", "") for c in bit_cols],
      )
)

with pl.Config(
    tbl_formatting="UTF8_FULL",          # рамки вокруг каждой ячейки
    tbl_hide_column_data_types=True,
    tbl_hide_dataframe_shape=True,
    tbl_rows=-1,
    tbl_cols=-1,
    tbl_width_chars=250,
    tbl_cell_alignment="RIGHT",
):
    print(table)
