from datetime import datetime
import json
import pandas as pd
import yfinance as yf


def scarica_ticker_ftse_mib():
  """Scarica l'elenco COMPLETO di tutte le aziende del FTSE MIB da Wikipedia"""
  try:
    url = "https://it.wikipedia.org/wiki/FTSE_MIB"
    tabelle = pd.read_html(url)
    df = tabelle[0]  # La tabella principale con i componenti
    
    colonna = [c for c in df.columns if "Ticker" in c or "Simbolo" in c or "Quotazione" in c]
    if colonna:
      simboli = df[colonna[0]].dropna().tolist()
    else:
      simboli = df.iloc[:, 0].dropna().tolist()

    # Pulisce i codici aggiungendo l'estensione .MI per Yahoo Finance
    return [s if ".MI" in str(s) else f"{str(s).strip()}.MI" for s in simboli]
  except Exception as e:
    print(f"Errore nel recupero automatico del FTSE MIB: {e}")
    return []


def scarica_ticker_sp500():
  """Scarica l'elenco COMPLETO di tutte le aziende dell'S&P 500 da Wikipedia"""
  try:
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    tabelle = pd.read_html(url)
    df = tabelle[0]
    simboli = df["Symbol"].dropna().tolist()
    return [str(s).replace(".", "-").strip() for s in simboli]
  except Exception as e:
    print(f"Errore nel recupero automatico dell'S&P 500: {e}")
    return []


def scarica_ticker_nasdaq():
  """Scarica l'elenco dei principali titoli del Nasdaq-100 da Wikipedia"""
  try:
    url = "https://en.wikipedia.org/wiki/NASDAQ-100"
    tabelle = pd.read_html(url)
    df = None
    for tab in tabelle:
      if "Ticker" in tab.columns or "Symbol" in tab.columns:
        df = tab
        break
    if df is None:
      df = tabelle[3]  # fallback comune per la tabella del Nasdaq 100

    colonna = [c for c in df.columns if "Ticker" in c or "Symbol" in c]
    simboli = df[colonna[0]].dropna().tolist() if colonna else df.iloc[:, 1].dropna().tolist()
    
    return [str(s).replace(".", "-").strip() for s in simboli]
  except Exception as e:
    print(f"Errore nel recupero automatico del Nasdaq-100: {e}")
    return []


def analizza_e_salva_mercato(nome_file, lista_ticker):
  if not lista_ticker:
    print(f"Nessun ticker trovato per {nome_file}")
    return

  print(f"\nInizio scansione di TUTTI i {len(lista_ticker)} titoli per {nome_file}...")
  top_n = 3
  risultati_screening = []

  # FASE 1: Esamina TUTTI i titoli del paniere uno per uno
  for ticker in lista_ticker:
    try:
      df = yf.download(ticker, period="3mo", interval="1d", progress=False)
      if df.empty or len(df) < 20:
        continue

      close = df["Close"].iloc[:, 0] if isinstance(df.columns, pd.MultiIndex) else df["Close"]

      prezzo_attuale = float(close.iloc[-1])
      prezzo_passato = float(close.iloc[-20])  # Circa 1 mese fa
      rendimento_pct = ((prezzo_attuale - prezzo_passato) / prezzo_passato) * 100

      # Calcolo RSI (14 periodi)
      delta = close.diff()
      gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
      loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
      rs = gain / loss
      rsi = float((100 - (100 / (1 + rs))).iloc[-1])

      risultati_screening.append({
          "Ticker": ticker, 
          "Rend_1M": rendimento_pct, 
          "RSI_raw": rsi
      })
    except Exception:
      continue

  if not risultati_screening:
    print(f"Nessun dato valido estratto per {nome_file}.")
    return

  # FASE 2: Ordina tutti i risultati e prende i migliori (escludendo gli ipercomprati estremi)
  df_screen = pd.DataFrame(risultati_screening)
  df_screen = df_screen.sort_values(by="Rend_1M", ascending=False)
  df_filtrati = df_screen[df_screen["RSI_raw"] < 75].head(top_n)
  migliori_ticker = df_filtrati["Ticker"].tolist()

  print(f"-> I {top_n} titoli migliori trovati per {nome_file}: {migliori_ticker}")

  # FASE 3: Analisi tecnica approfondita solo sui vincitori trovati
  risultati_finali = []
  for ticker in migliori_ticker:
    try:
      df = yf.download(ticker, period="6mo", interval="1d", progress=False)
      close = df["Close"].iloc[:, 0] if isinstance(df.columns, pd.MultiIndex) else df["Close"]

      ultimo_prezzo = float(close.iloc[-1])
      sma_20 = float(close.rolling(window=20).mean().iloc[-1])
      sma_50 = float(close.rolling(window=50).mean().iloc[-1])

      delta = close.diff()
      gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
      loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
      rsi = float((100 - (100 / (1 + (gain / loss)))).iloc[-1])

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
          "sma_20": round(sma_20, 2),
          "sma_50": round(sma_50, 2),
          "rsi": round(rsi, 2),
          "segnale": segnale,
          "motivazione": motivo,
      })
    except Exception as e:
      print(f"Errore nell'analisi tecnica di {ticker}: {e}")

  # Salvataggio nel file JSON corrispondente
  payload = {
      "ultimo_aggiornamento": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
      "dati": risultati_finali,
  }

  with open(nome_file, "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=4)
  print(f"File {nome_file} generato con successo.")


if __name__ == "__main__":
  # 1. FTSE MIB (Italia)
  tickers_italiani = scarica_ticker_ftse_mib()
  analizza_e_salva_mercato("dati_ftsemib.json", tickers_italiani)

  # 2. S&P 500 (USA)
  tickers_usa = scarica_ticker_sp500()
  analizza_e_salva_mercato("dati_sp500.json", tickers_usa)

  # 3. Nasdaq-100 (Tech USA)
  tickers_nasdaq = scarica_ticker_nasdaq()
  analizza_e_salva_mercato("dati_nasdaq.json", tickers_nasdaq)

