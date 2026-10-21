from datetime import datetime
import io
import json
import pandas as pd
import requests
import yfinance as yf


def scarica_ticker_ftsemib():
  """Scarica l'intero FTSE MIB da Wikipedia filtrando i ticker validi"""
  try:
    url = "https://it.wikipedia.org/wiki/FTSE_MIB"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
      tabelle = pd.read_html(io.StringIO(response.text))
      df = None
      for tab in tabelle:
        cols_str = " ".join([str(c) for c in tab.columns]).lower()
        if (
            "società" in cols_str
            or "ticker" in cols_str
            or "simbolo" in cols_str
            or "quotazione" in cols_str
        ):
          df = tab
          break
      if df is None:
        df = tabelle[0]

      colonna = [
          c
          for c in df.columns
          if "Ticker" in str(c)
          or "Simbolo" in str(c)
          or "Quotazione" in str(c)
      ]
      simboli = (
          df[colonna[0]].dropna().tolist()
          if colonna
          else df.iloc[:, 0].dropna().tolist()
      )

      tickers = []
      for s in simboli:
        s_str = str(s).strip().upper()
        if (
            not s_str
            or "S.P.A" in s_str
            or "SOCIETÀ" in s_str
            or len(s_str) > 10
            or "." in s_str.replace(".MI", "")
        ):
          continue
        if not s_str.endswith(".MI"):
          s_str = f"{s_str}.MI"
        tickers.append(s_str)

      if len(tickers) > 5:
        print(f"Scaricati {len(tickers)} titoli dinamici dal FTSE MIB.")
        return tickers
  except Exception as e:
    print(f"Errore scraping FTSE MIB: {e}")

  # Fallback di sicurezza nel caso Wikipedia non risponda
  return [
      "ENEL.MI",
      "ENI.MI",
      "UCG.MI",
      "ISP.MI",
      "STLA.MI",
      "RACE.MI",
      "G.MI",
      "MB.MI",
      "CPR.MI",
      "HER.MI",
  ]


def scarica_ticker_sp500():
  """Scarica l'intero S&P 500 da Wikipedia"""
  try:
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
      tabelle = pd.read_html(io.StringIO(response.text))
      df = tabelle[0]
      simboli = df["Symbol"].dropna().tolist()
      tickers = [str(s).replace(".", "-").strip() for s in simboli]
      if len(tickers) > 50:
        print(f"Scaricati {len(tickers)} titoli dinamici da S&P 500.")
        return tickers
  except Exception:
    pass

  return ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "JPM", "V"]


def scarica_ticker_nasdaq():
  """Scarica l'intero Nasdaq-100 da Wikipedia"""
  try:
    url = "https://en.wikipedia.org/wiki/NASDAQ-100"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
      tabelle = pd.read_html(io.StringIO(response.text))
      df = None
      for tab in tabelle:
        if "Ticker" in tab.columns or "Symbol" in tab.columns:
          df = tab
          break
      if df is None:
        df = tabelle[3]
      colonna = [c for c in df.columns if "Ticker" in c or "Symbol" in c]
      simboli = (
          df[colonna[0]].dropna().tolist()
          if colonna
          else df.iloc[:, 1].dropna().tolist()
      )
      tickers = [str(s).replace(".", "-").strip() for s in simboli]
      if len(tickers) > 20:
        print(f"Scaricati {len(tickers)} titoli dinamici dal Nasdaq-100.")
        return tickers
  except Exception:
    pass

  return ["AAPL", "MSFT", "NVDA", "AMZN", "META", "TSLA", "AVGO", "COST"]


def analizza_e_salva_mercato(nome_file, lista_ticker):
  print(
      f"\nAnalisi estesa in blocco per {nome_file} ({len(lista_ticker)}"
      " titoli totali)..."
  )
  risultati_finali = []
  top_n = 10

  try:
    # SCARICA TUTTI I TITOLI DELL'INDICE IN UN UNICO BLOCCO
    df_totale = yf.download(
        lista_ticker, period="6mo", interval="1d", progress=False, group_by="ticker"
    )
    if df_totale.empty:
      print(f"Nessun dato ricevuto per {nome_file}")
      return

    for ticker in lista_ticker:
      try:
        # Estrae i dati del singolo titolo dal pacchetto totale
        if len(lista_ticker) == 1:
          df = df_totale
        else:
          df = df_totale[ticker] if ticker in df_totale else pd.DataFrame()

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
          continue  # Esclude ipercomprato estremo

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

        risultati_finali.append({
            "ticker": ticker,
            "prezzo": round(ultimo_prezzo, 2),
            "rendimento_1m": rendimento_pct,
            "sma_20": round(sma_20, 2),
            "sma_50": round(sma_50, 2),
            "rsi": round(rsi, 2),
            "segnale": segnale,
            "motivazione": motivo,
        })
      except Exception:
        continue

    # Ordina per performance a 1 mese (decrescente) e prende i migliori top_n del totale
    risultati_finali.sort(key=lambda x: x["rendimento_1m"], reverse=True)
    risultati_finali = risultati_finali[:top_n]

    # Pulisce il campo d'appoggio temporaneo prima di scrivere il JSON
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
        " migliori trovati su tutto il paniere)."
    )

  except Exception as e:
    print(f"Errore generale nel blocco {nome_file}: {e}")


if __name__ == "__main__":
  print("=== AVVIAMENTO MOTORE DI ANALISI TOTALE (ESTESO) ===")

  try:
    analizza_e_salva_mercato("dati_ftsemib.json", scarica_ticker_ftsemib())
  except Exception as e:
    print(f"Errore critico FTSE MIB: {e}")

  try:
    analizza_e_salva_mercato("dati_sp500.json", scarica_ticker_sp500())
  except Exception as e:
    print(f"Errore critico S&P 500: {e}")

  try:
    analizza_e_salva_mercato("dati_nasdaq.json", scarica_ticker_nasdaq())
  except Exception as e:
    print(f"Errore critico Nasdaq: {e}")

  print("=== ELABORAZIONE COMPLETATA CON SUCCESSO ===")
