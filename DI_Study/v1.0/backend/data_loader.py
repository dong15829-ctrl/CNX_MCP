import pandas as pd
from sqlalchemy.orm import Session
from database import SessionLocal
from models import SalesFact, Hitlist, InsightSummary

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_available_months(country_code="US"):
    """
    Returns list of available months for a country.
    """
    db = SessionLocal()
    try:
        # distinct dates from SalesFact
        dates = db.query(SalesFact.year_month).filter(SalesFact.country_code == country_code).distinct().all()
        # sort descending
        return sorted([d[0] for d in dates], reverse=True)
    finally:
        db.close()

def load_insight_data(country_code="US", year_month=None):
    """
    Loads data from SQLite and structures it for the API.
    """
    db = SessionLocal()
    try:
        # 1. Fetch Sales Facts
        query = db.query(SalesFact).filter(SalesFact.country_code == country_code)
        
        # Filter Logic:
        # If year_month is provided, we want trends UP TO that month.
        # But for Hitlists, maybe just that month?
        # Let's apply valid date filtering if needed. 
        # For simplicity in this version, we will load ALL history for constraints, 
        # but in a real app query should be optimized.
        
        facts = query.all()

        if not facts:
            return {}

        # 2. Extract Dates (Sorted)
        # Filter dates <= selected year_month
        all_dates = sorted(list(set(f.year_month for f in facts)))
        
        if year_month:
            # Filter dates up to selected month (inclusive)
            dates = [d for d in all_dates if d <= year_month]
        else:
            dates = all_dates
            
        if not dates: 
             return {}
             
        # Filter facts to only these dates
        facts = [f for f in facts if f.year_month in dates]
        
        # Helper to build series
        def build_series(section, category, metric, brand=None):
            series = []
            for d in dates:
                # Find value for this date
                # Inefficient O(N) lookup but dataset is small. 
                # Optimization: Convert facts to Dict {(section, cat, metric, brand, date): value}
                val = 0.0
                matches = [f for f in facts if f.year_month == d and f.section == section and f.category == category and f.metric == metric]
                if brand:
                    matches = [m for m in matches if m.brand == brand]
                
                if matches:
                    val = matches[0].value
                series.append(val)
            return series

        # Optimization: Pre-index facts
        fact_map = {} # Key: (section, category, metric, brand, year_month) -> value
        for f in facts:
            k = (f.section, f.category, f.metric, f.brand, f.year_month)
            fact_map[k] = f.value
            
        def get_series_fast(section, category, metric, brand=None):
            return [fact_map.get((section, category, metric, brand, d), 0.0) for d in dates]

        # Structure Data
        response = {"dates": dates}
        
        sections = ['market', 'product', 'size', 'price']
        for sec in sections:
            # Total
            total_sales = get_series_fast(sec, 'total', 'sales')
            total_traffic = get_series_fast(sec, 'total', 'traffic')
            
            # Breakdown Sales (Brands)
            # Find all brands for this section/breakdown/sales
            brands_sales = sorted(list(set(f.brand for f in facts if f.section == sec and f.category == 'breakdown' and f.metric == 'sales' and f.brand)))
            breakdown_sales = {b: get_series_fast(sec, 'breakdown', 'sales', b) for b in brands_sales}
            
            # Breakdown Share
            brands_share = sorted(list(set(f.brand for f in facts if f.section == sec and f.category == 'breakdown' and f.metric == 'share_pct' and f.brand)))
            breakdown_share = {b: get_series_fast(sec, 'breakdown', 'share_pct', b) for b in brands_share}
            
            # Hitlists
            # Fetch for this country
            hl_query = db.query(Hitlist).filter(Hitlist.country_code == country_code, Hitlist.section == sec)
            
            # If specific month is requested, do we show ONLY that month's hitlist?
            # Or history of hitlists? Dashboard usually shows Tables for current month.
            # Let's filter Hitlist to match exactly 'year_month' if provided, 
            # OR if not provided, show latest.
            
            hl_objs = hl_query.all()
            
            # Group by Month
            hl_grouped = {}
            for h in hl_objs:
                # Filter Logic for Hitlists:
                # If year_month selected, ONLY show that month.
                # If NOT selected, show all (or latest? logic below sorts it)
                if year_month and h.year_month != year_month:
                    continue
                    
                if h.year_month not in hl_grouped:
                    hl_grouped[h.year_month] = []
                # Reconstruct row list: [Rank, Model, '', ASIN, '', Brand, Inch, Type, Sales, %, MoM, QTY, ASP, Traf, CVR]
                # Note: The indices must match frontend.
                # Frontend expects: 0:Rank, 1:Model, 2:ASIN, 3:Brand... wait check script.js
                # Script.js: 
                # idx 0: Rank, 1: Model, 2: ASIN (Actually script says idx 2 is ASIN? Wait.)
                # Script.js: headers=['Rank','Model','ASIN','Brand'...]
                # row.slice(0, headers.length).forEach...
                # row is: [Rank, Model, ASIN, Brand, Inch, Type, Sales, %, MoM, QTY, ASP, Traf, CVR]
                
                row = [
                    h.rank, h.model, h.asin, h.brand, h.inch, h.type_,
                    h.sales, h.share_pct, h.mom_pct, h.qty, h.asp, h.traffic, h.cvr_pct
                ]
                hl_grouped[h.year_month].append(row)
            
            # Format hitlists list
            hitlists_list = []
            for mon, rows in hl_grouped.items():
                # Sort rows by rank
                rows.sort(key=lambda x: x[0]) 
                hitlists_list.append({"month": mon, "rows": rows})
                
            # Sort hitlists by month name (Sep, Oct)
            # Simple heuristic sort
            hitlists_list.sort(key=lambda x: x['month'])

            response[sec] = {
                "total": {"sales": total_sales, "traffic": total_traffic},
                "breakdown_sales": breakdown_sales,
                "breakdown_share": breakdown_share,
                "hitlists": hitlists_list
            }

        return response

    except Exception as e:
        print(f"DB Load Error: {e}")
        return {}
    finally:
        db.close()

