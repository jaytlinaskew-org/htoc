from pathlib import Path
import win32com.client

_here = Path(__file__).resolve().parent
src_dir = _here / "DOCX_v7"
out_dir = _here / "PDF"
out_dir.mkdir(parents=True, exist_ok=True)

docs = sorted(src_dir.glob("*.docx"))
word = win32com.client.Dispatch("Word.Application")
word.Visible = False
wdExportFormatPDF = 17

try:
    for docx in docs:
        pdf = out_dir / (docx.stem + ".pdf")
        print(f"Converting: {docx.name} -> {pdf.name}")
        doc = word.Documents.Open(str(docx), ReadOnly=False)
        try:
            # Update all fields, including TOC page numbers
            doc.Fields.Update()
            if doc.TablesOfContents.Count > 0:
                for i in range(1, doc.TablesOfContents.Count + 1):
                    doc.TablesOfContents(i).Update()
            doc.ExportAsFixedFormat(
                OutputFileName=str(pdf),
                ExportFormat=wdExportFormatPDF,
                OpenAfterExport=False,
                OptimizeFor=0,
                Range=0,
                From=1,
                To=1,
                Item=0,
                IncludeDocProps=True,
                KeepIRM=True,
                CreateBookmarks=1,
                DocStructureTags=True,
                BitmapMissingFonts=True,
                UseISO19005_1=False,
            )
        finally:
            doc.Close(False)
finally:
    word.Quit()

print(f"Done. Converted {len(docs)} DOCX files to PDF in {out_dir}")
