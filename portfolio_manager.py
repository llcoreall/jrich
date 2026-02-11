import json
import os
from typing import Dict, List, Any

PORTFOLIO_FILE = "portfolio_data.json"

DEFAULT_DATA = {
    "assets": [],
    "cash": {"USD": 0.0, "CAD": 0.0, "KRW": 0.0},
    "settings": {
        "base_currency": "USD",
        "theme": "Dark",
        "dividend_method": "TTM_Avg",
        "section_labels": {
            "strategic_allocation": "Strategic Allocation",
            "asset_growth": "Asset Growth Trajectory",
            "asset_manifest": "Asset Manifest",
            "risk_analysis": "Risk Analysis",
            "global_intel": "Global Intel"
        },
        "risk_inputs": {
            "roi": 0.0,
            "volatility": 0.0,
            "risk_free_rate": 0.045
        }
    }
}

class PortfolioManager:
    """
    Manages loading and saving of portfolio data to a local JSON file.
    Ensures data persistence across sessions.
    """
    def __init__(self, user_id=None):
        import shutil
        
        self.filepath = PORTFOLIO_FILE # Default fallback
        
        if user_id:
            target_file = f"data_{user_id}.json"
            self.filepath = target_file
            
            # Migration Logic for 'csj'
            # If user is 'csj' and their specific file doesn't exist yet, 
            # but the old default file exists, copy it over to preserve data.
            if user_id == "csj" and not os.path.exists(target_file) and os.path.exists(PORTFOLIO_FILE):
                try:
                    shutil.copy(PORTFOLIO_FILE, target_file)
                    print(f"MIGRATION: Copied {PORTFOLIO_FILE} to {target_file}")
                except Exception as e:
                    print(f"MIGRATION ERROR: {e}")

        self.data = self._load_data()

    def _load_data(self) -> Dict[str, Any]:
        """Loads data from JSON file or creates default if not exists/corrupt."""
        if not os.path.exists(self.filepath):
            return self._create_default_file()
        
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # In a real app we might want to backup the corrupted file
            return self._create_default_file()

    def _create_default_file(self) -> Dict[str, Any]:
        """Creates a new data file with default structure."""
        self.save_data(DEFAULT_DATA)
        return DEFAULT_DATA

    def save_data(self, data: Dict[str, Any] = None):
        """Saves current data state to JSON file."""
        if data:
            self.data = data
        
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4)

    def get_assets(self) -> List[Dict[str, Any]]:
        return self.data.get("assets", [])

    def add_or_update_asset(self, asset: Dict[str, Any]):
        """Adds a new asset or updates existing one based on ticker (Merges Quantity)."""
        asset['ticker'] = asset['ticker'].upper()
        
        # Find index of existing asset
        existing_idx = next((i for i, a in enumerate(self.data["assets"]) if a["ticker"] == asset["ticker"]), None)
        
        if existing_idx is not None:
            # Merge Logic:
            # 1. Update Quantity
            current_asset = self.data["assets"][existing_idx]
            old_qty = current_asset.get('quantity', 0.0)
            new_added_qty = asset.get('quantity', 0.0)
            total_qty = old_qty + new_added_qty
            
            # 2. Update Avg Price (Weighted Average)
            # Only if both have valid prices. If crypto (avg_price=0), keep it 0 or update if provided?
            # User requirement: "Crypto has avg cost disabled/hidden". So likely 0.
            # But for stocks, we need weighted avg.
            old_avg = current_asset.get('avg_price', 0.0)
            new_input_price = asset.get('avg_price', 0.0)
            
            if total_qty > 0:
                if old_avg > 0 and new_input_price > 0:
                    weighted_avg = ((old_qty * old_avg) + (new_added_qty * new_input_price)) / total_qty
                elif new_input_price > 0: # Old was 0
                    weighted_avg = new_input_price # aggregate? No, if old was 0 maybe it was missing.
                    # Actually if old was 0 (e.g. gifted), it drags down avg. 
                    # But if it was Crypto (0), we keep it 0.
                    if current_asset.get('asset_class') == 'Crypto':
                        weighted_avg = 0.0
                    else:
                        weighted_avg = ((old_qty * old_avg) + (new_added_qty * new_input_price)) / total_qty
                else: 
                    # New is 0 (e.g. crypto add) -> keep old avg? or 0? 
                    # If crypto, stay 0.
                    weighted_avg = old_avg if current_asset.get('asset_class') != 'Crypto' else 0.0
            else:
                weighted_avg = 0.0
            
            # Update fields
            current_asset['quantity'] = total_qty
            current_asset['avg_price'] = weighted_avg
            
            # Update other metadata if provided and different (Sector/Class might change if corrected)
            if asset.get('sector'):
                current_asset['sector'] = asset['sector']
            if asset.get('asset_class'):
                current_asset['asset_class'] = asset['asset_class']
                
            self.data["assets"][existing_idx] = current_asset
        else:
            self.data["assets"].append(asset)
        
        self.save_data()

    def remove_asset(self, ticker: str):
        """Removes an asset by ticker."""
        original_count = len(self.data["assets"])
        self.data["assets"] = [a for a in self.data["assets"] if a["ticker"] != ticker.upper()]
        
        if len(self.data["assets"]) < original_count:
            self.save_data()

    def update_cash(self, currency: str, amount: float):
        """Updates cash balance for a specific currency."""
        if "cash" not in self.data:
            self.data["cash"] = DEFAULT_DATA["cash"]
        self.data["cash"][currency.upper()] = amount
        self.save_data()

    def update_setting(self, key: str, value: Any):
        """Updates a specific setting."""
        if "settings" not in self.data:
            self.data["settings"] = DEFAULT_DATA["settings"]
        self.data["settings"][key] = value
        self.save_data()

    def get_setting(self, key: str, default: Any = None) -> Any:
        return self.data.get("settings", {}).get(key, default)
