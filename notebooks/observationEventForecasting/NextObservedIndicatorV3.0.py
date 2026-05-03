def main():
    #!/usr/bin/env python
    # coding: utf-8



    import numpy as np
    import pandas as pd
    import os
    import datetime
    from datetime import datetime
    from datetime import timedelta
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import Pipeline
    from lifelines import WeibullAFTFitter
    import warnings




    from datetime import datetime, timedelta

    # Set start_full_date_str and start_date_str to 100 days before today
    today = datetime.today()
    start_full_date_str = (today - timedelta(days=100)).strftime("%Y-%m-%d")
    start_date_str = start_full_date_str
    # Define the file path template
    file_path_template = "Z:/HTOC/Data_Analytics/Data/OpDiv_Observations/htoc_opdiv_obs_d{date}.csv"




    # Calculate today's date
    today = datetime.today()
    print(today)

    # Calculate end date (today + 0 days)
    end_dt = today + timedelta(days=0)
    end_date_str = end_dt.strftime("%Y-%m-%d")
    print(end_date_str)

    # Convert string dates to datetime objects
    start_full_dt = datetime.strptime(start_full_date_str, "%Y-%m-%d")
    start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")




    # Function to load files and save them to the specified directory
    def load_files(filenames):
        dataframes = []
        for filename in filenames:
            if not os.path.exists(filename):
                print(f"File {filename} does not exist. Skipping.")
                continue
            df = pd.read_csv(filename)
            dataframes.append(df)
        return dataframes


    # Define the file path template and date range
    date_format = "%Y%m%d"
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")  # Convert start_date_str to datetime
    dates_to_pull = pd.date_range(start_date, end_dt, freq='D')

    # Generate the list of file paths
    datelist = [file_path_template.format(date=dt.strftime(date_format)) for dt in dates_to_pull]
    print(datelist)

    # Concatenate dataframes from the list of files
    src = pd.concat(load_files(datelist), ignore_index=True)

    # Clean up the 'indicator' and 'OpDiv' columns if they exist
    if 'indicator' in src.columns:
        src['indicator'] = src['indicator'].astype(str).str.split(' ', expand=True)[0].str.strip()
    if 'OpDiv' in src.columns:
        src['OpDiv'] = src['OpDiv'].astype(str).str.strip()

    # Display the cleaned dataframe
    display(src)




    src.drop(columns=['curr_date', 'indicator_key'], inplace=True)
    src.rename(columns={'obs_date': 'date'}, inplace=True)
    src['date'] = pd.to_datetime(src['date'])
    src.reset_index(drop=True, inplace=True)




    src




    src[src['indicator'] == '192.124.249.112']




    # Group the src dataframe by 'OpDiv' and get a dictionary of DataFrames for each OpDiv
    opdiv_groups = {opdiv: group for opdiv, group in src.groupby('OpDiv')}

    # Allow searching by indicator
    def get_by_indicator(indicator_value):
        return src[src['indicator'] == indicator_value]

    # Example usage:
    get_by_indicator('192.124.249.112')




    opdiv_merged = {}

    for opdiv, group_df in opdiv_groups.items():
        group_df['date'] = pd.to_datetime(group_df['date'])
        all_users = group_df['API_UserName'].unique()
        all_indicators = group_df['indicator'].unique()
        all_dates = pd.date_range(start=group_df['date'].min(), end=pd.Timestamp.now().normalize(), freq='D')
        all_combinations = pd.MultiIndex.from_product(
            [all_users, all_dates, all_indicators],
            names=['API_UserName', 'date', 'indicator']
        ).to_frame(index=False)
        all_combinations['OpDiv'] = opdiv  # Add OpDiv column

        merged = all_combinations.merge(group_df, how='left', on=['API_UserName', 'date', 'indicator', 'OpDiv'])
        merged['observations'] = merged['observations'].fillna(0).astype(int)
        merged['date'] = pd.to_datetime(merged['date'])
        merged['dayofweek'] = merged['date'].dt.dayofweek
        merged['is_weekend'] = merged['dayofweek'].isin([5, 6])
        merged['day'] = merged['date'].dt.day
        merged['month'] = merged['date'].dt.month
        merged['seen'] = (merged['observations'] > 0).astype(int)
        opdiv_merged[opdiv] = merged

    # Example: display the merged dataframe for one OpDiv
    display(opdiv_merged['DHA'])




    # Replace 'VA' with the correct OpDiv if needed
    opdiv_merged['VA'][opdiv_merged['VA']['indicator'] == '192.124.249.112']




    def load_data(filepath, n_days=100):
        df = pd.read_csv(filepath)
        df['date'] = pd.to_datetime(df['date'])
        df.sort_values(by=['indicator', 'date'], inplace=True)
        latest_dates = df['date'].drop_duplicates().sort_values().tail(n_days)
        return df[df['date'].isin(latest_dates)].copy()

    def extract_time_series_features(group):
        series = group['seen'].values
        indices = np.where(series == 1)[0]
        if len(indices) == 0:
            return pd.Series({
                'last_seen': len(series),
                'freq_1': 0,
                'freq_7': 0,
                'freq_14': 0,
                'freq_30': 0,
                'freq_45': 0,
                'avg_gap': len(series),
                'burstiness': 0,
                'label_7': 0,
                'label_14': 0,
                'label_30': 0,
                'label_45': 0
            })
        last_seen = len(series) - 1 - indices[-1]
        freq_1 = np.sum(series[-1:])
        freq_7 = np.sum(series[-7:])
        freq_14 = np.sum(series[-14:])
        freq_30 = np.sum(series[-30:])
        freq_45 = np.sum(series[-45:])
        gaps = np.diff(indices)
        avg_gap = np.mean(gaps) if len(gaps) > 0 else len(series)
        burstiness = (np.std(gaps) - avg_gap) / (np.std(gaps) + avg_gap) if len(gaps) > 1 else 0

        label_7 = 1 if np.any(series[-7:]) else 0
        label_14 = 1 if np.any(series[-14:]) else 0
        label_30 = 1 if np.any(series[-30:]) else 0
        label_45 = 1 if np.any(series[-45]) else 0
        return pd.Series({
            'last_seen': last_seen,
            'freq_1': freq_1,
            'freq_7': freq_7,
            'freq_14': freq_14,
            'freq_30': freq_30,
            'freq_45': freq_45,
            'avg_gap': avg_gap,
            'burstiness': burstiness,
            'label_7': label_7,
            'label_14': label_14,
            'label_30': label_30,
            'label_45': label_45
        })

    def build_features(df):
        features_df = df.groupby('indicator').apply(extract_time_series_features).reset_index()
        return features_df

    def train_predict(model_cls, X, y):
        if len(np.unique(y)) < 2:
            return np.full(len(y), np.nan)
        model = Pipeline([('scaler', StandardScaler()), ('clf', model_cls())])
        model.fit(X, y)
        return model.predict_proba(X)[:, 1]

    def train_gbt(X, y):
        if len(np.unique(y)) < 2:
            return np.full(len(y), np.nan)
        model = GradientBoostingClassifier()
        model.fit(X, y)
        return model.predict_proba(X)[:, 1]

    def fit_weibull_aft(X, avg_gap, event):
        aft_df = X.copy()
        aft_df['duration'] = avg_gap
        aft_df['event'] = event
        aft = WeibullAFTFitter()
        aft.fit(aft_df, duration_col='duration', event_col='event')
        return aft

    def get_model_outputs(features_df, df):
        df_pred = features_df.copy()
        X = df_pred[['last_seen', 'freq_1', 'freq_7', 'freq_14' ,'freq_30', 'freq_45', 'avg_gap', 'burstiness']]

        y_7 = df_pred['label_7']
        y_14 = df_pred['label_14']
        y_30 = df_pred['label_30']
        y_45 = df_pred['label_45']

        # Logistic Regression, Estimate baseline probabilities
        df_pred['logistic_7'] = train_predict(LogisticRegression, X, y_7)
        df_pred['logistic_14'] = train_predict(LogisticRegression, X, y_14)
        df_pred['logistic_30'] = train_predict(LogisticRegression, X, y_30)
        df_pred['logistic_45'] = train_predict(LogisticRegression, X, y_45)


        # Gradient Boosted Trees, Non-linear patterns and feature interactions
        df_pred['gbt_7'] = train_gbt(X, y_7)
        df_pred['gbt_14'] = train_gbt(X, y_14)
        df_pred['gbt_30'] = train_gbt(X, y_30)
        df_pred['gbt_45'] = train_gbt(X, y_45)

        # Exponential Model, memoryless Poisson process for frequency
        rate = (df_pred['freq_30'] / 30).clip(lower=1e-6)
        df_pred['exp_7'] = 1 - np.exp(-rate * 7)
        df_pred['exp_14'] = 1 - np.exp(-rate * 14)
        df_pred['exp_30'] = 1 - np.exp(-rate * 30)
        df_pred['exp_45'] = 1 - np.exp(-rate * 45)
        df_pred['exp_1'] = 1 - np.exp(-rate * 1)

        # Weibull AFT Model, time-to-event behavor, burstiness
        aft = fit_weibull_aft(X, df_pred['avg_gap'], y_7)
        surv_func = aft.predict_survival_function(X.assign(duration=df_pred['avg_gap'], event=y_7), times=[1, 7, 14, 30, 45])
        df_pred['weibull_1'] = 1 - surv_func.loc[1].values
        df_pred['weibull_7'] = 1 - surv_func.loc[7].values
        df_pred['weibull_14'] = 1 - surv_func.loc[14].values
        df_pred['weibull_30'] = 1 - surv_func.loc[30].values
        df_pred['weibull_45'] = 1 - surv_func.loc[45].values

        # 1-Day forecast (tomorrow)
        df_pred['logistic_1'] = train_predict(LogisticRegression, X, y_7)
        df_pred['gbt_1'] = train_gbt(X, y_7)

        # Merge in actual "seen" value for today's date
        latest_date = df['date'].max()
        today_seen = df[df['date'] == latest_date][['indicator', 'seen']].rename(columns={'seen': 'seen_today'})
        df_pred = df_pred.merge(today_seen, on='indicator', how='left')

        return df_pred

    def add_rule_and_ensemble(output):
        features = ['last_seen', 'freq_1', 'freq_7', 'freq_30', 'avg_gap', 'burstiness']
        X = output[features]

        # Rule-based labels
        output['rule_1d'] = output['last_seen'].apply(lambda x: 1 if x == 0 else 0)
        output['rule_7d'] = output['last_seen'].apply(lambda x: 1 if x <= 6 else 0)
        output['rule_14d'] = output['last_seen'].apply(lambda x: 1 if x <= 13 else 0)
        output['rule_30d'] = output['last_seen'].apply(lambda x: 1 if x <= 29 else 0)
        output['rule_45d'] = output['last_seen'].apply(lambda x: 1 if x <= 44 else 0)

        y_1 = output['rule_1d']
        y_7 = output['rule_7d']
        y_14 = output['rule_14d']
        y_30 = output['rule_30d']
        y_45 = output['rule_45d']

        def train_logistic_model(X, y):
            if len(np.unique(y)) < 2:
                return np.full(len(y), np.nan)
            model = Pipeline([
                ('scaler', StandardScaler()),
                ('clf', LogisticRegression())
            ])
            model.fit(X, y)
            return model.predict_proba(X)[:, 1]

        output['prob_1d'] = train_logistic_model(X, y_1)
        output['prob_7d'] = train_logistic_model(X, y_7)
        output['prob_14d'] = train_logistic_model(X, y_14)
        output['prob_30d'] = train_logistic_model(X, y_30)
        output['prob_45d'] = train_logistic_model(X, y_45)

        # Ensemble, combines predictions from all models and prevents overfitting
        output['ensemble_1d'] = (
            0.3 * output['prob_1d'].astype(float) +
            0.25 * output['gbt_1'] +
            0.25 * output['weibull_1'] +
            0.2 * output['exp_1']
        )
        output['ensemble_7d'] = (
            0.3 * output['prob_7d'].astype(float) +
            0.25 * output['gbt_7'] +
            0.25 * output['weibull_7'] +
            0.2 * output['exp_7']
        )
        output['ensemble_14d'] = (
            0.3 * output['prob_14d'].astype(float) +
            0.25 * output['gbt_14'] +
            0.25 * output['weibull_14'] +
            0.2 * output['exp_14']
        )
        output['ensemble_30d'] = (
            0.3 * output['prob_30d'].astype(float) +
            0.25 * output['gbt_30'] +
            0.25 * output['weibull_30'] +
            0.2 * output['exp_30']
        )
        output['ensemble_45d'] = (
            0.3 * output['prob_45d'].astype(float) +
            0.25 * output['gbt_45'] +
            0.25 * output['weibull_45'] +
            0.2 * output['exp_45']
        )
        return output

    def classify_window(prob, freq, high_thresh, label):
        if prob >= high_thresh and freq >= 2:
            return f"{label}: Highly likely"
        elif prob >= 0.07 and freq >= 1:
            return f"{label}: Possibly active"
        else:
            return f"{label}: Low confidence"

    def add_confidence_and_format(output):
        output['confidence_1d'] = output.apply(
            lambda row: classify_window(float(row['ensemble_1d']), row['freq_1'], 0.6, '1-Day'), axis=1
        )
        output['confidence_7d'] = output.apply(
            lambda row: classify_window(float(row['ensemble_7d']), row['freq_7'], 0.6, '7-Day'), axis=1
        )
        output['confidence_14d'] = output.apply(
            lambda row: classify_window(float(row['ensemble_14d']), row['freq_14'], 0.6, '14-Day'), axis=1
        )
        output['confidence_30d'] = output.apply(
            lambda row: classify_window(float(row['ensemble_30d']), row['freq_30'], 0.6, '30-Day'), axis=1
        )
        output['confidence_45d'] = output.apply(
            lambda row: classify_window(float(row['ensemble_45d']), row['freq_45'], 0.6, '45-Day'), axis=1
        )

        # Format percentages
        for col in ['prob_1d', 'prob_7d', 'prob_14d', 'prob_30d','prob_45d', 'ensemble_1d', 'ensemble_7d', 'ensemble_14d', 'ensemble_30d', 'ensemble_45d']:
            output[col] = np.clip(output[col].astype(float) * 100, 0, 100).round(2).astype(str) + '%'
        return output

    def build_production_output(output):
        warnings.simplefilter(action='ignore', category=pd.errors.SettingWithCopyWarning)
        production_output = output[[
            'indicator', 'seen_today', 'freq_1', 'freq_7', 'freq_30',
            'ensemble_1d', 'confidence_1d',
            'ensemble_7d', 'confidence_7d',
            'ensemble_14d', 'confidence_14d',
            'ensemble_30d', 'confidence_30d',
            'ensemble_45d', 'confidence_45d'
        ]].copy()
        production_output.rename(columns={
            'indicator': 'Indicator',
            'seen_today': 'Observed Today',
            'freq_1': 'Frequency (1d)',
            'freq_7': 'Frequency (7d)',
            'freq_30': 'Frequency (30d)',
            'freq_45': 'Frequency (45d)',
            'ensemble_1d': 'Probability: 1-Day',
            'confidence_1d': 'Confidence: 1-Day',
            'ensemble_7d': 'Probability: 7-Day',
            'confidence_7d': 'Confidence: 7-Day',
            'ensemble_14d': 'Probability: 14-Day',
            'confidence_14d': 'Confidence: 14-Day',
            'ensemble_30d': 'Probability: 30-Day',
            'confidence_30d': 'Confidence: 30-Day',
            'confidence_45d': 'Confidence: 45-Day'
        }, inplace=True)
        return production_output




    import warnings

    # Silence pandas groupby apply deprecation warning globally for this notebook
    warnings.filterwarnings("ignore", category=DeprecationWarning, message="DataFrameGroupBy.apply operated on the grouping columns")

    from datetime import datetime
    import os

    def main():
        today = datetime.today().date()

        prediction_path = r'C:\Users\jaskew\Documents\NOI Logs\Predictions'

        opdiv_production_outputs = {}
        opdiv_forecast_logs = {}
        production_output = None
        opdiv_df = None

        for opdiv_name, opdiv_df in opdiv_merged.items():
            opdiv_df = opdiv_df.copy()
            features_df = build_features(opdiv_df)
            output = get_model_outputs(features_df, opdiv_df)
            output = add_rule_and_ensemble(output)
            output = add_confidence_and_format(output)
            production_output = build_production_output(output)


            # Save production output
            opdiv_production_outputs[opdiv_name] = production_output

            # Save today's prediction CSV
            #opdiv_output_dir = os.path.join(prediction_path, opdiv_name)
            #os.makedirs(opdiv_output_dir, exist_ok=True)

        # Explicit unpacking of key OpDivs (optional for clarity)
        DHA_output = opdiv_production_outputs.get("DHA")
        CDC_output = opdiv_production_outputs.get("CDC")
        FDA_output = opdiv_production_outputs.get("FDA")
        NIH_output = opdiv_production_outputs.get("NIH")
        VA_output = opdiv_production_outputs.get("VA")
        HRSA_output = opdiv_production_outputs.get("HRSA")
        IHS_output = opdiv_production_outputs.get("IHS")
        OS_output = opdiv_production_outputs.get("OS")
        CMS_output = opdiv_production_outputs.get("CMS")
        HHS_output = opdiv_production_outputs.get("HHS")

        DHA_log = opdiv_forecast_logs.get("DHA")
        CDC_log = opdiv_forecast_logs.get("CDC")
        FDA_log = opdiv_forecast_logs.get("FDA")
        NIH_log = opdiv_forecast_logs.get("NIH")
        VA_log = opdiv_forecast_logs.get("VA")
        HRSA_log = opdiv_forecast_logs.get("HRSA")
        IHS_log = opdiv_forecast_logs.get("IHS")
        OS_log = opdiv_forecast_logs.get("OS")
        CMS_log = opdiv_forecast_logs.get("CMS")
        HHS_log = opdiv_forecast_logs.get("HHS")

        display(production_output.head(5))
        display(opdiv_df.head(5))

        return {
            "DHA_output": DHA_output, "CDC_output": CDC_output, "FDA_output": FDA_output,
            "NIH_output": NIH_output, "VA_output": VA_output, "HRSA_output": HRSA_output,
            "IHS_output": IHS_output, "OS_output": OS_output, "CMS_output": CMS_output,
            "HHS_output": HHS_output,
            "DHA_log": DHA_log, "CDC_log": CDC_log, "FDA_log": FDA_log,
            "NIH_log": NIH_log, "VA_log": VA_log, "HRSA_log": HRSA_log,
            "IHS_log": IHS_log, "OS_log": OS_log, "CMS_log": CMS_log,
            "HHS_log": HHS_log
        }


    if __name__ == "__main__":
        main()




    ### Add this section at the end of your NextObservedIndicatorV2.0 notebook to automate the feedback loop per OPDIV

    import pandas as pd
    from pathlib import Path
    from sklearn.ensemble import GradientBoostingClassifier
    import pickle

    # 5) Load forecast logs from all OPDIV folders
    logs_base = Path('Logs')  # adjust path if needed
    opdiv_logs = {}
    for sub in logs_base.iterdir():
        log_file = sub / 'forecast_log.xlsx'
        if log_file.exists():
            df = pd.read_excel(log_file)
            df = df[df['Outcome'].str.lower() != 'pending']
            opdiv_logs[sub.name] = df
    if not opdiv_logs:
        raise FileNotFoundError(f"No forecast_log.xlsx found under {logs_base}")
    print(f"Found logs for OPDIVs: {list(opdiv_logs.keys())}")

    # 6) Loop through each OPDIV to process, merge, retrain
    for opdiv, log_df in opdiv_logs.items():
        print(f"\nProcessing {opdiv}, {len(log_df)} records...")

        # Re-extract features (use your existing function)
        feats = (
            log_df
            .groupby(['Indicator', 'ForecastDate'])
            .apply(extract_time_series_features)
            .reset_index(drop=True)
        )
        # Map true outcomes to labels
        feats['y_true_7d'] = (log_df['Outcome'] == 'Seen').astype(int)

        # Prepare master path per OPDIV
        master_path = Path(f"train_master_{opdiv}.csv")
        if master_path.exists():
            master = pd.read_csv(master_path)
            updated_master = pd.concat([master, feats], ignore_index=True)
        else:
            updated_master = feats.copy()

        # Remove duplicates by key
        updated_master.drop_duplicates(subset=['Indicator', 'ForecastDate'], keep='last', inplace=True)
        updated_master.to_csv(master_path, index=False)
        print(f"Updated master for {opdiv}: {len(updated_master)} rows saved to {master_path}")

        # 7) Retrain model for this OPDIV
        feature_cols = [c for c in updated_master.columns if c not in ['Indicator','ForecastDate','y_true_7d']]
        X = updated_master[feature_cols]
        y = updated_master['y_true_7d']
        clf = GradientBoostingClassifier(n_estimators=200, max_depth=3)
        clf.fit(X, y)
        model_file = f"gbc_7d_{opdiv}.pkl"
        with open(model_file, 'wb') as f:
            pickle.dump(clf, f)
        print(f"Retrained and saved model for {opdiv} -> {model_file}")

        # (Optional) Quick hold-out validation example
        # from sklearn.metrics import classification_report
        # val = updated_master.sample(frac=0.1, random_state=42)
        # print(classification_report(val['y_true_7d'], clf.predict(val[feature_cols])))


if __name__ == "__main__":
    main()
