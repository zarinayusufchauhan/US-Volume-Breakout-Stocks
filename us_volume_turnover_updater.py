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

# दोनों शीट्स को कनेक्ट करना
try:
    ws_volume = client.open_by_key(spreadsheet_id).worksheet("US volume breakout stocks")
    ws_turnover = client.open_by_key(spreadsheet_id).worksheet("US volume breakout stocks")
except Exception as e:
    print(f"Sheet Connection Error: {e}")
    exit(1)

# 2. Top 250 US Stocks की list
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

# 3. Yahoo Finance से US Stocks का data लाना
def fetch_us_stocks_data():
    print(f"\n--- US Stocks का Data ला रहे हैं ({len(TOP_US_STOCKS)} stocks) ---")
    
    all_data_volume = []
    all_data_turnover = []
    failed_stocks = []
    
    for idx, symbol in enumerate(TOP_US_STOCKS, 1):
        try:
            print(f"Fetching {idx}/250: {symbol}...", end=" ")
            
            # Yahoo Finance से data लेना (1 साल का historical data)
            data = yf.download(symbol, period="1y", progress=False)
            
            if len(data) < 200:
                print(f"⚠️ Not enough historical data")
                failed_stocks.append(symbol)
                continue
            
            # Latest values
            latest_close = data['Close'].iloc[-1]
            latest_volume = int(data['Volume'].iloc[-1])
            
            # Turnover = Volume * Close Price
            latest_turnover = latest_volume * latest_close
            
            # Volume के आधार पर data
            all_data_volume.append([
                symbol,
                latest_volume,
                round(latest_close, 2)
            ])
            
            # Turnover के आधार पर data
            all_data_turnover.append([
                symbol,
                round(latest_turnover, 2),
                round(latest_close, 2)
            ])
            
            print(f"✅")
            
            # Rate limiting (Yahoo Finance के लिए)
            time.sleep(0.1)
            
        except Exception as e:
            print(f"❌ Error: {str(e)[:30]}")
            failed_stocks.append(symbol)
            continue
    
    print(f"\n✅ {len(all_data_volume)} stocks का data successfully fetch हुआ!")
    if failed_stocks:
        print(f"⚠️ {len(failed_stocks)} stocks failed: {', '.join(failed_stocks[:10])}")
    
    return all_data_volume, all_data_turnover

# 4. Volume के आधार पर टॉप 250 (Volume Descending)
def get_top_by_volume(data):
    df = pd.DataFrame(data, columns=['Symbol', 'Volume', 'Close'])
    df = df.sort_values(by='Volume', ascending=False).head(250)
    return df[['Symbol', 'Volume', 'Close']].values.tolist()

# 5. Turnover के आधार पर टॉप 250 (Turnover Descending)
def get_top_by_turnover(data):
    df = pd.DataFrame(data, columns=['Symbol', 'Turnover', 'Close'])
    df = df.sort_values(by='Turnover', ascending=False).head(250)
    return df[['Symbol', 'Turnover', 'Close']].values.tolist()

# 6. Google Sheet को update करना
def update_google_sheet(data_volume, data_turnover, fetched_date_str):
    try:
        print(f"\n--- Google Sheet को update कर रहे हैं ---")
        
        # वॉल्यूम डेटा update करना (पहली 125 rows)
        ws_volume.batch_clear(['A2:C126'])
        ws_volume.update('A2', data_volume[:125])
        print("✅ Top 125 Volume stocks का data add हुआ")
        
        # Turnover डेटा update करना (126 से 250 rows)
        ws_volume.batch_clear(['A127:C251'])
        ws_volume.update('A127', data_turnover[:125])
        print("✅ Top 125 Turnover stocks का data add हुआ")
        
        # Timestamp update करना
        ist_now = (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime('%d-%b %H:%M')
        status_msg = f"Data Date: {fetched_date_str} | Last Update: {ist_now} (IST) | Total: 250 Stocks"
        
        ws_volume.update('A1', [[status_msg]])
        print(f"✅ Timestamp updated: {status_msg}")
        
        return True
        
    except Exception as e:
        print(f"❌ Google Sheet अपडेट करने में Error: {e}")
        return False

# 7. Main Execution
if __name__ == "__main__":
    print("🚀 US Stock Market Volume & Turnover Updater शुरू हो रहा है...")
    
    # Data लाना
    data_volume, data_turnover = fetch_us_stocks_data()
    
    if data_volume and data_turnover:
        # Volume के आधार पर sort करना
        top_volume = get_top_by_volume(data_volume)
        
        # Turnover के आधार पर sort करना
        top_turnover = get_top_by_turnover(data_turnover)
        
        fetched_date_str = datetime.now().strftime('%d-%b-%Y')
        
        # Google Sheet update करना
        if update_google_sheet(top_volume, top_turnover, fetched_date_str):
            print("\n✅ SUCCESS: सब कुछ perfectly update हो गया!")
        else:
            print("\n❌ FAILED: Google Sheet update नहीं हुई")
            exit(1)
    else:
        print("\n❌ FAILED: Data fetch नहीं हुआ")
        exit(1)
