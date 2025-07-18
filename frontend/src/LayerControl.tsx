import React, { useState } from 'react';
import './App.css';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type GeoJsonObject = any;

export interface LayerState {
  id: number;
  name: string;
  data: GeoJsonObject;
  visible: boolean;
  color?: string; // Optional color for the layer representation
}

interface LayerControlProps {
  layers: LayerState[];
  onToggleLayer: (id: number) => void;
}

const LayerControl: React.FC<LayerControlProps> = ({ layers, onToggleLayer }) => {
  const [isOpen, setIsOpen] = useState(true); // State for collapsible panel

  if (layers.length === 0) {
    return null;
  }

  return (
    <div className="layer-control">
      <h4 className="layer-control-header" onClick={() => setIsOpen(!isOpen)}>
        Warstwy
        <span className="toggle-icon">{isOpen ? '▼' : '►'}</span>
      </h4>
      {isOpen && (
        <div className="layer-list">
          {layers.map((layer) => (
            <div key={layer.id} className="layer-item">
              <input
                type="checkbox"
                checked={layer.visible}
                onChange={() => onToggleLayer(layer.id)}
                id={`layer-checkbox-${layer.id}`}
              />
              <label htmlFor={`layer-checkbox-${layer.id}`}>
                {layer.color && (
                  <span
                    className="color-swatch"
                    style={{ backgroundColor: layer.color }}
                  ></span>
                )}
                {layer.name}
              </label>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default LayerControl;