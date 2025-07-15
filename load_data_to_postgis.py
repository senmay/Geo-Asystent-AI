import geopandas as gpd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
from pathlib import Path

# This script is designed to be run from the project's root directory.

def load_data():
    """
    Connects to the PostGIS database and uploads all .shp files
    from the sample_data directory.
    """
    # Explicitly point to the .env file in the project root
    project_root = Path(__file__).parent
    dotenv_path = project_root / ".env"
    
    if not dotenv_path.exists():
        print(f"CRITICAL: .env file not found at {dotenv_path}. Make sure it exists in the project root.")
        return
        
    print(f"Loading environment variables from: {dotenv_path}")
    load_dotenv(dotenv_path=dotenv_path)
    
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")

    if not all([db_user, db_pass, db_host, db_port, db_name]):
        print("CRITICAL: One or more database environment variables are not set in your .env file.")
        return

    engine_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    print(f"Connecting to database: {engine_url.replace(db_pass, '****')}")
    engine = create_engine(engine_url)

    data_dir = project_root / "sample_data"
    
    shapefiles = [f for f in os.listdir(data_dir) if f.endswith('.shp')]
    
    if not shapefiles:
        print(f"No shapefiles found in '{data_dir}'.")
        return

    print(f"Found shapefiles to load: {shapefiles}")

    for shp_file in shapefiles:
        try:
            file_path = data_dir / shp_file
            print(f"\nReading {file_path}...")
            gdf = gpd.read_file(file_path)
            
            table_name = file_path.stem
            
            print(f"Loading data into table '{table_name}'...")
            
            gdf.to_postgis(
                name=table_name,
                con=engine,
                if_exists="replace",
                index=True,
                index_label='id'
            )
            
            print(f"Successfully loaded {len(gdf)} features into '{table_name}'.")

        except Exception as e:
            print(f"Failed to load {shp_file}. Error: {e}")

if __name__ == "__main__":
    load_data()
