import React from 'react';
import './App.css';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type GeoJsonObject = any;

export interface LayerState {
  id: number;
  name: string;
  data: GeoJsonObject;
  visible: boolean;
}

interface LayerControlProps {
  layers: LayerState[];
  onToggleLayer: (id: number) => void;
}

const LayerControl: React.FC<LayerControlProps> = ({ layers, onToggleLayer }) => {
  if (layers.length === 0) {
    return null;
  }

  return (
    <div className="layer-control">
      <h4>Warstwy</h4>
      {layers.map((layer) => (
        <div key={layer.id} className="layer-item">
          <input
            type="checkbox"
            checked={layer.visible}
            onChange={() => onToggleLayer(layer.id)}
            id={`layer-checkbox-${layer.id}`}
          />
          <label htmlFor={`layer-checkbox-${layer.id}`}>{layer.name}</label>
        </div>
      ))}
    </div>
  );
};

export default LayerControl;