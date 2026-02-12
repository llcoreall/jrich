import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection
from typing import Dict, List, Any
import json

# Default fallback if sheet is empty
DEFAULT_ASSETS_DF = pd.DataFrame(columns=["Ticker", "Quantity", "AvgCost", "Class", "Sector"])
DEFAULT_CONFIG_DF = pd.DataFrame([
    {"Key": "CASH_USD", "Value": "0.0"},
    {"Key": "CASH_CAD", "Value": "0.0"},
    {"Key": "CASH_KRW", "Value": "0.0"},
    {"Key": "BASE_CURRENCY", "Value": "USD"}
], columns=["Key", "Value"])

class PortfolioManager:
    """
    Manages loading and saving of portfolio data to Google Sheets via st.connection.
    """
    def __init__(self, user_id=None):
        # user_id handling:
        # For GSheets, we might use different worksheets for different users 
        # OR different spreadsheets. 
        # User requested: "My Google Sheet". 
        # We will assume a single user for now or use user_id as worksheet suffix if needed.
        # Given "data_{user_id}.json" pattern, let's use:
        # Worksheet 'Assets_{user_id}' and 'Config_{user_id}'
        
        self.user_suffix = f"_{user_id}" if user_id else "_csj"
        self.assets_sheet = f"Assets{self.user_suffix}"
        self.config_sheet = f"Config{self.user_suffix}"
        
        # Initialize Connection
        try:
            self.conn = st.connection("gsheets", type=GSheetsConnection)
        except Exception as e:
            st.error(f"GSheets Connection Failed: {e}. Check secrets.toml.")
            self.data = {"assets": [], "cash": {}, "settings": {}}
            return

        self.data = self._load_data()

    def _load_data(self) -> Dict[str, Any]:
        """Loads data from GSheets."""
        data_struct = {
            "assets": [],
            "cash": {"USD": 0.0, "CAD": 0.0, "KRW": 0.0},
            "settings": {} # Add specific settings defaults if needed
        }
        
        # 1. LOAD ASSETS
        try:
            df_assets = self.conn.read(worksheet=self.assets_sheet, ttl=0) # ttl=0 for fresh data
            # Clean and Convert to Dict
            if not df_assets.empty:
                for _, row in df_assets.iterrows():
                    data_struct["assets"].append({
                        "ticker": str(row.get("Ticker", "")),
                        "quantity": float(row.get("Quantity", 0.0)),
                        "avg_price": float(row.get("AvgCost", 0.0)),
                        "asset_class": str(row.get("Class", "Stock")),
                        "sector": str(row.get("Sector", "Unknown"))
                    })
        except Exception:
            # Sheet might not exist, return default
            pass

        # 2. LOAD CONFIG (Cash & Settings)
        try:
            df_config = self.conn.read(worksheet=self.config_sheet, ttl=0)
            if not df_config.empty:
                for _, row in df_config.iterrows():
                    key = str(row.get("Key", ""))
                    val = str(row.get("Value", ""))
                    
                    if key.startswith("CASH_"):
                        currency = key.split("_")[1]
                        try:
                            data_struct["cash"][currency] = float(val)
                        except: pass
                    elif key == "BASE_CURRENCY":
                         data_struct["settings"]["base_currency"] = val
                    elif key.startswith("LABEL_"):
                        # Reconstruct section labels?
                        # Simplified: sticking to core data for now.
                        pass
        except Exception:
            pass
            
        return data_struct

    def save_data(self, data: Dict[str, Any] = None):
        """Saves current data state to GSheets."""
        if data:
            self.data = data
            
        # 1. PREPARE ASSETS DATAFRAME
        assets_list = []
        for a in self.data.get("assets", []):
            assets_list.append({
                "Ticker": a.get("ticker"),
                "Quantity": a.get("quantity"),
                "AvgCost": a.get("avg_price"),
                "Class": a.get("asset_class"),
                "Sector": a.get("sector")
            })
        
        df_assets = pd.DataFrame(assets_list)
        if df_assets.empty:
            df_assets = DEFAULT_ASSETS_DF

        # 2. PREPARE CONFIG DATAFRAME
        config_list = []
        # Cash
        for curr, amount in self.data.get("cash", {}).items():
            config_list.append({"Key": f"CASH_{curr}", "Value": str(amount)})
        
        # Settings
        base_curr = self.data.get("settings", {}).get("base_currency", "USD")
        config_list.append({"Key": "BASE_CURRENCY", "Value": base_curr})
        
        df_config = pd.DataFrame(config_list)

        # 3. WRITE TO SHEETS
        try:
            self.conn.update(worksheet=self.assets_sheet, data=df_assets)
            self.conn.update(worksheet=self.config_sheet, data=df_config)
            # st.toast("☁️ Cloud Sync Complete") # Optional feedback
        except Exception as e:
            st.error(f"Failed to sync to GSheets: {e}")

    # --- Methods below remain largely same, interacting with self.data ---

    def get_assets(self) -> List[Dict[str, Any]]:
        return self.data.get("assets", [])

    def add_or_update_asset(self, asset: Dict[str, Any]):
        # Same Logic as before (in-memory update)
        # Then call save_data which pushes to sheet
        asset['ticker'] = asset['ticker'].upper()
        existing_idx = next((i for i, a in enumerate(self.data["assets"]) if a["ticker"] == asset["ticker"]), None)
        
        if existing_idx is not None:
             # Merge Logic (Simplified Reuse)
            current_asset = self.data["assets"][existing_idx]
            old_qty = current_asset.get('quantity', 0.0)
            new_added_qty = asset.get('quantity', 0.0)
            total_qty = old_qty + new_added_qty
            
            old_avg = current_asset.get('avg_price', 0.0)
            new_input_price = asset.get('avg_price', 0.0)
            
            if total_qty > 0:
                if old_avg > 0 and new_input_price > 0:
                    weighted_avg = ((old_qty * old_avg) + (new_added_qty * new_input_price)) / total_qty
                elif new_input_price > 0:
                     if current_asset.get('asset_class') == 'Crypto':
                        weighted_avg = 0.0
                     else:
                        weighted_avg = ((old_qty * old_avg) + (new_added_qty * new_input_price)) / total_qty
                else: 
                    weighted_avg = old_avg if current_asset.get('asset_class') != 'Crypto' else 0.0
            else:
                weighted_avg = 0.0
            
            current_asset['quantity'] = total_qty
            current_asset['avg_price'] = weighted_avg
            if asset.get('sector'): current_asset['sector'] = asset['sector']
            if asset.get('asset_class'): current_asset['asset_class'] = asset['asset_class']
            self.data["assets"][existing_idx] = current_asset
        else:
            self.data["assets"].append(asset)
        
        self.save_data()

    def remove_asset(self, ticker: str):
        original_count = len(self.data["assets"])
        self.data["assets"] = [a for a in self.data["assets"] if a["ticker"] != ticker.upper()]
        if len(self.data["assets"]) < original_count:
            self.save_data()

    def update_cash(self, currency: str, amount: float):
        if "cash" not in self.data: self.data["cash"] = {}
        self.data["cash"][currency.upper()] = amount
        self.save_data()

    def update_setting(self, key: str, value: Any):
        if "settings" not in self.data: self.data["settings"] = {}
        self.data["settings"][key] = value
        self.save_data()

    def get_setting(self, key: str, default: Any = None) -> Any:
        return self.data.get("settings", {}).get(key, default)
