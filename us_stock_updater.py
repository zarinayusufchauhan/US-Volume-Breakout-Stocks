import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import os
import json
import time

# 1. Credentials Setup
creds_json = os.environ.get('GCP_CREDENTIALS')
if not creds_json:
    print("ERROR: GCP_CREDENTIALS secret missing!")
    exit(1)

creds_dict = json.loads(creds_json)
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# आपकी शीट की ID 
spreadsheet_id = "1Ub7LjwdrIcEHW48qv-cQCxbd6SN3uspqqaL3fH6_a5w"

# शीट को कनेक्ट करना
try:
    ws = client.open_by_key(spreadsheet_id).worksheet("US volume breakout stocks")
    print(f"✅ Sheet 'US volume breakout stocks' से connected!")
except Exception as e:
    print(f"Sheet Connection Error: {e}")
    exit(1)

# 2. Top 250 US Stocks की list
# S&P 500 और Nasdaq-100 के top stocks
TOP_US_STOCKS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TESLA", "META", "BERKB", "JPM", "JNJ",
    "V", "WMT", "PG", "MA", "DIS", "BA", "MCD", "GS", "AXP", "HD",
    "C", "IBM", "INTC", "CSCO", "VZ", "T", "XOM", "CVX", "KO", "PEP",
    "PM", "MO", "COST", "AMGN", "LLY", "ABBV", "PFE", "TMO", "UNH", "ISRG",
    "CRM", "ORCL", "ADBE", "NOW", "INTU", "ANET", "DDOG", "CRWD", "NET", "SNOW",
    "ASML", "TSM", "AMD", "QCOM", "AVGO", "NXPI", "MXIM", "KLAC", "LRCX", "ANSS",
    "CDNS", "SNPS", "SPLK", "OKTA", "SLACK", "TWLO", "ROOK", "PINS", "SQ", "PYPL",
    "SHOP", "DASH", "UBER", "LYFT", "ABNB", "EXPE", "BOOKING", "TRIP", "NFLX", "ROKU",
    "SPOT", "ZM", "TEAM", "DOCUSIGN", "WORKIVA", "ATLASSIAN", "STRIPE", "CHWY", "DKNG", "PENN",
    "GILD", "BIIB", "REGENERON", "ILMN", "VEEV", "WDAY", "PNPT", "COIN", "MSTR", "RIOT",
    "MARA", "CLSK", "GBTC", "SOS", "BITO", "IBIT", "FBTC", "SPY", "QQQ", "IWM",
    "EEM", "AGG", "BND", "TLT", "SHY", "TBT", "TQQQ", "SQQQ", "SSO", "PSQ",
    "UWM", "TWM", "LABU", "LABD", "TMF", "TMV", "UPRO", "DPST", "SPXL", "SPXS",
    "UDOW", "SDOW", "URTY", "DRTY", "YINN", "YANG", "SVXY", "UVXY", "VIXY", "TNA",
    "TZA", "JNUG", "JDST", "NUGT", "DUST", "AGQ", "ZSL", "UGAZ", "DGAZ", "UCL",
    "SCO", "ULE", "DLE", "USO", "DBO", "USL", "UCO", "BNO", "DBA", "DBE",
    "DBF", "DBC", "CORN", "SOYB", "WEAT", "UGA", "UNG", "UNL", "ULCL", "UPL",
    "DNL", "DCL", "DUG", "DRN", "UYM", "DBV", "PWV", "ULV", "DXD", "PSP",
    "PSJ", "PSA", "PSK", "RXL", "XLY", "XLP", "XLE", "XLF", "XLV", "XLI",
    "XLK", "XLU", "XLRE", "VUG", "VTV", "VOE", "VBR", "VBK", "VB", "VEA",
    "VWO", "VNQ", "VNE", "VNQI", "VXUS", "VTIAX", "VCIT", "VCSH", "VWOB", "BSV",
    "BIV", "BLV", "BLW", "VMBS", "VGIT", "VGSH", "VGSLX", "VGLTX", "VBTLX", "BRK.A",
    "LUV", "DAL", "AAL", "UAL", "ALK", "SAVE", "SKW", "FDX", "UPS", "XPO",
    "R", "SAIA", "LOGI", "AZO", "ORLY", "ATGE", "PAG", "TRC", "REZI", "PEN",
    "LAD", "TPH", "NRG", "OXY", "MPC", "PSX", "VLO", "DESP", "RIG", "EQNR",
    "SLB", "NOG", "CDEV", "DRRX", "PXD", "COG", "MRO", "EOG", "WMB", "OKE",
    "FTAI", "SRE", "ES", "EIX", "NEE", "SO", "DUK", "AEP", "PPL", "D",
    "EXC", "ETR", "SCHW", "LMND", "ASHR", "PTON", "ZG", "Z", "MELI", "VIOT",
    "SABR", "BALL", "WEC", "AEE", "CCEP", "KMI", "ET", "MMP", "BP", "MPLX",
    "TMDX", "BRKM", "NI", "PII", "PKI", "DRI", "LYB", "APD", "LIN", "DAR",
    "ALB", "CTVA", "FMC", "THO", "TWO", "IRM", "STAG", "STOR", "CCI", "EQIX",
    "DLR", "CONE", "PLD", "ARE", "VTR", "WELL", "LTC", "NHI", "OHI", "SASRX",
    "RIVE", "LMB", "VICI", "AGNC", "NRZ", "ORC", "ARCC", "MAIN", "GAIN", "PCI"
]

# शुरुआत में 250 stocks तक सीमित करो
TOP_US_STOCKS = TOP_US_STOCKS[:250]

# 3. Yahoo Finance से data लाना
def fetch_us_stocks_data():
    print(f"\n--- US Stocks का Data ला रहे हैं ({len(TOP_US_STOCKS)} stocks) ---")
    
    all_data = []
    failed_stocks = []
    
    for idx, symbol in enumerate(TOP_US_STOCKS, 1):
        try:
            print(f"Fetching {idx}/250: {symbol}...", end=" ")
            
            # Yahoo Finance से data लेना
            data = yf.download(symbol, period="250d", progress=False)
            
            if len(data) < 200:
                print(f"⚠️ Not enough historical data")
                failed_stocks.append(symbol)
                continue
            
            # Latest values
            latest_close = data['Close'].iloc[-1]
            latest_volume = data['Volume'].iloc[-1]
            
            # DMA calculations (अगर data काफी है)
            if len(data) >= 50:
                dma_50 = data['Close'].tail(50).mean()
            else:
                dma_50 = latest_close
                
            if len(data) >= 100:
                dma_100 = data['Close'].tail(100).mean()
            else:
                dma_100 = latest_close
                
            if len(data) >= 200:
                dma_200 = data['Close'].tail(200).mean()
            else:
                dma_200 = latest_close
            
            all_data.append([
                symbol,
                int(latest_volume),
                round(latest_close, 2),
                round(latest_close, 2),  # CMP
                round(dma_50, 2),
                round(dma_100, 2),
                round(dma_200, 2),
                "",  # Output (formula में calculate होगा)
                "",  # Difference from 200 DMA (formula में)
                ""   # CAR (formula में)
            ])
            
            print(f"✅")
            
            # Rate limiting (Yahoo Finance के लिए)
            time.sleep(0.1)
            
        except Exception as e:
            print(f"❌ Error: {str(e)[:30]}")
            failed_stocks.append(symbol)
            continue
    
    print(f"\n✅ {len(all_data)} stocks का data successfully fetch हुआ!")
    if failed_stocks:
        print(f"⚠️ {len(failed_stocks)} stocks failed: {', '.join(failed_stocks[:10])}")
    
    return all_data

# 4. Google Sheet को update करना
def update_google_sheet(data):
    try:
        print(f"\n--- Google Sheet को update कर रहे हैं ---")
        
        # पुराना data clear करना (A2:J251 तक)
        ws.batch_clear(['A2:J251'])
        print("✅ पुराना data clear किया")
        
        # नया data डालना
        ws.update('A2', data)
        print(f"✅ {len(data)} stocks का data Google Sheet में add हो गया!")
        
        # Timestamp update करना
        ist_now = (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime('%d-%b %H:%M')
        status_msg = f"Last Update: {ist_now} (IST) | Total Stocks: {len(data)}"
        
        ws.update('A1', [[status_msg]])
        print(f"✅ Timestamp updated: {status_msg}")
        
        return True
        
    except Exception as e:
        print(f"❌ Google Sheet अपडेट करने में Error: {e}")
        return False

# 5. Main Execution
if __name__ == "__main__":
    print("🚀 US Stock Market Auto Updater शुरू हो रहा है...")
    
    # Data लाना
    data = fetch_us_stocks_data()
    
    if data:
        # Google Sheet update करना
        if update_google_sheet(data):
            print("\n✅ SUCCESS: सब कुछ perfectly update हो गया!")
        else:
            print("\n❌ FAILED: Google Sheet update नहीं हुई")
            exit(1)
    else:
        print("\n❌ FAILED: Data fetch नहीं हुआ")
        exit(1)
