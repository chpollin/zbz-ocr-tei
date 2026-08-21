"""HTML-Report fuer die OCR-Evaluation (aus evaluate_ocr.py ausgegliedert).

Reiner Praesentations-Layer: konsumiert das results-Dict, keine Engine-Logik.
"""

from pathlib import Path


def generate_html_report(results: dict, output_path: Path):
    """Generiert HTML-Report mit visueller Diff-Ansicht."""
    engine_label = results.get('engine', 'OCR').capitalize()
    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OCR Evaluation Report - {engine_label}</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        h1 {{ color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}

        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .summary-card .value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #4CAF50;
        }}
        .summary-card .label {{
            color: #666;
            margin-top: 5px;
        }}
        .summary-card.warning .value {{ color: #FF9800; }}
        .summary-card.error .value {{ color: #f44336; }}

        .document-section {{
            background: white;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .document-header {{
            background: #4CAF50;
            color: white;
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .document-header.warning {{ background: #FF9800; }}
        .document-header.error {{ background: #f44336; }}
        .document-header h3 {{ margin: 0; }}
        .document-header .metrics {{
            display: flex;
            gap: 20px;
        }}
        .document-header .metric {{
            text-align: center;
        }}
        .document-header .metric-value {{
            font-size: 1.5em;
            font-weight: bold;
        }}

        .document-body {{
            padding: 20px;
        }}

        .diff-container {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}
        .diff-panel {{
            border: 1px solid #ddd;
            border-radius: 4px;
            overflow: hidden;
        }}
        .diff-panel-header {{
            background: #f0f0f0;
            padding: 10px 15px;
            font-weight: bold;
            border-bottom: 1px solid #ddd;
        }}
        .diff-panel-content {{
            padding: 15px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 13px;
            line-height: 1.6;
            white-space: pre-wrap;
            word-wrap: break-word;
            max-height: 400px;
            overflow-y: auto;
            background: #fafafa;
        }}

        .errors-list {{
            margin-top: 15px;
        }}
        .error-item {{
            background: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 4px;
            padding: 10px 15px;
            margin: 10px 0;
        }}
        .error-item .type {{
            font-weight: bold;
            color: #856404;
            text-transform: uppercase;
            font-size: 0.8em;
        }}
        .error-item .content {{
            margin-top: 5px;
            font-family: monospace;
        }}
        .error-item .ref {{ color: #d32f2f; text-decoration: line-through; }}
        .error-item .hyp {{ color: #388e3c; }}
        .error-item .context {{
            margin-top: 5px;
            font-size: 0.9em;
            color: #666;
        }}

        .toggle-btn {{
            background: #e0e0e0;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            margin-right: 10px;
        }}
        .toggle-btn:hover {{ background: #d0d0d0; }}

        .collapsible {{ display: none; }}
        .collapsible.show {{ display: block; }}

        .timestamp {{
            color: #999;
            font-size: 0.9em;
            margin-top: 30px;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>OCR Evaluation Report - {engine_label}</h1>
        <p>Vergleich von {engine_label}-Output mit Referenz-TEI-Dateien</p>

        <h2>Zusammenfassung</h2>
        <div class="summary-grid">
            <div class="summary-card">
                <div class="value">{results['summary']['total_documents']}</div>
                <div class="label">Dokumente</div>
            </div>
            <div class="summary-card {'warning' if results['summary']['avg_cer'] > 0.05 else ''}">
                <div class="value">{results['summary']['avg_cer']*100:.2f}%</div>
                <div class="label">Durchschn. CER</div>
            </div>
            <div class="summary-card">
                <div class="value">{results['summary']['avg_wer']*100:.2f}%</div>
                <div class="label">Durchschn. WER</div>
            </div>
            <div class="summary-card">
                <div class="value">{(1-results['summary']['avg_cer'])*100:.2f}%</div>
                <div class="label">Genauigkeit</div>
            </div>
        </div>
"""

    # Dokument-Details
    html += "<h2>Dokument-Details</h2>"

    for doc_id, doc_data in results['documents'].items():
        cer = doc_data.get('cer', 0)
        header_class = 'error' if cer > 0.1 else 'warning' if cer > 0.02 else ''

        html += f"""
        <div class="document-section">
            <div class="document-header {header_class}">
                <h3>{doc_id}</h3>
                <div class="metrics">
                    <div class="metric">
                        <div class="metric-value">{cer*100:.2f}%</div>
                        <div>CER</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{doc_data.get('wer', 0)*100:.2f}%</div>
                        <div>WER</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{doc_data.get('ref_chars', 0)}</div>
                        <div>Zeichen (aligned)</div>
                    </div>
                </div>
            </div>
            <div class="document-body">
                <button class="toggle-btn" onclick="toggleSection('{doc_id}-diff')">Textvergleich anzeigen</button>
                <button class="toggle-btn" onclick="toggleSection('{doc_id}-errors')">Fehler anzeigen ({len(doc_data.get('differences', []))})</button>

                <div id="{doc_id}-diff" class="collapsible">
                    <div class="diff-container">
                        <div class="diff-panel">
                            <div class="diff-panel-header">Referenz (TEI)</div>
                            <div class="diff-panel-content">{doc_data.get('reference_text', '')[:2000]}{'...' if len(doc_data.get('reference_text', '')) > 2000 else ''}</div>
                        </div>
                        <div class="diff-panel">
                            <div class="diff-panel-header">OCR-Output</div>
                            <div class="diff-panel-content">{doc_data.get('ocr_text', '')[:2000]}{'...' if len(doc_data.get('ocr_text', '')) > 2000 else ''}</div>
                        </div>
                    </div>
                </div>

                <div id="{doc_id}-errors" class="collapsible errors-list">
"""

        # Fehler auflisten (max 20)
        for diff in doc_data.get('differences', [])[:20]:
            ref_text = diff.get('reference', '').replace('<', '&lt;').replace('>', '&gt;')
            hyp_text = diff.get('hypothesis', '').replace('<', '&lt;').replace('>', '&gt;')
            context = diff.get('context', '').replace('<', '&lt;').replace('>', '&gt;')

            html += f"""
                    <div class="error-item">
                        <div class="type">{diff.get('type', 'unknown')}</div>
                        <div class="content">
                            <span class="ref">{ref_text if ref_text else '(leer)'}</span>
                            &rarr;
                            <span class="hyp">{hyp_text if hyp_text else '(leer)'}</span>
                        </div>
                        <div class="context">Kontext: ...{context}...</div>
                    </div>
"""

        if len(doc_data.get('differences', [])) > 20:
            html += f'<p>... und {len(doc_data["differences"]) - 20} weitere Unterschiede</p>'

        html += """
                </div>
            </div>
        </div>
"""

    # Footer
    html += f"""
        <div class="timestamp">
            Generiert am {results['timestamp']}
        </div>
    </div>

    <script>
        function toggleSection(id) {{
            const elem = document.getElementById(id);
            elem.classList.toggle('show');
        }}
    </script>
</body>
</html>
"""

    output_path.write_text(html, encoding='utf-8')
    print(f"HTML-Report gespeichert: {output_path}")
