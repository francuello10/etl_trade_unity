#!/usr/bin/env python3
"""
Convierte el documento Markdown a HTML con formato para Google Drive
"""

import os
import sys

try:
    import markdown
    from markdown.extensions import tables, fenced_code, codehilite
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False

INPUT_MD = "outputs/TradeUnity Executive Report.md"
OUTPUT_HTML = "outputs/TradeUnity Executive Report.html"

CSS_STYLE = """
<style>
    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        line-height: 1.6;
        color: #333;
        max-width: 1200px;
        margin: 0 auto;
        padding: 20px;
        background-color: #ffffff;
    }
    
    h1 {
        color: #1a73e8;
        border-bottom: 3px solid #1a73e8;
        padding-bottom: 10px;
        margin-top: 30px;
    }
    
    h2 {
        color: #34a853;
        border-bottom: 2px solid #34a853;
        padding-bottom: 8px;
        margin-top: 25px;
    }
    
    h3 {
        color: #ea4335;
        margin-top: 20px;
    }
    
    h4 {
        color: #fbbc04;
        margin-top: 15px;
    }
    
    table {
        border-collapse: collapse;
        width: 100%;
        margin: 20px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    th {
        background-color: #1a73e8;
        color: white;
        padding: 12px;
        text-align: left;
        font-weight: bold;
    }
    
    td {
        padding: 10px;
        border-bottom: 1px solid #ddd;
    }
    
    tr:nth-child(even) {
        background-color: #f8f9fa;
    }
    
    tr:hover {
        background-color: #e8f0fe;
    }
    
    code {
        background-color: #f4f4f4;
        padding: 2px 6px;
        border-radius: 3px;
        font-family: 'Courier New', monospace;
        font-size: 0.9em;
    }
    
    pre {
        background-color: #f4f4f4;
        padding: 15px;
        border-radius: 5px;
        overflow-x: auto;
        border-left: 4px solid #1a73e8;
    }
    
    blockquote {
        border-left: 4px solid #34a853;
        padding-left: 20px;
        margin-left: 0;
        color: #555;
        font-style: italic;
    }
    
    ul, ol {
        margin: 15px 0;
        padding-left: 30px;
    }
    
    li {
        margin: 8px 0;
    }
    
    strong {
        color: #1a73e8;
        font-weight: 600;
    }
    
    em {
        color: #ea4335;
    }
    
    hr {
        border: none;
        border-top: 2px solid #ddd;
        margin: 30px 0;
    }
    
    .highlight {
        background-color: #fff3cd;
        padding: 2px 4px;
        border-radius: 3px;
    }
    
    /* Estilos para emojis y símbolos especiales */
    .emoji {
        font-size: 1.2em;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        body {
            padding: 10px;
        }
        
        table {
            font-size: 0.9em;
        }
        
        th, td {
            padding: 8px;
        }
    }
    
    /* Estilos para secciones especiales */
    .resumen {
        background-color: #e8f5e9;
        padding: 20px;
        border-radius: 5px;
        margin: 20px 0;
        border-left: 5px solid #34a853;
    }
    
    .alerta {
        background-color: #fff3cd;
        padding: 15px;
        border-radius: 5px;
        margin: 20px 0;
        border-left: 5px solid #fbbc04;
    }
    
    .critico {
        background-color: #ffebee;
        padding: 15px;
        border-radius: 5px;
        margin: 20px 0;
        border-left: 5px solid #ea4335;
    }
</style>
"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trade Unity - Análisis Ejecutivo Profundo</title>
    {css}
</head>
<body>
    {content}
</body>
</html>
"""


def convert_md_to_html():
    """Convierte el archivo Markdown a HTML."""
    print("🔄 Convirtiendo Markdown a HTML...")
    
    if not os.path.exists(INPUT_MD):
        print(f"   ❌ Error: No se encuentra el archivo {INPUT_MD}")
        return False
    
    # Leer el archivo Markdown
    print(f"   📖 Leyendo {INPUT_MD}...")
    with open(INPUT_MD, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    if not HAS_MARKDOWN:
        print("   ⚠️  Instalando markdown...")
        import subprocess
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                "markdown", "markdown-extensions", "--break-system-packages"
            ])
            import markdown
            from markdown.extensions import tables, fenced_code, codehilite
        except Exception as e:
            print(f"   ❌ Error instalando markdown: {e}")
            return False
    
    # Convertir Markdown a HTML
    print("   🔄 Convirtiendo a HTML...")
    md = markdown.Markdown(
        extensions=[
            'tables',
            'fenced_code',
            'codehilite',
            'nl2br',
            'sane_lists'
        ]
    )
    
    html_content = md.convert(md_content)
    
    # Crear HTML completo con estilos
    full_html = HTML_TEMPLATE.format(
        css=CSS_STYLE,
        content=html_content
    )
    
    # Guardar archivo HTML
    print(f"   💾 Guardando {OUTPUT_HTML}...")
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(full_html)
    
    file_size = os.path.getsize(OUTPUT_HTML) / 1024  # KB
    print(f"   ✅ Archivo HTML generado: {OUTPUT_HTML}")
    print(f"   📊 Tamaño: {file_size:.1f} KB")
    print(f"\n   📋 Instrucciones:")
    print(f"   1. Abre Google Drive")
    print(f"   2. Sube el archivo: {OUTPUT_HTML}")
    print(f"   3. Haz clic derecho > 'Abrir con' > 'Google Docs' o 'Vista previa'")
    print(f"   4. O simplemente ábrelo en tu navegador")
    
    return True


if __name__ == "__main__":
    success = convert_md_to_html()
    if success:
        print("\n✨ Conversión completada exitosamente!")
    else:
        print("\n❌ Error en la conversión")
        sys.exit(1)
