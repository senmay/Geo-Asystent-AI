import React from 'react';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import type { GeoJsonFeatureCollection } from '../services/api/types';
import 'leaflet.browser.print/dist/leaflet.browser.print.min.js';


// Import font for Polish characters support
import 'jspdf/dist/polyfills.es.js';

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

      const doc = new jsPDF({
        orientation: 'portrait',
        unit: 'mm',
        format: 'a4',
        putOnlyUsedFonts: true,
        compress: true
      });
      
      // Configure for Polish characters support
      doc.setFont('helvetica');
      
      // Helper function to handle Polish characters
      const encodeText = (text: string): string => {
        return text
          .replace(/ą/g, 'a')
          .replace(/ć/g, 'c')
          .replace(/ę/g, 'e')
          .replace(/ł/g, 'l')
          .replace(/ń/g, 'n')
          .replace(/ó/g, 'o')
          .replace(/ś/g, 's')
          .replace(/ź/g, 'z')
          .replace(/ż/g, 'z')
          .replace(/Ą/g, 'A')
          .replace(/Ć/g, 'C')
          .replace(/Ę/g, 'E')
          .replace(/Ł/g, 'L')
          .replace(/Ń/g, 'N')
          .replace(/Ó/g, 'O')
          .replace(/Ś/g, 'S')
          .replace(/Ź/g, 'Z')
          .replace(/Ż/g, 'Z');
      };
      
      const pageWidth = doc.internal.pageSize.getWidth();
      const margin = 20;
      let yPosition = margin;

      doc.setFont('helvetica', 'bold');
      doc.setFontSize(18);
      doc.text(encodeText(reportTitle), pageWidth / 2, yPosition, { align: 'center' });
      yPosition += 15;

      doc.setFont('helvetica', 'normal');
      doc.setFontSize(10);
      const currentDate = new Date().toLocaleDateString('pl-PL', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
      doc.text(encodeText(`Data wygenerowania: ${currentDate}`), pageWidth / 2, yPosition, { align: 'center' });
      yPosition += 20;

      doc.setFont('helvetica', 'bold');
      doc.setFontSize(14);
      doc.text(encodeText('Podsumowanie'), pageWidth / 2, yPosition, { align: 'center' });
      yPosition += 10;

      doc.setFont('helvetica', 'normal');
      doc.setFontSize(11);
      doc.text(encodeText(`Liczba znalezionych obiektów: ${data.features.length}`), pageWidth / 2, yPosition, { align: 'center' });
      yPosition += 20;

      doc.setFont('helvetica', 'bold');
      doc.setFontSize(13);
      doc.text(encodeText('Lista działek'), pageWidth / 2, yPosition, { align: 'center' });
      yPosition += 15;

      const colW = [20, 90, 50];
      const totalTableWidth = colW.reduce((a, b) => a + b, 0);
      const tableStartX = (pageWidth - totalTableWidth) / 2;
      const colX = [
        tableStartX,
        tableStartX + colW[0],
        tableStartX + colW[0] + colW[1]
      ];
      const colC = colX.map((x, i) => x + colW[i] / 2);
      const rowHeight = 8;

      doc.setFontSize(10);
      doc.setDrawColor(150);
      doc.setFillColor('gray');
      doc.setFont('helvetica', 'bold');

      for (let i = 0; i < colW.length; i++) {
        doc.rect(colX[i], yPosition, colW[i], rowHeight);
      }

      doc.text(encodeText('Lp.'), colX[0] + colW[0] / 2, yPosition + 5, { align: 'center' });
      doc.text(encodeText('ID Działki'), colX[1] + colW[1] / 2, yPosition + 5, { align: 'center' });
      doc.text(encodeText('Powierzchnia (ha)'), colX[2] + colW[2] / 2, yPosition + 5, { align: 'center' });

      yPosition += rowHeight;
      doc.setFont('helvetica', 'normal');

      data.features.forEach((feature, index) => {
        if (yPosition + rowHeight > 270) {
          doc.addPage();
          yPosition = margin;
        }

        const props = feature.properties || {};
        const parcelId = props.ID_DZIALKI || props.id || 'Brak ID';
        const areaHa = props.area_sqm ? (props.area_sqm / 10000).toFixed(4) : 'Brak danych';

        for (let i = 0; i < colW.length; i++) {
          doc.rect(colX[i], yPosition, colW[i], rowHeight);
        }

        doc.text(`${index + 1}`, colX[0] + colW[0] / 2, yPosition + 5, { align: 'center' });
        doc.text(encodeText(String(parcelId)), colX[1] + colW[1] / 2, yPosition + 5, { align: 'center' });
        doc.text(encodeText(areaHa), colX[2] + colW[2] / 2, yPosition + 5, { align: 'center' });

        yPosition += rowHeight;
      });

      // Screenshot mapy
      try {
        const mapElement = document.querySelector('.leaflet-container') as HTMLElement;
        if (mapElement) {
          yPosition += 20;

          if (yPosition > 200) {
            doc.addPage();
            yPosition = margin;
          }

          doc.setFontSize(14);
          doc.setFont('helvetica', 'bold');
          doc.text(encodeText('Zrzut ekranu z mapy glownej'), pageWidth / 2, yPosition, { align: 'center' });
          yPosition += 10;

          const canvas = await html2canvas(mapElement, {
            useCORS: true,
            allowTaint: true,
            scale: 0.8,
            width: mapElement.offsetWidth,
            height: Math.min(mapElement.offsetHeight, 800)
          });

          const imgData = canvas.toDataURL('image/png');
          const imgWidth = pageWidth - 2 * margin;
          const imgHeight = (canvas.height * imgWidth) / canvas.width;

          if (yPosition + imgHeight > 280) {
            doc.addPage();
            yPosition = margin;
          }         

          doc.addImage(imgData, 'PNG', margin, yPosition, imgWidth, Math.min(imgHeight, 150));
        }
      } catch (mapError) {
        console.warn('Nie udało się dodać mapy do PDF:', mapError);
      }

      // Stopka
      const totalPages = doc.getNumberOfPages();
      for (let i = 1; i <= totalPages; i++) {
        doc.setPage(i);
        doc.setFontSize(8);
        doc.setFont('helvetica', 'italic');
        doc.text(
          encodeText('Raport wygenerowany przez Geo-Asystent AI'),
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
