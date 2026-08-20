import sqlite3
import pandas as pd
import os
import pycountry
import json
import numpy as np

# Base directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Root of the project
JSON_DIR = os.path.join(BASE_DIR, "json")  # Path to JSON folder
DATA_DIR = os.path.join(BASE_DIR, "ddb")  # Path to database folder
CSV_UN_DIR = os.path.join(DATA_DIR, "UN")
JSON_UN_DIR = os.path.join(JSON_DIR, "UN_JSON")
CSV_AQUASTAT_DIR = os.path.join(DATA_DIR, "AQUASTAT")
JSON_AQUASTAT_DIR = os.path.join(JSON_DIR, "AQUASTAT_JSON")
EEA_DIR = os.path.join(DATA_DIR, "EEA")
CSV_EEA_DIR = os.path.join(EEA_DIR, "CSV_DATA")
JSON_EEA_DIR = os.path.join(JSON_DIR, "EEA_JSON")
json_file_water_composition_europe = os.path.join(JSON_DIR, "EEA_JSON", "water_composition_europe.json")
db_file_disaggregated = os.path.join(DATA_DIR, "EEA", "sqlDB", "Waterbase_v2023_1_WISE6_DisaggregatedData.sqlite")
db_file_aggregated = os.path.join(DATA_DIR, "EEA", "sqlDB", "Waterbase_v2023_1_WISE6.sqlite")


def ensure_json_folder():
    """Ensures the JSON directory exists."""
    if not os.path.exists(JSON_DIR):
        os.makedirs(JSON_DIR)
        print(f"Created missing folder: {JSON_DIR}")


def convert_alpha2_to_alpha3(alpha2):
    """Converts ISO2 country code to ISO3."""
    # Values not available in pycountry
    if alpha2 == "EL": # Greece
        return "GRC"
    elif alpha2 == "XK": # Kosovo
        return "XKX"
    elif alpha2 == "EU27_2020":
        return ""
    else:
        try:
            country = pycountry.countries.get(alpha_2=alpha2)
            return country.alpha_3 if country else alpha2
        except:
            return None  # Return None if conversion fails

def country_to_iso3(country_name):
    """Converts country name to ISO Alpha-3 code."""
    try:
        return pycountry.countries.lookup(country_name).alpha_3
    except LookupError:
        return None


def generate_json_Water_points():
    """Generates JSON with monitoring site locations."""
    json_file_monitoring_sites = os.path.join(JSON_DIR, "EEA_JSON", "monitoring_sites.json")
    ensure_json_folder()
    if os.path.exists(json_file_monitoring_sites):
        print(f"{json_file_monitoring_sites} already exists. No action needed.")
        return

    if not os.path.exists(db_file_disaggregated):
        print(f"Database not found: {db_file_disaggregated}")
        return

    print("Generating monitoring site JSON...")
    try:
        conn = sqlite3.connect(db_file_disaggregated)
        query = """
        SELECT monitoringSiteName, lat, lon, countryCode 
        FROM S_WISE6_SpatialObject_DerivedData 
        WHERE lat IS NOT NULL AND lon IS NOT NULL
        """
        df = pd.read_sql_query(query, conn)
        conn.close()

        df.to_json(json_file_monitoring_sites, orient="records")
        print(f"Data saved in {json_file_monitoring_sites}!")
    except Exception as e:
        print(f"Error generating {json_file_monitoring_sites}: {e}")


def generate_json_belgium_monitoring_sites():
    """Generates JSON with Belgium monitoring site locations."""
    json_file_monitoring_sites = os.path.join(JSON_DIR, "EEA_JSON", "belgium_composition.json")
    ensure_json_folder()
    
    if os.path.exists(json_file_monitoring_sites):
        print(f"{json_file_monitoring_sites} already exists. No action needed.")
        return

    if not os.path.exists(db_file_disaggregated):
        print(f"Database not found: {db_file_disaggregated}")
        return

    print("Generating monitoring site JSON...")
    try:
        conn = sqlite3.connect(db_file_disaggregated)
        query = """
        SELECT 
            s.monitoringSiteIdentifier,
            s.monitoringSiteName,
            s.lat,
            s.lon,
            s.waterBodyName,
            JSON_GROUP_ARRAY(
                DISTINCT JSON_OBJECT(
                    'observedPropertyDeterminandLabel', avg_data.observedPropertyDeterminandLabel,
                    'averageObservedValue', avg_data.avgResultObservedValue,
                    'resultUom', avg_data.resultUom
                )
            ) AS observedData
        FROM S_WISE6_SpatialObject_DerivedData s
        JOIN (
            SELECT 
                monitoringSiteIdentifier, 
                observedPropertyDeterminandLabel, 
                AVG(resultObservedValue) AS avgResultObservedValue,
                resultUom
            FROM T_WISE6_DisaggregatedData
            WHERE observedPropertyDeterminandLabel IN (
                'Mercury and its compounds',
                'Lead and its compounds',
                'Cadmium and its compounds',
                'Atrazine',
                'Glyphosate',
                'Polychlorinated biphenyls',
                'Perfluorooctane sulfonic acid (PFOS) and its derivatives',
                'Benzene',
                'Nitrate',
                'Total phosphorus'
            )
            GROUP BY monitoringSiteIdentifier, observedPropertyDeterminandLabel, resultUom
        ) AS avg_data
        ON s.monitoringSiteIdentifier = avg_data.monitoringSiteIdentifier
        WHERE s.lat IS NOT NULL 
        AND s.lon IS NOT NULL 
        AND s.countryCode = 'BE'
        GROUP BY s.monitoringSiteIdentifier;
        """
        df = pd.read_sql_query(query, conn)
        conn.close()

        #Verification of the columns
        expected_columns = ["monitoringSiteIdentifier", "monitoringSiteName", "lat", "lon", "waterBodyName", "observedData"]
        df.rename(columns=lambda x: x.strip(), inplace=True)  # Remove leading/trailing spaces from column names
        missing_columns = [col for col in expected_columns if col not in df.columns]
        if missing_columns:
            print(f"Warning: Missing columns in dataframe: {missing_columns}")

        #Convert observedData to JSON
        df["observedData"] = df["observedData"].apply(lambda x: json.loads(x) if isinstance(x, str) else x)

        #Check if observedData is a list
        for index, row in df.iterrows():
            if not isinstance(row["observedData"], list):
                print(f"Warning: Invalid observedData format at index {index}, resetting to empty list.")
                df.at[index, "observedData"] = []

        #Save to JSON
        df.to_json(json_file_monitoring_sites, orient="records", indent=4)
        print(f"Data saved in {json_file_monitoring_sites}!")
    except Exception as e:
        print(f"Error generating {json_file_monitoring_sites}: {e}")
    
def generate_json_water_composition_BE_EU():
    json_file_water_composition = os.path.join(JSON_DIR, "EEA_JSON", "BEandEU_water_composition.json")
    ensure_json_folder()

    if os.path.exists(json_file_water_composition):
        print(f"{json_file_water_composition} already exists. No action needed.")
        return

    if not os.path.exists(db_file_aggregated):
        print(f"Database not found: {db_file_aggregated}")
        return

    print("Generating JSON with Belgium's latest value & EU averages...")

    try:
        conn = sqlite3.connect(db_file_aggregated)
        # Query for the most recent Belgian value per determinand
        query_be = """
        SELECT 
            observedPropertyDeterminandLabel,
            AVG(resultMeanValue) AS avgResultMeanValue_2010_2023
        FROM T_WISE6_AggregatedData
        WHERE countryCode = 'BE' 
        AND phenomenonTimeReferenceYear BETWEEN 2010 AND 2023
        AND observedPropertyDeterminandLabel IN (
            'Phosphate',
            'Nickel and its compounds',
            'Cadmium and its compounds',
            'Dissolved organic carbon (DOC)',
            'Lead and its compounds',
            'pH',
            'Water temperature',
            'Oxygen saturation',
            'Electrical conductivity',
            'Dissolved oxygen',
            'Nitrate',
            'Total phosphorus',
            'Nitrite',
            'BOD5',
            'Ammonium',
            'CODCr',
            'Benzo(g,h,i)perylene',
            'Benzo(a)pyrene',
            'Fluoranthene',
            'Total nitrogen'
        )
        GROUP BY observedPropertyDeterminandLabel;
        """
        df_be = pd.read_sql_query(query_be, conn)

        # Query for EU average per determinand
        query_eu = """
        SELECT 
            observedPropertyDeterminandLabel,
            AVG(resultMeanValue) AS eu_averageMeanValue
        FROM T_WISE6_AggregatedData
        WHERE phenomenonTimeReferenceYear BETWEEN 2010 AND 2023
        AND observedPropertyDeterminandLabel IN (
            'Phosphate',
            'Nickel and its compounds',
            'Cadmium and its compounds',
            'Dissolved organic carbon (DOC)',
            'Lead and its compounds',
            'pH',
            'Water temperature',
            'Oxygen saturation',
            'Electrical conductivity',
            'Dissolved oxygen',
            'Nitrate',
            'Total phosphorus',
            'Nitrite',
            'BOD5',
            'Ammonium',
            'CODCr',
            'Benzo(g,h,i)perylene',
            'Benzo(a)pyrene',
            'Fluoranthene',
            'Total nitrogen'
        )
        GROUP BY observedPropertyDeterminandLabel;
        """
        df_eu = pd.read_sql_query(query_eu, conn)
        conn.close()

        #Merge Belgium's latest values with EU averages
        df_final = df_be.merge(df_eu, on="observedPropertyDeterminandLabel", how="left")

        json_data = df_final.to_dict(orient="records")

        with open(json_file_water_composition, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=4)

        print(f"Data saved in {json_file_water_composition}!")

    except Exception as e:
        print(f"Error generating {json_file_water_composition}: {e}")
    
#Generate Mean Pollution JSON
def generate_json_water_composition_europe():
    """Generates JSON with mean pollution levels per country."""
    ensure_json_folder()
    if os.path.exists(json_file_water_composition_europe):
        print(f"{json_file_water_composition_europe} already exists. No action needed.")
        return

    if not os.path.exists(db_file_aggregated):
        print(f"Database not found!")
        return

    print("Generating water composition europe JSON...")
    try:
        conn = sqlite3.connect(db_file_aggregated)
        query = """
                WITH MostCommonUnit AS (
            SELECT 
                countryCode,
                observedPropertyDeterminandLabel,
                resultUom,
                COUNT(*) AS unit_count,
                ROW_NUMBER() OVER (
                    PARTITION BY countryCode, observedPropertyDeterminandLabel 
                    ORDER BY COUNT(*) DESC
                ) AS rn
            FROM T_WISE6_AggregatedData
            GROUP BY countryCode, observedPropertyDeterminandLabel, resultUom
        ),
        CleanedData AS (
            SELECT *
            FROM T_WISE6_AggregatedData
            WHERE (
                (observedPropertyDeterminandLabel = 'Lead and its compounds' AND resultMeanValue BETWEEN 0 AND 500)
            OR (observedPropertyDeterminandLabel = 'Mercury and its compounds' AND resultMeanValue BETWEEN 0 AND 5)
            OR (observedPropertyDeterminandLabel = 'Nickel and its compounds' AND resultMeanValue BETWEEN 0 AND 500)
            OR (observedPropertyDeterminandLabel = 'Ammonium' AND resultMeanValue BETWEEN 0 AND 10)
            OR (observedPropertyDeterminandLabel = 'Cadmium and its compounds' AND resultMeanValue BETWEEN 0 AND 1)
            OR (observedPropertyDeterminandLabel NOT IN (
                    'Lead and its compounds',
                    'Mercury and its compounds',
                    'Nickel and its compounds',
                    'Ammonium',
                    'Cadmium and its compounds'
                ))
            )
        ),
        FilteredData AS (
            SELECT a.*
            FROM CleanedData a
            INNER JOIN MostCommonUnit u
                ON a.countryCode = u.countryCode
                AND a.observedPropertyDeterminandLabel = u.observedPropertyDeterminandLabel
                AND a.resultUom = u.resultUom
            WHERE u.rn = 1
        )
        SELECT 
            f.countryCode,
            f.observedPropertyDeterminandLabel,
            AVG(f.resultMeanValue) AS resultMeanValue,
            f.resultUom,
            COUNT(*) AS n_samples,
            MIN(f.resultMeanValue) AS min_val,
            MAX(f.resultMeanValue) AS max_val
        FROM FilteredData f
        GROUP BY f.countryCode, f.observedPropertyDeterminandLabel;
        """
        df_final = pd.read_sql_query(query, conn)
        conn.close()

        # Convert ISO2 to ISO3
        df_final["countryCode"] = df_final["countryCode"].apply(convert_alpha2_to_alpha3)
        
        
        df_final.dropna(subset=["countryCode"], inplace=True)

        # Save to JSON
        df_final.to_json(json_file_water_composition_europe, orient="records")
        print(f"Data saved in {json_file_water_composition_europe}!")
    except Exception as e:
        print(f"Error generating {json_file_water_composition_europe}: {e}")

    
def extract_iso3(gems_code):
    """Extracts the ISO3 code from the GEMS code."""
    if pd.isna(gems_code):
        return None
    gems_code = str(gems_code).strip()  # Remove leading/trailing spaces
    if "BEL" in gems_code:  # Check if "BEL" is in the GEMS code (Example: BEL-12345)
        return "BEL"
    else:
        return gems_code[:3] 

def UN_DB_CSV_TO_JSON():
    """Converts UN CSV files to JSON format with cleaned and grouped data."""
    csv_files = [f for f in os.listdir(CSV_UN_DIR) if f.endswith(".csv")]

    for file in csv_files:
        try:
            csv_path = os.path.join(CSV_UN_DIR, file)
            df = pd.read_csv(csv_path, encoding="ISO-8859-1", sep=";", low_memory=False)

            # Nettoyage de base
            df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
            df["ISO3"] = df["GEMS.Station.Number"].apply(extract_iso3)
            df["Sample.Date"] = pd.to_datetime(df["Sample.Date"], errors="coerce")
            df["Year"] = df["Sample.Date"].dt.year
            df = df[df["Year"] >= 1960]

            df.drop(columns=["GEMS.Station.Number", "Sample.Date", "Sample.Time", "Depth",
                             "Analysis.Method.Code", "Value.Flags", "Data.Quality"],
                    inplace=True, errors="ignore")

            bins = [1960, 1980, 2000, 2024]
            labels = ["1960-1980", "1980-2000", "2000-2023"]
            df["Year_Bin"] = pd.cut(df["Year"], bins=bins, labels=labels, right=False)

            df.dropna(subset=["ISO3", "Value", "Unit", "Parameter.Code"], inplace=True)
            df["Year_Bin"] = df["Year_Bin"].astype(str)

            results = []

            for parameter in df["Parameter.Code"].unique():
                df_param = df[df["Parameter.Code"] == parameter].copy()

                # Garde l’unité dominante pour ce paramètre
                most_common_unit = df_param["Unit"].value_counts().idxmax()
                df_param = df_param[df_param["Unit"] == most_common_unit]

                # Filtrage spécifique pour le zinc
                if parameter.lower() in ["zn", "zn2+", "zinc"]:
                    df_param = df_param[df_param["Value"] < 1000]

                # Moyenne par pays/période
                grouped = df_param.groupby(["ISO3", "Year_Bin"], as_index=False).agg({
                    "Value": "mean",
                    "Unit": "first"
                })
                grouped["Parameter"] = parameter
                results.append(grouped)

            if not results:
                print(f"Aucune donnée exploitable dans {file}")
                continue

            # Fusionne tous les paramètres en un seul DataFrame
            df_all = pd.concat(results, ignore_index=True)
            df_all.replace({np.nan: None}, inplace=True)
            json_data = df_all.to_dict(orient="records")

            # Sauvegarde
            json_file = file.replace(".csv", ".json")
            json_path = os.path.join(JSON_UN_DIR, json_file)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2)

            print(f"✅ JSON Created: {json_file}")

        except Exception as e:
            print(f"❌ Error with {file}: {e}")


def AQUASTAT_CSV_TO_JSON():
    """Converts AQUASTAT CSV files to JSON format."""
    csv_path_aquastat = os.path.join(CSV_AQUASTAT_DIR, "AQUASTATDisseminationSystem.csv")
    df = pd.read_csv(csv_path_aquastat)

    # Function to correct the percentage values
    def correct_percentage(value, variable_name):
        """Corrects percentage values based on variable name."""
        if isinstance(value, (int, float)):
            # If the variable is a percentage, divide by 10 if it's > 100 (assumed formatting error)
            if "Agricultural water withdrawal as % of total renewable water resources" in variable_name or "SDG 6.4.2. Water Stress" in variable_name:
                if value > 1000:
                    return value / 100
                elif value > 100:
                    return value / 10
        return value

    df["Value"] = df.apply(lambda row: correct_percentage(row["Value"], row["Variable"]), axis=1)

    def remove_outliers(group):
        """Removes outliers from the group based on mean and standard deviation."""
        mean = group["Value"].mean()
        std_dev = group["Value"].std()
        threshold = 10  #  Limit for outlier detection
        lower_limit = mean - threshold * std_dev
        upper_limit = mean + threshold * std_dev
        return group[(group["Value"] >= lower_limit) & (group["Value"] <= upper_limit)]

    df = df.groupby("Variable", group_keys=False).apply(lambda group: remove_outliers(group))
    df["ISO3"] = df["Area"].apply(country_to_iso3)
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
    df = df[["ISO3", "Year", "Value", "Variable"]]
    max_values = df.groupby("Variable")["Value"].max()
    print("Valeurs maximales par variable:")
    print(max_values)

    json_path_aquastat = os.path.join(JSON_AQUASTAT_DIR, "aquastat.json")
    df.to_json(json_path_aquastat, orient="records")


def CSV_BathingWaterToJson():
    """Converts Bathing Water CSV files to JSON format."""
    csv_path_bathingwater = os.path.join(CSV_EEA_DIR, "BathingWaterWithExcellentQuality.csv")
    df = pd.read_csv(csv_path_bathingwater)

    df["time"] = pd.to_numeric(df["time"], errors="coerce")
    df["obs_value"] = pd.to_numeric(df["obs_value"], errors="coerce")
    df["geo_label"] = df["geo_label"].replace({
        "Kosovo (under United Nations Security Council Resolution 1244/99)": "Kosovo",
        "European Union - 27 countries (from 2020)": "European Union"
    })

    # Select relevant columns
    df = df[["geo_label", "dimension_label", "time", "obs_value", ]]
    json_path_bathingwater = os.path.join(JSON_EEA_DIR, "bathing_water.json")
    df.to_json(json_path_bathingwater, orient="records")
    print(f"Saved file: {json_path_bathingwater}")

def CSV_WaterExploitationIndex_toJson():
    """Converts Water Exploitation Index CSV files to JSON format."""
    csv_path_waterEI = os.path.join(CSV_EEA_DIR, "WaterExploitationIndex.csv")
    df = pd.read_csv(csv_path_waterEI)

    df["time"] = pd.to_numeric(df["time"], errors="coerce")
    df["obs_value"] = pd.to_numeric(df["obs_value"], errors="coerce")

    # Fix name issues
    df["geo_label"] = df["geo_label"].replace({
        "Kosovo (under United Nations Security Council Resolution 1244/99)": "Kosovo",
        "European Union - 27 countries (from 2020)": "European Union"
    })
    df = df[["geo_label", "dimension_label", "time", "obs_value", ]]
    json_path_waterEI = os.path.join(JSON_EEA_DIR, "WaterExploitationIndex.json")

    df.to_json(json_path_waterEI, orient="records")

    print(f"JSON SAVED : : {json_path_waterEI}")

def CSV_BE_EU_WaterData_ToJson():
    """Converts Bathing Water and Water Exploitation Index CSV files to JSON format for Belgium and EU."""
    csv_path_bathingwater = os.path.join(CSV_EEA_DIR, "BathingWaterWithExcellentQuality.csv")
    csv_path_waterEI = os.path.join(CSV_EEA_DIR, "WaterExploitationIndex.csv")
    df_bathing = pd.read_csv(csv_path_bathingwater)
    df_waterEI = pd.read_csv(csv_path_waterEI)

    for df in [df_bathing, df_waterEI]:
        df["time"] = pd.to_numeric(df["time"], errors="coerce")
        df["obs_value"] = pd.to_numeric(df["obs_value"], errors="coerce")
        df["geo_label"] = df["geo_label"].replace({
            "Kosovo (under United Nations Security Council Resolution 1244/99)": "Kosovo",
            "European Union - 27 countries (from 2020)": "European Union"
        })
    df_bathing = df_bathing[df_bathing["unit_label"] != "Number"]

    df_bathing = df_bathing[~df_bathing["dimension"].isin(["INL", "CST"])]
    # Filter for Belgium and EU
    df_bathing = df_bathing[df_bathing["geo_label"].isin(["Belgium", "European Union"])]
    df_waterEI = df_waterEI[df_waterEI["geo_label"].isin(["Belgium", "European Union"])]
    df_bathing = df_bathing.groupby(["geo_label", "time", "dimension", "unit_label"], as_index=False)["obs_value"].mean()
    df_waterEI = df_waterEI[["geo_label", "dimension_label", "time", "obs_value"]]

    json_path_bathing = os.path.join(JSON_EEA_DIR, "BathingWaterQuality_BE_EU.json")
    json_path_waterEI = os.path.join(JSON_EEA_DIR, "WaterExploitationIndex_BE_EU.json")

    df_bathing.to_json(json_path_bathing, orient="records")
    df_waterEI.to_json(json_path_waterEI, orient="records")

    print(f"JSON SAVED : {json_path_bathing}")
    print(f"JSON SAVED : {json_path_waterEI}")



#Run all generators when executed directly
if __name__ == "__main__":
    generate_json_Water_points()
    generate_json_belgium_monitoring_sites()
    generate_json_water_composition_BE_EU()
    generate_json_water_composition_europe()
    UN_DB_CSV_TO_JSON()
    AQUASTAT_CSV_TO_JSON()
    CSV_BathingWaterToJson()
    CSV_WaterExploitationIndex_toJson()
    CSV_BE_EU_WaterData_ToJson()
