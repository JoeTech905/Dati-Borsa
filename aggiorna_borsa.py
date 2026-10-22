from datetime import datetime
import json
import time
import pandas as pd
import yfinance as yf

# 1. FTSE MIB COMPLETO
TICKERS_FTSEMIB = [
    "A2A.MI",
    "AMP.MI",
    "AZM.MI",
    "BPE.MI",
    "BMPS.MI",
    "BGN.MI",
    "CPR.MI",
    "ENEL.MI",
    "ENI.MI",
    "ERG.MI",
    "EXO.MI",
    "FCA.MI",
    "G.MI",
    "HER.MI",
    "IGD.MI",
    "IP.MI",
    "ISP.MI",
    "LDO.MI",
    "MB.MI",
    "MONC.MI",
    "NEXI.MI",
    "PIRC.MI",
    "PRY.MI",
    "RACE.MI",
    "REC.MI",
    "SFER.MI",
    "SRG.MI",
    "STLA.MI",
    "STM.MI",
    "TEN.MI",
    "TIT.MI",
    "TRN.MI",
    "UCG.MI",
    "UNI.MI",
    "UNIP.MI",
]

# 2. NASDAQ ESTESO (Componenti ufficiali + Mid-Cap / Growth Tech)
TICKERS_NASDAQ = [
    "AAPL",
    "ABNB",
    "ADBE",
    "ADI",
    "ADP",
    "ADSK",
    "AEP",
    "AMAT",
    "AMD",
    "AMGN",
    "AMZN",
    "ANSS",
    "ARM",
    "ASML",
    "AVGO",
    "AZN",
    "BIIB",
    "BKNG",
    "BKR",
    "CDNS",
    "CDW",
    "CEG",
    "CHTR",
    "CMCSA",
    "COIN",
    "COST",
    "CPRT",
    "CRWD",
    "CSCO",
    "CSX",
    "CTAS",
    "CTSH",
    "DDOG",
    "DLTR",
    "DXCM",
    "EA",
    "EBAY",
    "ENPH",
    "EXC",
    "FAST",
    "FTNT",
    "GEHC",
    "GILD",
    "GOOG",
    "GOOGL",
    "HON",
    "IDXX",
    "ILMN",
    "INTC",
    "INTU",
    "ISRG",
    "KDP",
    "KHC",
    "KLAC",
    "LCID",
    "LRCX",
    "LULU",
    "MAR",
    "MCHP",
    "MDLZ",
    "MELI",
    "META",
    "MNST",
    "MRNA",
    "MRVL",
    "MSFT",
    "MU",
    "NFLX",
    "NVDA",
    "NXPI",
    "ODFL",
    "OKTA",
    "ON",
    "ORLY",
    "PANW",
    "PAYX",
    "PCAR",
    "PDD",
    "PEP",
    "PLTR",
    "QCOM",
    "REGN",
    "ROP",
    "ROST",
    "SBUX",
    "SHOP",
    "SMCI",
    "SNPS",
    "SPLK",
    "SQ",
    "TEAM",
    "TMUS",
    "TSLA",
    "TXN",
    "UBER",
    "VRSK",
    "VRTX",
    "WBD",
    "WDAY",
    "ZM",
    "ZS",
]

# 3. S&P 500 SELEZIONE TOP & GROWTH
TICKERS_SP500 = [
    "AAPL",
    "ABBV",
    "ABT",
    "ACN",
    "ADBE",
    "AMD",
    "AMGN",
    "AMZN",
    "AXP",
    "BA",
    "BAC",
    "BLK",
    "BMY",
    "BRK-B",
    "C",
    "CAT",
    "CL",
    "CMCSA",
    "COP",
    "COST",
    "CRM",
    "CSCO",
    "CVS",
    "CVX",
    "DE",
    "DHR",
    "DIS",
    "DOW",
    "GE",
    "GILD",
    "GOOGL",
    "GS",
    "HD",
    "HON",
    "IBM",
    "INTC",
    "JNJ",
    "JPM",
    "KO",
    "LIN",
    "LLY",
    "LMT",
    "MA",
    "MCD",
    "MDT",
    "META",
    "MMM",
    "MO",
    "MRK",
    "MS",
    "MSFT",
    "NEE",
    "NFLX",
    "NKE",
    "NVDA",
    "ORCL",
    "PEP",
    "PFE",
    "PG",
    "PLTR",
    "PM",
    "QCOM",
    "RTX",
    "SBUX",
    "SHOP",
    "SLB",
    "SMCI",
    "SO",
    "SPGI",
    "T",
    "TGT",
    "TMO",
    "TMUS",
    "TSLA",
    "TXN",
    "UBER",
    "UNH",
    "UNP",
    "UPS",
    "USB",
    "V",
    "VZ",
    "WFC",
    "WMT",
    "XOM",
]


def scarica_in_micro_blocchi(lista_ticker, dim_blocco=40):
  df_totale_unito = pd.DataFrame()
  for i in range(0, len(lista_ticker), dim_blocco):
    sotto_lista = lista_ticker[i : i + dim_blocco]
    try:
      df_chunk = yf.download(
          sotto_lista,
          period="6mo",
          interval="1d",
          progress=False,
          group_by="ticker",
      )
      if not df_chunk.empty:
        if df_totale_unito.empty:
          df_totale_unito = df_chunk
        else:
          df_totale_unito = pd.concat([df_totale_unito, df_chunk], axis=1)
    except Exception:
      pass
    time.sleep(1)
  return df_totale_unito


def analizza_e_salva_mercato(nome_file, lista_ticker):
  print(f"\nScansione estesa per {nome_file} ({len(lista_ticker)} titoli)...")
  risultati_finali = []
  top_n = 15

  try:
    df_totale = scarica_in_micro_blocchi(lista_ticker, dim_blocco=40)
    if df_totale.empty:
      return

    for ticker in lista_ticker:
      try:
        if len(lista_ticker) == 1:
          df = df_totale
        else:
          if ticker in df_totale.columns.levels[0]:
            df = df_totale[ticker]
          else:
            continue

        if df.empty or "Close" not in df.columns or len(df) < 50:
          continue

        close = df["Close"].dropna()
        if len(close) < 50:
          continue

        ultimo_prezzo = float(close.iloc[-1])
        prezzo_passato = float(close.iloc[-20])
        rendimento_pct = (
            (ultimo_prezzo - prezzo_passato) / prezzo_passato
        ) * 100

        sma_20 = float(close.rolling(window=20).mean().iloc[-1])
        sma_50 = float(close.rolling(window=50).mean().iloc[-1])

        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = float((100 - (100 / (1 + rs))).iloc[-1])

        if rsi >= 75:
          continue

        segnale = "Neutro"
        motivo = "Trend laterale o fase di transizione."
        if sma_20 > sma_50 and rsi < 70:
          segnale = "Rialzista (Buy/Accumulo)"
          motivo = "Medie mobili a favore e RSI equilibrato."
        elif sma_20 < sma_50 and rsi > 30:
          segnale = "Ribassista (Prudenza)"
          motivo = "Trend di medio periodo debole."
        elif rsi <= 30:
          segnale = "Ipervenduto (Possibile Rimbalzo)"
          motivo = "Prezzo tirato molto al ribasso, potenziale occasione."
        elif rsi >= 70:
          segnale = "Ipercomprato (Attenzione)"
          motivo = "Il titolo ha corso molto, rischio storno."

        # Storico ultimi 30 giorni per il grafico
        storico_30 = [round(float(p), 2) for p in close.tail(30).tolist()]

        risultati_finali.append({
            "ticker": ticker,
            "prezzo": round(ultimo_prezzo, 2),
            "rendimento_1m": rendimento_pct,
            "sma_20": round(sma_20, 2),
            "sma_50": round(sma_50, 2),
            "rsi": round(rsi, 2),
            "segnale": segnale,
            "motivazione": motivo,
            "storico": storico_30,
        })
      except Exception:
        continue

    risultati_finali.sort(key=lambda x: x["rendimento_1m"], reverse=True)
    risultati_finali = risultati_finali[:top_n]

    for r in risultati_finali:
      r.pop("rendimento_1m", None)

    payload = {
        "ultimo_aggiornamento": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "dati": risultati_finali,
    }

    with open(nome_file, "w", encoding="utf-8") as f:
      json.dump(payload, f, ensure_ascii=False, indent=4)
    print(
        f"✔ File {nome_file} generato con successo ({len(risultati_finali)}"
        " titoli)."
    )
  except Exception as e:
    print(f"Errore su {nome_file}: {e}")


if __name__ == "__main__":
  analizza_e_salva_mercato("dati_ftsemib.json", TICKERS_FTSEMIB)
  analizza_e_salva_mercato("dati_sp500.json", TICKERS_SP500)
  analizza_e_salva_mercato("dati_nasdaq.json", TICKERS_NASDAQ)
