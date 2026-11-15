"""Build the printable report from its Markdown source using python-docx."""
from pathlib import Path
import re
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]/'reports'
SOURCE = ROOT/'COMPLETE_PROJECT_REPORT.md'
OUTPUT = ROOT/'QKD_SDN_Complete_Report.docx'


def shade(cell, fill):
    node=OxmlElement('w:shd');node.set(qn('w:fill'),fill)
    cell._tc.get_or_add_tcPr().append(node)


def main():
    doc=Document()
    doc.core_properties.title='Theory experiments and interpretation of the QKD SDN project'
    doc.core_properties.subject='Simulation findings and practical results guide'
    doc.core_properties.author='QKD SDN project'
    sec=doc.sections[0]
    sec.page_width,sec.page_height=Inches(8.27),Inches(11.69)
    sec.top_margin,sec.bottom_margin=Inches(.7),Inches(.65)
    sec.left_margin,sec.right_margin=Inches(.72),Inches(.72)
    sec.header_distance,sec.footer_distance=Inches(.3),Inches(.3)
    styles=doc.styles
    normal=styles['Normal']
    normal.font.name='Calibri';normal.font.size=Pt(11)
    normal.font.color.rgb=RGBColor(0,0,0)
    normal.paragraph_format.space_after=Pt(6)
    normal.paragraph_format.line_spacing=1.08
    normal.paragraph_format.widow_control=True
    for name,size in [('Title',24),('Heading 1',16),('Heading 2',12)]:
        style=styles[name];style.font.name='Calibri';style.font.size=Pt(size)
        style.font.color.rgb=RGBColor(0,0,0)
        style.paragraph_format.space_before=Pt(14 if name!='Title' else 0)
        style.paragraph_format.space_after=Pt(7)
        style.paragraph_format.keep_with_next=True
    styles['Title'].font.bold=True
    # The bundled default template has decorative title borders; remove them.
    for border in list(styles.element.xpath('.//w:pBdr')):
        border.getparent().remove(border)
    header=sec.header.paragraphs[0]
    header.add_run('QKD SDN PROJECT  |  Theory and experiment report').font.size=Pt(8)
    footer=sec.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.RIGHT
    footer.add_run('15 November 2026  |  Page ').font.size=Pt(8)
    for field_type in ('PAGE','NUMPAGES'):
        if field_type=='NUMPAGES':footer.add_run(' of ').font.size=Pt(8)
        node=OxmlElement('w:fldSimple');node.set(qn('w:instr'),field_type)
        footer._p.append(node)
    lines=SOURCE.read_text(encoding='utf-8').splitlines()
    i=0
    while i<len(lines):
        line=lines[i]
        if not line.strip():i+=1;continue
        if line.startswith('```'):
            code=[];i+=1
            while i<len(lines) and not lines[i].startswith('```'):
                code.append(lines[i]);i+=1
            p=doc.add_paragraph('\n'.join(code))
            p.paragraph_format.space_before=Pt(3);p.paragraph_format.space_after=Pt(9)
            p.paragraph_format.line_spacing=1.05
            for run in p.runs:run.font.name='Consolas';run.font.size=Pt(8.5)
            i+=1;continue
        if line.startswith('|'):
            data=[]
            while i<len(lines) and lines[i].startswith('|'):
                cells=[v.strip() for v in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch('[-: ]+',v) for v in cells):data.append(cells)
                i+=1
            n=len(data[0]);table=doc.add_table(rows=0,cols=n)
            table.alignment=WD_TABLE_ALIGNMENT.CENTER;table.autofit=False
            if n==3:fractions=[.24,.35,.41]
            elif n==4:fractions=[.28,.24,.24,.24]
            elif n==5:fractions=[.13,.25,.14,.17,.31]
            else:fractions=[1/n]*n
            # Prefer a compact first column and wider descriptive columns.
            if data[0][0] in ('Scenario name','Path','File or folder'):
                fractions=[.22,.41,.37] if n==3 else fractions
            if data[0][0]=='File or folder':fractions=[.38,.34,.28]
            for col,f in zip(table.columns,fractions):col.width=Inches(6.83*f)
            borders=OxmlElement('w:tblBorders')
            for edge in ('top','left','bottom','right','insideH','insideV'):
                node=OxmlElement('w:'+edge)
                node.set(qn('w:val'),'single');node.set(qn('w:sz'),'4');node.set(qn('w:color'),'D9D9D9')
                borders.append(node)
            table._tbl.tblPr.append(borders)
            for row_index,values in enumerate(data):
                row=table.add_row();trpr=row._tr.get_or_add_trPr()
                trpr.append(OxmlElement('w:cantSplit'))
                if row_index==0:trpr.append(OxmlElement('w:tblHeader'))
                for j,(cell,text) in enumerate(zip(row.cells,values)):
                    cell.width=Inches(6.83*fractions[j]);cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
                    tcpr=cell._tc.get_or_add_tcPr();margins=OxmlElement('w:tcMar')
                    for edge in ('top','bottom','left','right'):
                        node=OxmlElement('w:'+edge);node.set(qn('w:w'),'90');node.set(qn('w:type'),'dxa');margins.append(node)
                    tcpr.append(margins)
                    shade(cell,'203B53' if row_index==0 else 'F2F5F7' if row_index%2==0 else 'FFFFFF')
                    p=cell.paragraphs[0];p.paragraph_format.space_after=Pt(2);p.paragraph_format.space_before=Pt(2)
                    p.paragraph_format.line_spacing=1.03
                    r=p.add_run(text);r.font.size=Pt(9.5)
                    if row_index==0:r.font.bold=True;r.font.color.rgb=RGBColor(255,255,255)
                    if n>=4 and j>0 and len(text)<22:p.alignment=WD_ALIGN_PARAGRAPH.CENTER
            doc.add_paragraph().paragraph_format.space_after=Pt(1)
            continue
        if line.startswith('# '):doc.add_paragraph(line[2:],style='Title');i+=1;continue
        if line.startswith('## '):
            doc.add_paragraph(line[3:],style='Heading 1');i+=1;continue
        if line.startswith('### '):
            doc.add_paragraph(line[4:],style='Heading 2');i+=1;continue
        # Markdown paragraphs are stored on one line in the source.
        p=doc.add_paragraph(line)
        if line.startswith('Report date:'):p.runs[0].italic=True;p.runs[0].font.size=Pt(10)
        # Pair existing scientific plot with the relevant interpretation section.
        if line.startswith('No unaffected wavelength was permanently isolated'):
            image=ROOT.parent/'results/hybrid/isolation_comparison.png'
            if image.exists():
                pic=doc.add_paragraph();pic.add_run().add_picture(str(image),width=Inches(6.7))
                pic.paragraph_format.keep_with_next=True
                props=pic._p.xpath('.//wp:docPr')
                for prop in props:prop.set('descr','Isolation decisions in selected scenarios across twenty seeds; benign correlated drift causes more false isolation under the combined policy.')
                cap=doc.add_paragraph('Figure 1  Runs with permanent isolation in selected scenarios. A high bar is a desired response for the tested attacks, but a failure cost for benign correlated drift.')
                cap.runs[0].font.size=Pt(9)
        i+=1
    doc.save(OUTPUT)
    print(OUTPUT)
    print('Source words:',len(SOURCE.read_text(encoding='utf-8').split()))


if __name__=='__main__':main()
