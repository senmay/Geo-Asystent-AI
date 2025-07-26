import geopandas as gpd
from langchain.tools import tool
import os
from sqlalchemy.engine import Engine
import logging

from exceptions import (
    LayerNotFoundError,
    InvalidLayerNameError,
    GISDataProcessingError,
    DatabaseConnectionError,
    SpatialQueryError
)
from utils.db_logger import log_database_operation
from utils.result_helpers import (
    limit_results_for_display, 
    add_simple_id_messages, 
    create_parcel_message,
    create_numbered_parcel_message
)

logger = logging.getLogger(__name__)

@tool
def get_layer_as_geojson(layer_name: str, db_engine: Engine) -> str:
    """
    Retrieves a GIS layer from the PostGIS database using a provided database engine,
    reprojects it to WGS 84 (EPSG:4326), and returns it as a GeoJSON string.
    Recognizes layer names like 'parcels', 'buildings', 'parcels_low', 'buildings_low'.
    """
    logger.info(f"Starting get_layer_as_geojson operation", extra={
        'operation': 'get_layer_as_geojson',
        'layer_name': layer_name
    })

    normalized_input = layer_name.lower().strip()
    base_layer_name = None
    id_column = None
    
    if "parcel" in normalized_input or "działki" in normalized_input:
        base_layer_name = "parcels"
        id_column = "ID_DZIALKI"
    elif "building" in normalized_input or "budynki" in normalized_input:
        base_layer_name = "buildings"
        id_column = "ID_BUDYNKU"
    elif "gpz" in normalized_input:
        base_layer_name = normalized_input
        id_column = "id"
    
    if not base_layer_name:
        raise InvalidLayerNameError(
            layer_name=layer_name,
            valid_patterns=["działki", "budynki", "gpz"]
        )

    # GPZ layer doesn't have a _low version
    if base_layer_name == "gpz_110kv":
        table_to_use = base_layer_name
    else:
        table_to_use = f"{base_layer_name}_low"
    
    logger.debug(f"Querying table: '{table_to_use}'", extra={
        'operation': 'get_layer_as_geojson',
        'table_name': table_to_use,
        'base_layer': base_layer_name
    })

    try:
        sql = f'SELECT * FROM "{table_to_use}";'
        
        # Handle different geometry column names
        geom_col = 'geom' if base_layer_name == "gpz_110kv" else 'geometry'
        
        try:
            gdf = gpd.read_postgis(sql, db_engine, geom_col=geom_col)
        except Exception as e:
            raise DatabaseConnectionError(
                operation=f"reading from table '{table_to_use}'",
                original_error=e
            )
        
        if gdf.empty:
            raise LayerNotFoundError(layer_name=layer_name)
        
        logger.info(f"Successfully read {len(gdf)} features from table '{table_to_use}'", extra={
            'operation': 'get_layer_as_geojson',
            'table_name': table_to_use,
            'feature_count': len(gdf)
        })
        
        try:
            gdf_reprojected = gdf.to_crs(epsg=4326)
            gdf_reprojected['loaded_layer'] = table_to_use
            
            # Add a message with the ID
            if id_column and id_column in gdf.columns:
                gdf_reprojected = add_simple_id_messages(gdf_reprojected, id_column)
            
            return gdf_reprojected.to_json()
            
        except Exception as e:
            raise GISDataProcessingError(
                operation="coordinate transformation and GeoJSON conversion",
                original_error=e
            )
        
    except (InvalidLayerNameError, LayerNotFoundError, DatabaseConnectionError, GISDataProcessingError):
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        # Try fallback to full resolution table
        logger.warning(f"Failed to read from '{table_to_use}', trying full resolution table")
        table_to_use = base_layer_name
        
        try:
            sql = f'SELECT * FROM "{table_to_use}";'
            gdf = gpd.read_postgis(sql, db_engine, geom_col='geometry')
            
            if gdf.empty:
                raise LayerNotFoundError(layer_name=layer_name)
            
            logger.info(f"Successfully read {len(gdf)} features from fallback table '{table_to_use}'")
            
            gdf_reprojected = gdf.to_crs(epsg=4326)
            gdf_reprojected['loaded_layer'] = table_to_use
            
            if id_column and id_column in gdf.columns:
                gdf_reprojected = add_simple_id_messages(gdf_reprojected, id_column)

            return gdf_reprojected.to_json()
            
        except Exception as final_e:
            raise GISDataProcessingError(
                operation=f"reading from fallback table '{table_to_use}'",
                original_error=final_e
            )

@tool
def find_largest_parcel(db_engine: Engine) -> str:
    """
    Finds the single largest parcel by area and returns it as a GeoJSON string.
    The result also includes the parcel's ID and its area in square meters.
    """
    logger.info("Starting find_largest_parcel operation", extra={
        'operation': 'find_largest_parcel'
    })
    
    table_name = "parcels_low"
    
    sql = f"""
        SELECT *, ST_Area(geometry) as area_sqm
        FROM "{table_name}"
        ORDER BY area_sqm DESC
        LIMIT 1;
    """
    
    try:
        with log_database_operation("find_largest_parcel", table=table_name):
            gdf = gpd.read_postgis(sql, db_engine, geom_col='geometry')
            
        if gdf.empty:
            raise LayerNotFoundError(layer_name="parcels", available_layers=["parcels_low", "parcels"])
            
        parcel_id = gdf.iloc[0].get('ID_DZIALKI', 'N/A')
        area_sqm = gdf.iloc[0]['area_sqm']
        logger.info(f"Found largest parcel with ID: {parcel_id}", extra={
            'operation': 'find_largest_parcel',
            'parcel_id': parcel_id,
            'area_sqm': area_sqm
        })
        
        try:
            gdf_reprojected = gdf.to_crs(epsg=4326)
            parcel_id = gdf.iloc[0].get('ID_DZIALKI', 'Brak ID')
            gdf_reprojected['message'] = create_parcel_message(parcel_id, area_sqm, "largest")
            
            return gdf_reprojected.to_json()
            
        except Exception as e:
            raise GISDataProcessingError(
                operation="coordinate transformation and GeoJSON conversion for largest parcel",
                original_error=e
            )
            
    except (LayerNotFoundError, GISDataProcessingError):
        raise
    except Exception as e:
        raise DatabaseConnectionError(
            operation=f"finding largest parcel in table '{table_name}'",
            original_error=e
        )

@tool
def find_n_largest_parcels(n: int, db_engine: Engine) -> str:
    """
    Finds the N largest parcels by area and returns them as a GeoJSON string.
    The result also includes each parcel's ID and its area in square meters.
    """
    logger.info(f"Starting find_n_largest_parcels operation", extra={
        'operation': 'find_n_largest_parcels',
        'n': n
    })
    
    table_name = "parcels_low"
    
    sql = f"""
        SELECT *, ST_Area(geometry) as area_sqm
        FROM "{table_name}"
        ORDER BY area_sqm DESC
        LIMIT {n};
    """
    
    try:
        gdf = gpd.read_postgis(sql, db_engine, geom_col='geometry')
        if gdf.empty:
            return f"Error: Could not find any parcels in the database."
            
        logger.info(f"Found {len(gdf)} largest parcels", extra={
            'operation': 'find_n_largest_parcels',
            'n': n,
            'found_count': len(gdf)
        })
        
        gdf_reprojected = gdf.to_crs(epsg=4326)
        
        # Limit results for display
        limited_gdf, summary = limit_results_for_display(gdf_reprojected, max_display=5, item_type="działka")
        
        messages = []
        for index, row in limited_gdf.iterrows():
            parcel_id = row.get('ID_DZIALKI', 'Brak ID')
            area_sqm = row['area_sqm']
            messages.append(create_numbered_parcel_message(index + 1, parcel_id, area_sqm))
        
        # Add summary message if there are more results
        if summary:
            messages.append(summary)
        
        limited_gdf['message'] = messages
        
        return limited_gdf.to_json()
    except Exception as e:
        return f"Error finding the {n} largest parcels: {e}"

@tool
def find_parcels_above_area(min_area: float, db_engine: Engine) -> str:
    """
    Finds all parcels with an area greater than a specified minimum area and returns them as a GeoJSON string.
    The result also includes each parcel's ID and its area in square meters.
    """
    logger.info(f"Starting find_parcels_above_area operation", extra={
        'operation': 'find_parcels_above_area',
        'min_area': min_area
    })
    
    table_name = "parcels_low"
    
    sql = f"""
        SELECT *, ST_Area(geometry) as area_sqm
        FROM "{table_name}"
        WHERE ST_Area(geometry) > {min_area};
    """
    
    try:
        gdf = gpd.read_postgis(sql, db_engine, geom_col='geometry')
        if gdf.empty:
            return f"Error: Could not find any parcels with an area greater than {min_area} m²."
            
        logger.info(f"Found {len(gdf)} parcels with area above {min_area} m²", extra={
            'operation': 'find_parcels_above_area',
            'min_area': min_area,
            'found_count': len(gdf)
        })
        
        gdf_reprojected = gdf.to_crs(epsg=4326)
        
        # Limit results for display
        limited_gdf, summary = limit_results_for_display(gdf_reprojected, max_display=5, item_type="działka")
        
        messages = []
        for index, row in limited_gdf.iterrows():
            parcel_id = row.get('ID_DZIALKI', 'Brak ID')
            area_sqm = row['area_sqm']
            messages.append(create_parcel_message(parcel_id, area_sqm, "standard"))
        
        # Add summary message if there are more results
        if summary:
            messages.append(summary)
            
        limited_gdf['message'] = messages
        
        return limited_gdf.to_json()
    except Exception as e:
        return f"Error finding parcels above {min_area} m²: {e}"

@tool
def find_parcels_near_gpz(radius_meters: int, db_engine: Engine) -> str:
    """
    Finds all parcels within a specified radius of any GPZ point.
    The result includes each parcel's ID and its area.
    The radius is specified in meters.
    """
    logger.info(f"Starting find_parcels_near_gpz operation", extra={
        'operation': 'find_parcels_near_gpz',
        'radius_meters': radius_meters
    })

    parcels_table = "parcels_low"
    gpz_table = "gpz_110kv"

    # This SQL query uses a subquery with ST_DWithin for efficient spatial filtering.
    # It finds all parcels where the distance to any GPZ is within the specified radius.
    # NOTE: This assumes both layers are in the same CRS in the database.
    # If not, a transform would be needed, but ST_DWithin is much faster on projected CRS.
    sql = f"""
        SELECT p.*, ST_Area(p.geometry) as area_sqm
        FROM "{parcels_table}" p
        WHERE EXISTS (
            SELECT 1
            FROM "{gpz_table}" g
            WHERE ST_DWithin(p.geometry, g.geom, {radius_meters})
        );
    """

    try:
        gdf = gpd.read_postgis(sql, db_engine, geom_col='geometry')
        if gdf.empty:
            logger.info(f"No parcels found within {radius_meters}m of a GPZ, returning empty GeoJSON.", extra={
            'operation': 'find_parcels_near_gpz',
            'radius_meters': radius_meters,
            'found_count': 0
        })
            return '{"type": "FeatureCollection", "features": []}'

        logger.info(f"Found {len(gdf)} parcels within {radius_meters}m of a GPZ.", extra={
            'operation': 'find_parcels_near_gpz',
            'radius_meters': radius_meters,
            'found_count': len(gdf)
        })

        gdf_reprojected = gdf.to_crs(epsg=4326)

        # Limit results for display
        limited_gdf, summary = limit_results_for_display(gdf_reprojected, max_display=5, item_type="działka")

        messages = []
        for index, row in limited_gdf.iterrows():
            parcel_id = row.get('ID_DZIALKI', 'Brak ID')
            area_sqm = row['area_sqm']
            messages.append(create_parcel_message(parcel_id, area_sqm, "standard"))

        # Add summary message if there are more results
        if summary:
            messages.append(summary)

        limited_gdf['message'] = messages

        return limited_gdf.to_json()
    except Exception as e:
        logger.error(f"Error in find_parcels_near_gpz tool: {e}", exc_info=True)
        # Re-raise the exception to be handled by the agent/caller,
        # which should result in a proper JSON error response.
        raise


@tool
def find_parcels_without_buildings(db_engine: Engine) -> str:
    """
    Finds all parcels that do not contain any buildings within their boundaries.
    Uses spatial intersection to identify parcels without buildings.
    Returns parcels as GeoJSON with their ID and area information.
    """
    logger.info("Starting find_parcels_without_buildings operation", extra={
        'operation': 'find_parcels_without_buildings'
    })
    
    parcels_table = "parcels_low"
    buildings_table = "buildings_low"
    
    # SQL query to find parcels that don't intersect with any buildings
    sql = f"""
        SELECT p.*, ST_Area(p.geometry) as area_sqm
        FROM "{parcels_table}" p
        WHERE NOT EXISTS (
            SELECT 1
            FROM "{buildings_table}" b
            WHERE ST_Intersects(p.geometry, b.geometry)
        );
    """
    
    try:
        with log_database_operation("find_parcels_without_buildings", table=parcels_table):
            gdf = gpd.read_postgis(sql, db_engine, geom_col='geometry')
            
        if gdf.empty:
            logger.info("No parcels without buildings found, returning empty GeoJSON.", extra={
            'operation': 'find_parcels_without_buildings',
            'found_count': 0
        })
            return '{"type": "FeatureCollection", "features": []}'
            
        logger.info(f"Found {len(gdf)} parcels without buildings", extra={
            'operation': 'find_parcels_without_buildings',
            'found_count': len(gdf)
        })
        
        try:
            gdf_reprojected = gdf.to_crs(epsg=4326)
            
            # Limit results for display
            limited_gdf, summary = limit_results_for_display(gdf_reprojected, max_display=5, item_type="działka")
            
            messages = []
            for index, row in limited_gdf.iterrows():
                parcel_id = row.get('ID_DZIALKI', 'Brak ID')
                area_sqm = row['area_sqm']
                messages.append(create_parcel_message(parcel_id, area_sqm, "unbuilt"))
            
            # Add summary message if there are more results
            if summary:
                messages.append(summary)
            
            limited_gdf['message'] = messages
            
            return limited_gdf.to_json()
            
        except Exception as e:
            raise GISDataProcessingError(
                operation="coordinate transformation and GeoJSON conversion for parcels without buildings",
                original_error=e
            )
            
    except (GISDataProcessingError, DatabaseConnectionError):
        raise
    except Exception as e:
        raise SpatialQueryError(
            operation="finding parcels without buildings",
            original_error=e
        )


@tool
def export_results_to_pdf(geojson_data: str, report_title: str = "Raport GIS") -> str:
    """
    Exports GIS query results to a PDF file.
    Creates a PDF report with a list of parcels, their IDs, and areas.
    Returns the path to the generated PDF file.
    """
    import json
    import tempfile
    from datetime import datetime
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    
    logger.info(f"Starting export_results_to_pdf operation", extra={
        'operation': 'export_results_to_pdf',
        'report_title': report_title
    })
    
    try:
        # Parse GeoJSON data
        geojson = json.loads(geojson_data)
        features = geojson.get('features', [])
        
        if not features:
            logger.warning("No features found in GeoJSON data for PDF export", extra={
            'operation': 'export_results_to_pdf',
            'report_title': report_title,
            'feature_count': 0
        })
            return "Brak danych do eksportu - nie znaleziono żadnych obiektów."
        
        # Create temporary PDF file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        pdf_path = temp_file.name
        temp_file.close()
        
        # Create PDF document
        doc = SimpleDocTemplate(pdf_path, pagesize=A4)
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=20
        )
        
        # Build PDF content
        story = []
        
        # Title
        story.append(Paragraph(report_title, title_style))
        story.append(Paragraph(f"Data wygenerowania: {datetime.now().strftime('%d.%m.%Y %H:%M')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Summary
        story.append(Paragraph(f"Podsumowanie", subtitle_style))
        story.append(Paragraph(f"Liczba znalezionych obiektów: {len(features)}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Table data
        table_data = [['Lp.', 'ID Działki', 'Powierzchnia (ha)', 'Informacje']]
        
        for idx, feature in enumerate(features, 1):
            properties = feature.get('properties', {})
            
            # Extract parcel ID
            parcel_id = properties.get('ID_DZIALKI', properties.get('id', 'Brak ID'))
            
            # Extract area
            area_sqm = properties.get('area_sqm', 0)
            area_ha = area_sqm / 10000 if area_sqm else 0
            area_str = f"{area_ha:.4f}" if area_ha > 0 else "Brak danych"
            
            # Extract message or create default
            message = properties.get('message', 'Działka')
            if isinstance(message, list) and message:
                message = message[0] if len(message) > 0 else 'Działka'
            
            table_data.append([
                str(idx),
                str(parcel_id),
                area_str,
                str(message)[:50] + "..." if len(str(message)) > 50 else str(message)
            ])
        
        # Create table
        table = Table(table_data, colWidths=[1*cm, 3*cm, 2.5*cm, 8*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        story.append(Paragraph("Lista działek", subtitle_style))
        story.append(table)
        
        # Add footer
        story.append(Spacer(1, 30))
        story.append(Paragraph("Raport wygenerowany przez Geo-Asystent AI", styles['Normal']))
        
        # Build PDF
        doc.build(story)
        
        logger.info(f"PDF report generated successfully: {pdf_path}", extra={
            'operation': 'export_results_to_pdf',
            'report_title': report_title,
            'pdf_path': pdf_path,
            'feature_count': len(features)
        })
        return f"Raport PDF został wygenerowany pomyślnie. Zawiera {len(features)} obiektów. Plik zapisany jako: {pdf_path}"
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid GeoJSON data for PDF export: {e}", extra={
            'operation': 'export_results_to_pdf',
            'report_title': report_title,
            'error_type': 'JSONDecodeError'
        })
        return "Błąd: Nieprawidłowe dane GeoJSON do eksportu."
    except Exception as e:
        logger.error(f"Error generating PDF report: {e}", extra={
            'operation': 'export_results_to_pdf',
            'report_title': report_title,
            'error_type': type(e).__name__
        })
        return f"Błąd podczas generowania raportu PDF: {str(e)}"
