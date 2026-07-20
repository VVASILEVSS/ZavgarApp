"""
utils/print_utils.py — Утилиты для печати через QPrinter
"""

from __future__ import annotations

from PySide6.QtCore import QMarginsF
from PySide6.QtGui import QPageLayout, QPageSize, QTextDocument
from PySide6.QtPrintSupport import QPrintDialog, QPrinter


def print_table_html(title: str, headers: list[str], rows: list[list[str]]) -> str:
    """Генерация HTML для печати таблицы."""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                font-size: 10pt;
                margin: 20px;
            }}
            h1 {{
                font-size: 16pt;
                color: #1f2937;
                border-bottom: 2px solid #6366f1;
                padding-bottom: 8px;
                margin-bottom: 16px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 12px;
            }}
            th {{
                background-color: #6366f1;
                color: white;
                font-weight: bold;
                padding: 8px 12px;
                text-align: left;
                border: 1px solid #4f46e5;
            }}
            td {{
                padding: 6px 12px;
                border: 1px solid #d1d5db;
            }}
            tr:nth-child(even) {{
                background-color: #f9fafb;
            }}
            tr:hover {{
                background-color: #f3f4f6;
            }}
            .footer {{
                margin-top: 24px;
                font-size: 8pt;
                color: #6b7280;
                text-align: center;
                border-top: 1px solid #e5e7eb;
                padding-top: 8px;
            }}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
        <table>
            <thead>
                <tr>
    """
    
    # Заголовки
    for header in headers:
        html += f"                    <th>{header}</th>\n"
    html += "                </tr>\n            </thead>\n            <tbody>\n"
    
    # Строки данных
    for row in rows:
        html += "                <tr>\n"
        for cell in row:
            html += f"                    <td>{cell}</td>\n"
        html += "                </tr>\n"
    
    html += """            </tbody>
        </table>
        <div class="footer">
            ZavgarApp — Система учёта автопарка
        </div>
    </body>
    </html>
    """
    
    return html


def print_document(title: str, headers: list[str], rows: list[list[str]], parent=None) -> bool:
    """Печать таблицы через QPrinter."""
    html = print_table_html(title, headers, rows)
    
    # Создаём документ
    doc = QTextDocument()
    doc.setHtml(html)
    
    # Настройки страницы
    printer = QPrinter(QPrinter.HighResolution)
    page_layout = QPageLayout(
        QPageSize(QPageSize.A4),
        QPageLayout.Portrait,
        QMarginsF(15, 15, 15, 15)
    )
    printer.setPageLayout(page_layout)
    printer.setDocName(title)
    
    # Диалог печати
    dialog = QPrintDialog(printer, parent)
    if dialog.exec() == QPrintDialog.Accepted:
        doc.print(printer)
        return True
    
    return False


def print_single_record(title: str, fields: list[tuple[str, str]], parent=None) -> bool:
    """Печать одной записи (карточки)."""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                font-size: 11pt;
                margin: 20px;
            }}
            h1 {{
                font-size: 16pt;
                color: #1f2937;
                border-bottom: 2px solid #6366f1;
                padding-bottom: 8px;
                margin-bottom: 16px;
            }}
            .field {{
                margin-bottom: 12px;
                padding: 8px;
                background-color: #f9fafb;
                border-left: 3px solid #6366f1;
            }}
            .label {{
                font-weight: bold;
                color: #374151;
                display: inline-block;
                width: 200px;
            }}
            .value {{
                color: #1f2937;
            }}
            .footer {{
                margin-top: 24px;
                font-size: 8pt;
                color: #6b7280;
                text-align: center;
                border-top: 1px solid #e5e7eb;
                padding-top: 8px;
            }}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
    """
    
    for label, value in fields:
        html += f"""
        <div class="field">
            <span class="label">{label}:</span>
            <span class="value">{value}</span>
        </div>
        """
    
    html += """
        <div class="footer">
            ZavgarApp — Система учёта автопарка
        </div>
    </body>
    </html>
    """
    
    doc = QTextDocument()
    doc.setHtml(html)
    
    printer = QPrinter(QPrinter.HighResolution)
    page_layout = QPageLayout(
        QPageSize(QPageSize.A4),
        QPageLayout.Portrait,
        QMarginsF(15, 15, 15, 15)
    )
    printer.setPageLayout(page_layout)
    printer.setDocName(title)
    
    dialog = QPrintDialog(printer, parent)
    if dialog.exec() == QPrintDialog.Accepted:
        doc.print(printer)
        return True
    
    return False


def print_raw_html(html: str, title: str, parent=None) -> bool:
    """Печать готового HTML без обёртки."""
    doc = QTextDocument()
    doc.setHtml(html)
    
    printer = QPrinter(QPrinter.HighResolution)
    page_layout = QPageLayout(
        QPageSize(QPageSize.A4),
        QPageLayout.Portrait,
        QMarginsF(15, 15, 15, 15)
    )
    printer.setPageLayout(page_layout)
    printer.setDocName(title)
    
    dialog = QPrintDialog(printer, parent)
    if dialog.exec() == QPrintDialog.Accepted:
        doc.print(printer)
        return True
    
    return False
