function exportToPDF() {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();

    // Título
    doc.setFontSize(18);
    doc.text('Dashboard Clash Royale', 14, 22);

    // Nome do Clã e Data
    const clanName = document.querySelector('.main-header h1').textContent;
    const clanTag = document.querySelector('.clan-tag').textContent;
    doc.setFontSize(12);
    doc.text(`${clanName} - ${clanTag}`, 14, 30);
    doc.text(`Gerado em: ${new Date().toLocaleString('pt-BR')}`, 14, 36);

    // Capturar tabela
    const table = document.querySelector('table');

    if (table) {
        doc.autoTable({
            html: table,
            startY: 45,
            theme: 'grid',
            headStyles: {
                fillColor: [15, 52, 96], // --primary color
                textColor: [255, 255, 255],
                fontStyle: 'bold'
            },
            styles: {
                fontSize: 9,
                cellPadding: 3
            },
            columnStyles: {
                0: { cellWidth: 15 },
                3: { cellWidth: 25 },
                4: { cellWidth: 25 }
            }
        });
    }

    // Salvar PDF
    const fileName = `clash_royale_${clanTag.replace('#', '')}_${new Date().getTime()}.pdf`;
    doc.save(fileName);
}
