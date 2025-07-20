import React from 'react';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import type { GeoJsonFeatureCollection } from '../services/api/types';

export interface PDFExportProps {
  data: GeoJsonFeatureCollection | null;
  reportTitle?: string;
  onExportStart?: () => void;
  onExportComplete?: (success: boolean, message: string) => void;
}

const PDFExport: React.FC<PDFExportProps> = ({
  data,
  reportTitle = "Raport GIS - Geo-Asystent AI",
  onExportStart,
  onExportComplete
}) => {
  const exportToPDF = async () => {
    if (!data || !data.features || data.features.length === 0) {
      onExportComplete?.(false, "Brak danych do eksportu");
      return;
    }

    try {
      onExportStart?.();
      
      const doc = new jsPDF();
      const pageWidth = doc.internal.pageSize.getWidth();
      const margin = 20;
      let yPosition = margin;

      // Dodaj nagłówek
      doc.setFontSize(18);
      doc.setFont('helvetica', 'bold');
      doc.text(reportTitle, margin, yPosition);
      yPosition += 15;

      // Dodaj datę
      doc.setFontSize(10);
      doc.setFont('helvetica', 'normal');
      const currentDate = new Date().toLocaleDateString('pl-PL', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
      doc.text(`Data wygenerowania: ${currentDate}`, margin, yPosition);
      yPosition += 20;

      // Dodaj podsumowanie
      doc.setFontSize(14);
      doc.setFont('helvetica', 'bold');
      doc.text('Podsumowanie', margin, yPosition);
      yPosition += 10;

      doc.setFontSize(11);
      doc.setFont('helvetica', 'normal');
      doc.text(`Liczba znalezionych obiektów: ${data.features.length}`, margin, yPosition);
      yPosition += 20;

      // Dodaj listę działek
      doc.setFontSize(14);
      doc.setFont('helvetica', 'bold');
      doc.text('Lista działek', margin, yPosition);
      yPosition += 15;

      // Nagłówki tabeli
      doc.setFontSize(10);
      doc.setFont('helvetica', 'bold');
      doc.text('Lp.', margin, yPosition);
      doc.text('ID Działki', margin + 20, yPosition);
      doc.text('Powierzchnia (ha)', margin + 80, yPosition);
      doc.text('Informacje', margin + 140, yPosition);
      yPosition += 8;

      // Linia pod nagłówkami
      doc.line(margin, yPosition, pageWidth - margin, yPosition);
      yPosition += 5;

      // Dane działek
      doc.setFont('helvetica', 'normal');
      data.features.forEach((feature, index) => {
        // Sprawdź czy nie przekraczamy strony
        if (yPosition > 270) {
          doc.addPage();
          yPosition = margin;
        }

        const properties = feature.properties || {};
        
        // Wyciągnij dane
        const parcelId = properties.ID_DZIALKI || properties.id || 'Brak ID';
        const areaHa = properties.area_sqm ? (properties.area_sqm / 10000).toFixed(4) : 'Brak danych';
        const message = properties.message || 'Działka';
        
        // Skróć wiadomość jeśli za długa
        const shortMessage = typeof message === 'string' 
          ? (message.length > 30 ? message.substring(0, 30) + '...' : message)
          : String(message).substring(0, 30);

        // Dodaj wiersz
        doc.text(`${index + 1}.`, margin, yPosition);
        doc.text(String(parcelId), margin + 20, yPosition);
        doc.text(areaHa, margin + 80, yPosition);
        doc.text(shortMessage, margin + 140, yPosition);
        
        yPosition += 6;
      });

      // Dodaj screenshot mapy (opcjonalnie)
      try {
        const mapElement = document.querySelector('.leaflet-container') as HTMLElement;
        if (mapElement) {
          yPosition += 20;
          
          // Sprawdź czy mamy miejsce na mapę, jeśli nie - dodaj nową stronę
          if (yPosition > 200) {
            doc.addPage();
            yPosition = margin;
          }

          doc.setFontSize(14);
          doc.setFont('helvetica', 'bold');
          doc.text('Mapa', margin, yPosition);
          yPosition += 10;

          // Zrób screenshot mapy
          const canvas = await html2canvas(mapElement, {
            useCORS: true,
            allowTaint: true,
            scale: 0.5, // Zmniejsz skalę dla lepszej wydajności
            width: mapElement.offsetWidth,
            height: Math.min(mapElement.offsetHeight, 400) // Ogranicz wysokość
          });

          const imgData = canvas.toDataURL('image/png');
          const imgWidth = pageWidth - 2 * margin;
          const imgHeight = (canvas.height * imgWidth) / canvas.width;
          
          // Sprawdź czy obraz zmieści się na stronie
          if (yPosition + imgHeight > 280) {
            doc.addPage();
            yPosition = margin;
          }

          doc.addImage(imgData, 'PNG', margin, yPosition, imgWidth, Math.min(imgHeight, 150));
        }
      } catch (mapError) {
        console.warn('Nie udało się dodać mapy do PDF:', mapError);
      }

      // Dodaj stopkę
      const totalPages = doc.getNumberOfPages();
      for (let i = 1; i <= totalPages; i++) {
        doc.setPage(i);
        doc.setFontSize(8);
        doc.setFont('helvetica', 'italic');
        doc.text(
          'Raport wygenerowany przez Geo-Asystent AI',
          pageWidth / 2,
          doc.internal.pageSize.getHeight() - 10,
          { align: 'center' }
        );
        doc.text(
          `Strona ${i} z ${totalPages}`,
          pageWidth - margin,
          doc.internal.pageSize.getHeight() - 10,
          { align: 'right' }
        );
      }

      // Zapisz PDF
      const fileName = `raport_gis_${new Date().toISOString().split('T')[0]}.pdf`;
      doc.save(fileName);

      onExportComplete?.(true, `Raport PDF został wygenerowany pomyślnie. Zawiera ${data.features.length} obiektów.`);

    } catch (error) {
      console.error('Błąd podczas eksportu PDF:', error);
      onExportComplete?.(false, `Błąd podczas generowania PDF: ${error}`);
    }
  };

  return (
    <button
      onClick={exportToPDF}
      disabled={!data || !data.features || data.features.length === 0}
      style={{
        padding: '4px 8px',
        backgroundColor: data && data.features && data.features.length > 0 ? '#007bff' : '#6c757d',
        color: 'white',
        border: 'none',
        borderRadius: '3px',
        cursor: data && data.features && data.features.length > 0 ? 'pointer' : 'not-allowed',
        fontSize: '11px',
        fontWeight: '500',
        display: 'flex',
        alignItems: 'center',
        gap: '4px',
        transition: 'all 0.2s ease',
        minWidth: '70px',
        height: '24px'
      }}
      onMouseEnter={(e) => {
        if (data && data.features && data.features.length > 0) {
          e.currentTarget.style.backgroundColor = '#0056b3';
        }
      }}
      onMouseLeave={(e) => {
        if (data && data.features && data.features.length > 0) {
          e.currentTarget.style.backgroundColor = '#007bff';
        }
      }}
      title={data && data.features && data.features.length > 0 
        ? `Eksportuj ${data.features.length} obiektów do PDF` 
        : 'Brak danych do eksportu'
      }
    >
      📄 PDF
    </button>
  );
};

export default PDFExport;