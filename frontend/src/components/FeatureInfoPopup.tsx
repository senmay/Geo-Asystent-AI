import React from 'react';
import { Popup } from 'react-leaflet';
import type { LatLng } from 'leaflet';

export interface FeatureInfoPopupProps {
  position: LatLng;
  data: any;
  layerName: string;
  onClose: () => void;
}

const FeatureInfoPopup: React.FC<FeatureInfoPopupProps> = ({
  position,
  data,
  layerName,
  onClose
}) => {
  const formatValue = (value: any): string => {
    if (value === null || value === undefined) return 'brak danych';
    if (typeof value === 'boolean') return value ? 'tak' : 'nie';
    if (typeof value === 'number') return value.toLocaleString('pl-PL');
    return String(value);
  };

  const formatKey = (key: string): string => {
    // Common Polish translations for typical GIS attributes
    const translations: { [key: string]: string } = {
      'id': 'ID',
      'name': 'Nazwa',
      'area': 'Powierzchnia',
      'length': 'Długość',
      'type': 'Typ',
      'status': 'Status',
      'owner': 'Właściciel',
      'address': 'Adres',
      'geometry': 'Geometria',
      'created': 'Utworzono',
      'modified': 'Zmodyfikowano'
    };

    return translations[key.toLowerCase()] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const parseTextResponse = (text: string) => {
    // Parse text response in the format from obiekt.txt
    const lines = text.split('\n').filter(line => line.trim() !== '');
    const properties: any = {};
    
    lines.forEach(line => {
      const parts = line.split('\t');
      if (parts.length >= 2) {
        const key = parts[0].replace(':', '').trim();
        const value = parts[1].trim();
        if (key && value) {
          properties[key] = value;
        }
      }
    });
    
    return Object.keys(properties).length > 0 ? { features: [{ properties }] } : null;
  };

  const parseXMLResponse = (xmlText: string) => {
    try {
      const parser = new DOMParser();
      const xmlDoc = parser.parseFromString(xmlText, 'text/xml');

      // Check for parsing errors
      const parseError = xmlDoc.querySelector('parsererror');
      if (parseError) {
        return null;
      }

      const features: any[] = [];

      // Look for gml:featureMember elements (GUGIK format)
      const featureMembers = xmlDoc.querySelectorAll('gml\\:featureMember, featureMember');
      
      if (featureMembers.length > 0) {
        featureMembers.forEach((featureMember) => {
          const properties: any = {};
          
          // Look for Attribute elements with Name attribute
          const attributes = featureMember.querySelectorAll('Attribute[Name]');
          
          // Define the attributes we want to extract
          const wantedAttributes = [
            'Identyfikator działki',
            'Województwo', 
            'Powiat',
            'Gmina',
            'Obręb',
            'Numer działki',
            'Pole pow. w ewidencji gruntów (ha)'
          ];
          
          attributes.forEach((attr) => {
            const name = attr.getAttribute('Name');
            const value = attr.textContent?.trim();
            
            // Only include wanted attributes
            if (name && value && wantedAttributes.includes(name)) {
              properties[name] = value;
            }
          });

          if (Object.keys(properties).length > 0) {
            features.push({ properties });
          }
        });
      }

      return features.length > 0 ? { features } : null;
    } catch (error) {
      return null;
    }
  };

  const renderFeatureInfo = () => {
    if (!data) return (
      <div style={{ padding: '10px', textAlign: 'center', color: '#666' }}>
        Brak danych
      </div>
    );

    // Handle different response formats
    if (typeof data === 'string' || data.text) {
      const text = data.text || data;

      if (text.toLowerCase().includes('no features') || text.trim() === '') {
        return (
          <div style={{ padding: '10px', textAlign: 'center', color: '#666' }}>
            Brak obiektów w tym miejscu
          </div>
        );
      }

      // Try to parse as tab-separated text first (like obiekt.txt format)
      const parsedText = parseTextResponse(text);
      if (parsedText && parsedText.features.length > 0) {
        return (
          <div style={{ maxWidth: '400px', maxHeight: '350px', overflow: 'auto' }}>
            {parsedText.features.map((feature: any, featureIndex: number) => (
              <div key={featureIndex} style={{
                marginBottom: featureIndex < parsedText.features.length - 1 ? '15px' : '0',
                padding: '12px',
                backgroundColor: '#f8f9fa',
                borderRadius: '6px',
                border: '1px solid #e9ecef'
              }}>
                <div style={{
                  fontSize: '14px',
                  fontWeight: '600',
                  color: '#495057',
                  marginBottom: '8px',
                  borderBottom: '1px solid #dee2e6',
                  paddingBottom: '4px'
                }}>
                  Informacje o obiekcie
                </div>
                <div style={{ display: 'grid', gap: '6px' }}>
                  {Object.entries(feature.properties)
                    .filter(([_, value]) => value !== null && value !== undefined && value !== '')
                    .map(([key, value]) => (
                      <div key={key} style={{
                        display: 'grid',
                        gridTemplateColumns: '1fr 2fr',
                        gap: '8px',
                        fontSize: '13px',
                        alignItems: 'start'
                      }}>
                        <span style={{
                          fontWeight: '500',
                          color: '#6c757d',
                          textAlign: 'right'
                        }}>
                          {key}:
                        </span>
                        <span style={{ color: '#212529' }}>
                          {formatValue(value)}
                        </span>
                      </div>
                    ))}
                </div>
              </div>
            ))}
          </div>
        );
      }

      // Try to parse as XML if text parsing failed
      const parsedXML = parseXMLResponse(text);
      if (parsedXML && parsedXML.features.length > 0) {
        return (
          <div style={{ maxWidth: '400px', maxHeight: '350px', overflow: 'auto' }}>
            {parsedXML.features.map((feature: any, index: number) => (
              <div key={index} style={{
                marginBottom: index < parsedXML.features.length - 1 ? '15px' : '0',
                padding: '12px',
                backgroundColor: '#f8f9fa',
                borderRadius: '6px',
                border: '1px solid #e9ecef'
              }}>
                <div style={{
                  fontSize: '14px',
                  fontWeight: '600',
                  color: '#495057',
                  marginBottom: '8px',
                  borderBottom: '1px solid #dee2e6',
                  paddingBottom: '4px'
                }}>
                  Obiekt {index + 1}
                </div>
                <div style={{ display: 'grid', gap: '4px' }}>
                  {Object.entries(feature.properties)
                    .filter(([_, value]) => value !== null && value !== undefined && value !== '')
                    .map(([key, value]) => (
                      <div key={key} style={{
                        display: 'grid',
                        gridTemplateColumns: '1fr 2fr',
                        gap: '8px',
                        fontSize: '13px',
                        alignItems: 'start'
                      }}>
                        <span style={{
                          fontWeight: '500',
                          color: '#6c757d',
                          textAlign: 'right'
                        }}>
                          {formatKey(key)}:
                        </span>
                        <span style={{ color: '#212529' }}>
                          {formatValue(value)}
                        </span>
                      </div>
                    ))}
                </div>
              </div>
            ))}
          </div>
        );
      }

      // Fallback to formatted text display
      return (
        <div style={{
          maxWidth: '350px',
          maxHeight: '300px',
          overflow: 'auto',
          padding: '12px',
          backgroundColor: '#f8f9fa',
          borderRadius: '6px',
          border: '1px solid #e9ecef'
        }}>
          <div style={{
            fontSize: '13px',
            lineHeight: '1.4',
            color: '#212529',
            whiteSpace: 'pre-wrap',
            fontFamily: 'inherit'
          }}>
            {text}
          </div>
        </div>
      );
    }

    // Handle GeoJSON-like responses
    if (data.features && Array.isArray(data.features)) {
      if (data.features.length === 0) {
        return (
          <div style={{ padding: '10px', textAlign: 'center', color: '#666' }}>
            Brak obiektów w tym miejscu
          </div>
        );
      }

      return (
        <div style={{ maxWidth: '400px', maxHeight: '350px', overflow: 'auto' }}>
          {data.features.map((feature: any, index: number) => (
            <div key={index} style={{
              marginBottom: index < data.features.length - 1 ? '15px' : '0',
              padding: '12px',
              backgroundColor: '#f8f9fa',
              borderRadius: '6px',
              border: '1px solid #e9ecef'
            }}>
              <div style={{
                fontSize: '14px',
                fontWeight: '600',
                color: '#495057',
                marginBottom: '8px',
                borderBottom: '1px solid #dee2e6',
                paddingBottom: '4px'
              }}>
                Obiekt {index + 1}
              </div>
              {feature.properties && Object.keys(feature.properties).length > 0 ? (
                <div style={{ display: 'grid', gap: '4px' }}>
                  {Object.entries(feature.properties)
                    .filter(([_, value]) => value !== null && value !== undefined && value !== '')
                    .map(([key, value]) => (
                      <div key={key} style={{
                        display: 'grid',
                        gridTemplateColumns: '1fr 2fr',
                        gap: '8px',
                        fontSize: '13px',
                        alignItems: 'start'
                      }}>
                        <span style={{
                          fontWeight: '500',
                          color: '#6c757d',
                          textAlign: 'right'
                        }}>
                          {formatKey(key)}:
                        </span>
                        <span style={{ color: '#212529' }}>
                          {formatValue(value)}
                        </span>
                      </div>
                    ))}
                </div>
              ) : (
                <div style={{ fontSize: '12px', color: '#6c757d', fontStyle: 'italic' }}>
                  Brak dostępnych atrybutów
                </div>
              )}
            </div>
          ))}
        </div>
      );
    }

    // Handle object responses
    if (typeof data === 'object') {
      const entries = Object.entries(data).filter(([_, value]) =>
        value !== null && value !== undefined && value !== ''
      );

      if (entries.length === 0) {
        return (
          <div style={{ padding: '10px', textAlign: 'center', color: '#666' }}>
            Brak dostępnych danych
          </div>
        );
      }

      return (
        <div style={{
          maxWidth: '350px',
          maxHeight: '300px',
          overflow: 'auto',
          padding: '12px'
        }}>
          <div style={{ display: 'grid', gap: '6px' }}>
            {entries.map(([key, value]) => (
              <div key={key} style={{
                display: 'grid',
                gridTemplateColumns: '1fr 2fr',
                gap: '8px',
                fontSize: '13px',
                alignItems: 'start',
                paddingBottom: '4px',
                borderBottom: '1px solid #f0f0f0'
              }}>
                <span style={{
                  fontWeight: '500',
                  color: '#6c757d',
                  textAlign: 'right'
                }}>
                  {formatKey(key)}:
                </span>
                <span style={{ color: '#212529' }}>
                  {formatValue(value)}
                </span>
              </div>
            ))}
          </div>
        </div>
      );
    }

    return (
      <div style={{ padding: '10px', textAlign: 'center', color: '#666' }}>
        Nieznany format danych
      </div>
    );
  };

  return (
    <Popup
      position={position}
      closeButton={true}
      autoClose={false}
      closeOnClick={false}
      eventHandlers={{
        remove: onClose
      }}
    >
      <div>
        <h4 style={{ margin: '0 0 10px 0', fontSize: '14px', color: '#333' }}>
          {layerName}
        </h4>
        {renderFeatureInfo()}
      </div>
    </Popup>
  );
};

export default FeatureInfoPopup;