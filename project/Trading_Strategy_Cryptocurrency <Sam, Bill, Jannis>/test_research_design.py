
import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.linear_model import Ridge
from scipy.stats import spearmanr
from pathlib import Path
from dataclasses import dataclass
import json
import warnings

warnings.filterwarnings('ignore')

# Config
DATA_DIR = Path("/Users/sammm/Documents/HW_code/Fintech_ML/ml-crypto/data/curated")
METRICS_DIR = Path("/Users/sammm/Documents/HW_code/Fintech_ML/ml-crypto/data/metrics")
INPUT_FILE = DATA_DIR / "factors_weekly_enhanced.parquet"
OUTPUT_PRED = DATA_DIR / "ml_preds_weekly.parquet"
UNIVERSE_FILE = DATA_DIR / "universe_top30_annual.parquet"

@dataclass
class CFG:
    lookback_weeks: int = 52
    min_assets_per_week: int = 10
    asset_cap: int = 30
    early_stop_weeks: int = 8
    seed: int = 42
    
    # Enhanced LightGBM Params
    lgbm_params = dict(
        objective="lambdarank",
        metric="ndcg",
        ndcg_eval_at=[5, 10, 30],
        boosting_type="dart", # Try DART for better generalization
        n_estimators=3000,
        learning_rate=0.02, # Slower learning
        num_leaves=127,     # 2^7 - 1
        max_depth=-1,
        min_data_in_leaf=20,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.1,
        reg_lambda=1.0,
        random_state=42,
        verbose=-1,
        label_gain=[0, 1, 3, 7, 15]
    )
    
    ridge_alpha: float = 1.0
    w_ranker: float = 0.6 # Bias slightly towards Ranker
    w_ridge: float = 0.4

def to_relevance_levels(series, n_levels=5):
    try:
        return pd.qcut(series, n_levels, labels=False, duplicates='drop').fillna(n_levels // 2).astype(int)
    except:
        return pd.Series(0, index=series.index, dtype=int) # Fallback

def train_model():
    print(f"Loading data from {INPUT_FILE}...")
    df = pd.read_parquet(INPUT_FILE)
    df['date_week'] = pd.to_datetime(df['date_week'])
    
    uni = pd.read_parquet(UNIVERSE_FILE)
    uni['symbol'] = uni['symbol'].astype(str).str.upper()
    df['symbol'] = df['symbol'].astype(str).str.upper()
    df['year'] = df['date_week'].dt.year
    
    # Filter Universe
    df = df.merge(uni[['year', 'symbol']].drop_duplicates(), on=['year', 'symbol'], how='inner')
    
    # Define Target
    # y_fwd1 is already in factors_weekly (calculated in notebook usually, but check if factor_eda.ipynb calculated it or ml_train)
    # The view of ml_train.ipynb showed calculation of excess and y_fwd1. We need to recalculate here to be safe.
    
    df = df.sort_values(['symbol', 'date_week'])
    df['rf_weekly'] = df.get('rf_weekly', 0.0)
    df['excess'] = df['ret_simple_weekly'] - df['rf_weekly']
    df['y_fwd1'] = df.groupby('symbol')['excess'].shift(-1)
    
    # Volatility Scaling Target
    # Use Vol_4w if available, else calc
    if 'Vol_4w' not in df.columns:
        df['Vol_4w'] = df.groupby('symbol')['close'].pct_change().rolling(4).std()
    
    df['vol_clip'] = df['Vol_4w'].clip(lower=0.01) # Avoid div by zero
    df['target_scaled'] = df['y_fwd1'] / df['vol_clip']
    
    # Feature Selection (include new features)
    base_feats = [
        "log_mcap_year_z", "log_price_z", "max_price_week_z",
        "r1_z", "r2_z", "r3_z", "r4_z", "r4_1_z", "rmom3_z",
        "prcvol_mean_week_z", "prcvol_std_week_z", "vol_4w_z",
        # New
        "RSI_14_z", "ATR_14_norm_z", "BB_Width_20_z", "MACD_z", 
        "Close_div_MA20_z", "Close_div_MA50_z", "Vol_4w_z", "Vol_12w_z"
    ]
    fac_cols = [c for c in base_feats if c in df.columns]
    print(f"Features ({len(fac_cols)}): {fac_cols}")
    
    # Drop rows without target or features
    df_clean = df.dropna(subset=['y_fwd1'] + fac_cols).copy()
    
    # Rolling Walk-Forward Validation
    # Train on expanding window, validation on recent
    
    dates = sorted(df_clean['date_week'].unique())
    train_start_idx = CFG.lookback_weeks
    if len(dates) < train_start_idx + 10:
        print("Not enough data history.")
        return

    # To save predictions
    preds = []
    
    # Simulation Loop
    # We predict for week T using model trained on [0 .. T-gap]
    # Re-train every 4 weeks to save time, or every week
    # Notebook did rolling weekly. Let's do every week for best result.
    
    print(f"Starting training loop from week {train_start_idx}...")
    
    # For speed, we just train one big model for backtest? No, lookahead bias.
    # We must do rolling.
    
    # Initialize separate models for ensemble
    model = None
    ridge = None
    
    for i in range(train_start_idx, len(dates)):
        test_date = dates[i]
        
        # Check if we need to retrain (every 4 weeks or first run)
        should_retrain = ((i - train_start_idx) % 4 == 0) or (model is None)
        
        if should_retrain:
            train_end_idx = i - 1 - CFG.early_stop_weeks 
            valid_date_start = dates[i - CFG.early_stop_weeks]
            
            train_mask = (df_clean['date_week'] < valid_date_start)
            valid_mask = (df_clean['date_week'] >= valid_date_start) & (df_clean['date_week'] < test_date)
            
            if valid_mask.sum() == 0 or train_mask.sum() == 0:
                print(f"Skipping training for {test_date} (insufficient data)")
                continue # Use old model if available? Or skip? Better to skip or use old. 
                # If we continue here without model, next lines fail.
                # If model exists, we can allow prediction.
                if model is None: continue 
            
            if valid_mask.sum() > 0 and train_mask.sum() > 0:
                X_train = df_clean.loc[train_mask, fac_cols]
                y_train = df_clean.loc[train_mask, 'target_scaled']
                q_train = df_clean.loc[train_mask].groupby('date_week').size().values
                
                X_valid = df_clean.loc[valid_mask, fac_cols]
                y_valid = df_clean.loc[valid_mask, 'target_scaled']
                q_valid = df_clean.loc[valid_mask].groupby('date_week').size().values
                
                # --- LightGBM Ranker ---
                y_train_rel = df_clean.loc[train_mask].groupby('date_week')['target_scaled'].transform(lambda x: to_relevance_levels(x, 5))
                y_valid_rel = df_clean.loc[valid_mask].groupby('date_week')['target_scaled'].transform(lambda x: to_relevance_levels(x, 5))
                
                train_set = lgb.Dataset(X_train, y_train_rel, group=q_train)
                valid_set = lgb.Dataset(X_valid, y_valid_rel, group=q_valid, reference=train_set)
                
                model = lgb.train(
                    CFG.lgbm_params,
                    train_set,
                    valid_sets=[valid_set],
                    callbacks=[lgb.early_stopping(stopping_rounds=50), lgb.log_evaluation(0)]
                )
                
                # --- Ridge Regression ---
                ridge = Ridge(alpha=CFG.ridge_alpha)
                ridge.fit(X_train, y_train)
        
        # Predict (using current model)
        test_mask = (df_clean['date_week'] == test_date)
        if test_mask.sum() == 0 or model is None:
            continue

        X_test = df_clean.loc[test_mask, fac_cols]
        
        pred_lgb = model.predict(X_test)
        pred_ridge = ridge.predict(X_test)
        
        # Ensemble
        # Rank normalize
        rank_lgb = pd.Series(pred_lgb).rank(pct=True).values
        rank_ridge = pd.Series(pred_ridge).rank(pct=True).values
        
        pred_ensemble = (CFG.w_ranker * rank_lgb) + (CFG.w_ridge * rank_ridge)
        
        # Save Result
        res_df = df_clean.loc[test_mask, ['date_week', 'symbol', 'y_fwd1']]
        res_df['y_pred'] = pred_ensemble
        res_df['y_pred_ranker'] = pred_lgb
        res_df['y_pred_ridge'] = pred_ridge
        
        preds.append(res_df)
        
        if i % 20 == 0:
            print(f"Processed week {i}/{len(dates)} ({test_date.date()})")

    full_preds = pd.concat(preds, ignore_index=True)
    
    # Save
    print(f"Saving predictions to {OUTPUT_PRED}...")
    full_preds.to_parquet(OUTPUT_PRED)
    
    # Feature Importance (from last model)
    imp_df = pd.DataFrame({
        'feature': fac_cols,
        'importance': model.feature_importance(importance_type='gain')
    }).sort_values('importance', ascending=False)
    
    imp_file = METRICS_DIR / "feature_importance_enhanced.csv"
    imp_df.to_csv(imp_file, index=False)
    print("Top 10 Features:")
    print(imp_df.head(10))

if __name__ == "__main__":
    train_model()
