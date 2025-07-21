-- Tabela konfiguracji warstw GIS z stylowaniem
-- Eliminuje potrzebę modyfikacji kodu przy dodawaniu nowych warstw

CREATE TABLE IF NOT EXISTS layer_config (
    id SERIAL PRIMARY KEY,
    layer_name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    geometry_column VARCHAR(50) DEFAULT 'geometry',
    id_column VARCHAR(50) DEFAULT 'id',
    description TEXT,
    
    -- Stylowanie dla różnych typów geometrii
    point_color VARCHAR(20) DEFAULT '#ff7800',
    point_radius INTEGER DEFAULT 6,
    point_opacity DECIMAL(3,2) DEFAULT 0.8,
    point_fill_opacity DECIMAL(3,2) DEFAULT 0.8,
    
    line_color VARCHAR(20) DEFAULT '#3388ff',
    line_weight INTEGER DEFAULT 3,
    line_opacity DECIMAL(3,2) DEFAULT 0.7,
    line_dash_array VARCHAR(50),
    
    polygon_color VARCHAR(20) DEFAULT '#3388ff',
    polygon_weight INTEGER DEFAULT 2,
    polygon_opacity DECIMAL(3,2) DEFAULT 0.7,
    polygon_fill_color VARCHAR(20),
    polygon_fill_opacity DECIMAL(3,2) DEFAULT 0.2,
    
    -- Konfiguracja warstwy
    has_low_resolution BOOLEAN DEFAULT true,
    default_visible BOOLEAN DEFAULT false,
    min_zoom INTEGER DEFAULT 0,
    max_zoom INTEGER DEFAULT 20,
    cluster_points BOOLEAN DEFAULT true,
    
    -- Metadane
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    active BOOLEAN DEFAULT true
);

-- Indeksy dla wydajności
CREATE INDEX IF NOT EXISTS idx_layer_config_name ON layer_config(layer_name);
CREATE INDEX IF NOT EXISTS idx_layer_config_active ON layer_config(active);

-- Trigger do automatycznego update timestamp
CREATE OR REPLACE FUNCTION update_layer_config_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_layer_config_timestamp
    BEFORE UPDATE ON layer_config
    FOR EACH ROW
    EXECUTE FUNCTION update_layer_config_timestamp();

-- Wstaw domyślne konfiguracje warstw
INSERT INTO layer_config (
    layer_name, display_name, table_name, geometry_column, id_column,
    description, point_color, point_radius, line_color, polygon_color,
    polygon_fill_color, default_visible, cluster_points
) VALUES 
-- Warstwy punktowe
('gpz_POLSKA', 'GPZ 110kV', 'gpz_110kv', 'geom', 'id',
 'Stacje elektroenergetyczne 110kV', '#ff0000', 8, '#ff0000', '#ff0000',
 '#ff0000', true, true),

('gpz_WIELKOPOLSKIE', 'GPZ Wielkopolskie', 'GPZ_WIELKOPOLSKIE', 'geom', 'id',
 'Stacje elektroenergetyczne w województwie wielkopolskim', '#ff00ff', 8, '#ff00ff', '#ff00ff',
 '#ff00ff', false, true),

-- Warstwy poligonowe
('parcels', 'Działki przykładowe', 'parcels', 'geometry', 'ID_DZIALKI',
 'Działki ewidencyjne z informacjami o powierzchni', '#00ff00', 6, '#00ff00', '#00ff00',
 '#00ff00', true, false),

('buildings', 'Budynki przykładowe', 'buildings', 'geometry', 'ID_BUDYNKU',
 'Kontury budynków', '#3388ff', 6, '#3388ff', '#3388ff',
 '#3388ff', true, false),

('wojewodztwa', 'Województwa', 'Wojewodztwa', 'geom', 'JPT_NAZWA_',
 'Granice województw', '#800080', 6, '#800080', '#800080',
 '#800080', false, false),

('natura2000', 'Natura 2000', 'natura 2000', 'geom', 'id',
 'Obszary chronione Natura 2000', '#008000', 6, '#008000', '#008000',
 '#008000', false, false)

ON CONFLICT (layer_name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    point_color = EXCLUDED.point_color,
    point_radius = EXCLUDED.point_radius,
    line_color = EXCLUDED.line_color,
    polygon_color = EXCLUDED.polygon_color,
    polygon_fill_color = EXCLUDED.polygon_fill_color,
    default_visible = EXCLUDED.default_visible,
    cluster_points = EXCLUDED.cluster_points,
    updated_at = CURRENT_TIMESTAMP;