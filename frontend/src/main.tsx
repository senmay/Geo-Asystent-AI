import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'
import 'leaflet/dist/leaflet.css'; // Main leaflet CSS
import 'leaflet.markercluster/dist/MarkerCluster.css'; // Default cluster theme
import 'leaflet.markercluster/dist/MarkerCluster.Default.css'; // Default cluster theme

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
