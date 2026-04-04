import json
import os
import re
import unicodedata

def slugify(text):
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

with open('data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

with open('index.html', 'r', encoding='utf-8') as f:
    template = f.read()

# 1. Update index.html to include Crawler Trap + JSON-LD
crawler_trap_html = '<div class="mt-12 bg-white rounded-[2rem] p-8 border border-slate-200"> <h3 class="text-xl font-bold mb-4">Danh mục tra cứu địa giới hành chính (Dành cho máy chủ & AI)</h3> <ul class="grid grid-cols-2 md:grid-cols-4 gap-4">'
for unit in data['merged_units']:
    slug = slugify(unit['new_name'])
    crawler_trap_html += f'<li><a href="tinh/{slug}.html" class="text-blue-600 hover:underline">Sáp nhập {unit["new_name"]}</a></li>'
crawler_trap_html += '</ul></div>'

if 'id="seoLinks"' not in template:
    template = template.replace('</main>', f'<div id="seoLinks" class="max-w-5xl mx-auto px-4">{crawler_trap_html}</div></main>')

schema = {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Dữ liệu sáp nhập địa giới hành chính Việt Nam 2026",
    "description": "Tra cứu sáp nhập, quyết định, danh mục thay đổi hành chính Việt Nam theo nghị quyết Quốc hội.",
    "url": "https://xuannhiha0107.github.io/geo-vn-search/"
}
schema_script = f'<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>'

if 'application/ld+json' not in template:
    template = template.replace('</head>', f'{schema_script}</head>')

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(template)

sitemap_urls = ["https://xuannhiha0107.github.io/geo-vn-search/index.html"]

os.makedirs('tinh', exist_ok=True)

# Generate individual pages
for unit in data['merged_units']:
    slug = slugify(unit['new_name'])
    old_names = " và ".join([u['name'] for u in unit['old_units']])
    
    parts = unit['effective_date'].split('-')
    f_date = f"{parts[2]}/{parts[1]}/{parts[0]}" if len(parts) == 3 else unit['effective_date']
    
    pop_number = f"{unit.get('population', 0):,}".replace(',', '.') if unit.get('population') else 'Đang cập nhật'
    sq_number = f"{unit.get('area_km2', 0):,}".replace(',', '.') if unit.get('area_km2') else 'Đang cập nhật'
    
    aeo_text = f"Theo {unit['resolution']}, các đơn vị {old_names} đã chính thức sáp nhập thành {unit['new_name']} mang cấp độ {unit['new_type']}. Sự thay đổi về địa giới này chính thức có hiệu lực từ ngày {f_date}."

    old_units_html = "".join([f'<div class="bg-slate-50 border-2 border-dashed border-slate-200 p-4 rounded-xl text-center"><span class="text-sm font-bold text-slate-500">{u["name"]} ({u["type"]})</span></div>' for u in unit['old_units']])
    
    impacts_html = ""
    for imp in unit.get('affected_procedures', []):
        type_str = "Cập nhật tài liệu"
        if "cccd" in imp.lower() or "hộ chiếu" in imp.lower(): type_str = "Định danh cá nhân"
        if "sổ đỏ" in imp.lower() or "đất" in imp.lower(): type_str = "Tài sản / Đất đai"
        if "kinh doanh" in imp.lower() or "thuế" in imp.lower(): type_str = "Kinh doanh / Thuế"
        impacts_html += f'<div class="bg-slate-50 p-6 rounded-2xl border border-slate-100 flex flex-col justify-between"><div><span class="inline-block text-[10px] uppercase font-bold text-blue-600 bg-blue-100 px-2 py-1 rounded-sm mb-3">{type_str}</span><p class="font-medium text-slate-800 text-sm leading-relaxed">{imp}</p></div></div>'

    page_html = template
    
    t_title = f'<title>Sáp nhập {unit["new_name"]} - Cập nhật Nghị quyết thay đổi địa giới</title>'
    t_desc = f'<meta name="description" content="{aeo_text}">'
    page_html = re.sub(r'<title>.*?</title>', t_title, page_html, flags=re.DOTALL)
    page_html = re.sub(r'<meta name="description" content=".*?">', t_desc, page_html)
    
    page_html = page_html.replace('id="defaultState" class="grid', 'id="defaultState" class="hidden grid')
    page_html = page_html.replace('id="resultArea" class="hidden', 'id="resultArea" class=""')
    
    # Simple regex replaces for inner text
    page_html = re.sub(r'(id="aeoOverview"[^>]*>).*?(</p>)', rf'\g<1>{aeo_text}\g<2>', page_html)
    page_html = re.sub(r'(id="resTitle"[^>]*>).*?(</h2>)', rf'\g<1>{unit["new_name"]}\g<2>', page_html)
    page_html = re.sub(r'(id="resSubtitle"[^>]*>).*?(</p>)', rf'\g<1>{unit["new_type"]} thuộc phân vùng {unit.get("region", "")}\g<2>', page_html)
    page_html = re.sub(r'(id="resDate"[^>]*>).*?(</p>)', rf'\g<1>{f_date}\g<2>', page_html)
    
    comparison_trs = f'<tr class="border-b"><td class="p-3 text-sm text-slate-800 font-medium">Tên gọi / Phân cấp</td><td class="p-3 text-sm text-slate-500">{old_names}</td><td class="p-3 text-sm text-slate-800 font-bold text-blue-600">{unit["new_name"]} ({unit["new_type"]})</td></tr><tr class="border-b"><td class="p-3 text-sm text-slate-800 font-medium">Diện tích (km2) / Dân số</td><td class="p-3 text-sm text-slate-500">Phân mảnh địa giới</td><td class="p-3 text-sm text-slate-800 font-bold">{sq_number} km2 / {pop_number} người</td></tr>'
    page_html = re.sub(r'(<tbody id="comparisonTableBody">).*?(</tbody>)', rf'\g<1>{comparison_trs}\g<2>', page_html, flags=re.DOTALL)
    page_html = re.sub(r'(<div id="resOldUnits"[^>]*>).*?(</div>\s+<div class="flex flex-col items-center">)', rf'\g<1>{old_units_html}\g<2>', page_html, flags=re.DOTALL)
    page_html = re.sub(r'(<span id="resNewName"[^>]*>).*?(</span>)', rf'\g<1>{unit["new_name"]}\g<2>', page_html, flags=re.DOTALL)
    page_html = re.sub(r'(id="resResolution"[^>]*>).*?(</p>)', rf'\g<1>{unit["resolution"]}\g<2>', page_html, flags=re.DOTALL)
    page_html = re.sub(r'(id="resSubResolution"[^>]*>).*?(</p>)', rf'\g<1>{unit.get("sub_unit_resolution", "")}\g<2>', page_html, flags=re.DOTALL)
    page_html = re.sub(r'(<div id="resImpacts"[^>]*>).*?(</div>\s+</div>\n        </div>)', rf'\g<1>{impacts_html}\g<2>', page_html, flags=re.DOTALL)
    
    page_html = page_html.replace('href="index.html"', 'href="../index.html"')
    page_html = page_html.replace("fetch('data.json')", "fetch('../data.json')")
    page_html = page_html.replace('href="tinh/', 'href="../tinh/')
    
    with open(f'tinh/{slug}.html', 'w', encoding='utf-8') as f:
        f.write(page_html)
        
    sitemap_urls.append(f"https://xuannhiha0107.github.io/geo-vn-search/tinh/{slug}.html")

with open('robots.txt', 'w', encoding='utf-8') as f:
    f.write("User-agent: *\nAllow: /\nSitemap: https://xuannhiha0107.github.io/geo-vn-search/sitemap.xml")

sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
for url in sitemap_urls:
    sitemap_xml += f'  <url>\n    <loc>{url}</loc>\n  </url>\n'
sitemap_xml += '</urlset>'

with open('sitemap.xml', 'w', encoding='utf-8') as f:
    f.write(sitemap_xml)

print("Generated SSG specifically optimized for AEO.")
