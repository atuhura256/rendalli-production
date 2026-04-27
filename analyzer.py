import pandas as pd

def load_data(file_path):
    # Load the data and ensure dates are in the correct format
    df = pd.read_csv(file_path)
    df['DATE'] = pd.to_datetime(df['DATE'])
    return df

def get_cage_analysis(df, cage_name, stock_date, harvest_date):
    """
    Analyzes feed consumption for a specific cage within a date range.
    """
    # Filter by Cage
    cage_df = df[df['CAGE/TANK'] == cage_name].copy()
    
    # Filter by Date Range (Stocking to Harvesting)
    mask = (cage_df['DATE'] >= pd.to_datetime(stock_date)) & \
           (cage_df['DATE'] <= pd.to_datetime(harvest_date))
    filtered_df = cage_df.loc[mask]
    
    if filtered_df.empty:
        return None

    # Analysis Calculations
    total_feed = filtered_df['AMOUNT'].sum()
    days_fed = (pd.to_datetime(harvest_date) - pd.to_datetime(stock_date)).days
    avg_daily_feed = total_feed / days_fed if days_fed > 0 else 0
    
    # Feed Type Breakdown
    feed_breakdown = filtered_df.groupby('FEED TYPE')['AMOUNT'].sum().to_dict()
    
    return {
        "total_feed": total_feed,
        "avg_daily": avg_daily_feed,
        "feed_breakdown": feed_breakdown,
        "data_points": filtered_df
    }