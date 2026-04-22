"""
Generator for per-category service fixtures.
Reads current services.json, rebuilds into 7 category files under
src/lily_backend/system/fixtures/catalog/service/ with full DE/EN/RU/UK + SEO.

PK plan:
  1-4   hair (unchanged)
  5-10  nails (manicure/extensions) — price/duration fixes
  11    pedicure smart-complete — price 55 -> 60
  13-20 brows & lashes — price/duration fixes (21 REMOVED)
  22-28 cosmetology existing — price fixes
  29-34 massage existing — price fixes
  35-38 depilation existing women (39 REMOVED)
  40    depilation men back — duration 45 -> 25
  41-44 pedicure & nail extras (unchanged)
  45    NEW: Nagelverlängerungen 4-6D (nails)
  46    NEW: Effektzuschlag (brows/lashes addon)
  47-49 NEW: massage zones (Beine, Hüften, Bauch)
  50-63 NEW: cosmetology (+14 services)
  70-83 NEW: depilation women/men (+14 services)
"""

import json
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FX = ROOT / "src" / "lily_backend" / "system" / "fixtures" / "catalog"
SERVICE_DIR = FX / "service"
SERVICE_DIR.mkdir(exist_ok=True)

with open(FX / "services.json", encoding="utf-8") as f:
    raw = json.load(f)

existing = {e["pk"]: e for e in raw if e["model"] == "main.service"}


def svc(pk, fields):
    return {"model": "main.service", "pk": pk, "fields": fields}


def patch(pk, **overrides):
    entry = deepcopy(existing[pk])
    for k, v in overrides.items():
        entry["fields"][k] = v
    return entry


# ---------- Helper: build a full service field set ----------
def make(
    pk,
    *,
    category,
    slug,
    order,
    name_de,
    name_en,
    name_ru,
    name_uk,
    price,
    duration,
    duration_info_de,
    duration_info_en,
    duration_info_ru,
    duration_info_uk,
    description_de,
    description_en,
    description_ru,
    description_uk,
    content_de,
    content_en,
    content_ru,
    content_uk,
    seo_title_de,
    seo_title_en,
    seo_title_ru,
    seo_title_uk,
    seo_desc_de,
    seo_desc_en,
    seo_desc_ru,
    seo_desc_uk,
    is_hit=False,
    is_addon=False,
    parallel_ok=True,
    parallel_group="",
    min_gap_after_minutes=0,
    price_info_de="",
    price_info_en="",
    price_info_ru="",
    price_info_uk="",
):
    return svc(
        pk,
        {
            "seo_title": seo_title_de,
            "seo_title_de": seo_title_de,
            "seo_title_en": seo_title_en,
            "seo_title_ru": seo_title_ru,
            "seo_title_uk": seo_title_uk,
            "seo_description": seo_desc_de,
            "seo_description_de": seo_desc_de,
            "seo_description_en": seo_desc_en,
            "seo_description_ru": seo_desc_ru,
            "seo_description_uk": seo_desc_uk,
            "seo_image": "",
            "duration": duration,
            "min_gap_after_minutes": min_gap_after_minutes,
            "parallel_ok": parallel_ok,
            "parallel_group": parallel_group,
            "name": name_de,
            "name_de": name_de,
            "name_en": name_en,
            "name_ru": name_ru,
            "name_uk": name_uk,
            "slug": slug,
            "category": category,
            "price": f"{price:.2f}",
            "price_info": price_info_de,
            "price_info_de": price_info_de or None,
            "price_info_en": price_info_en,
            "price_info_ru": price_info_ru or None,
            "price_info_uk": price_info_uk or None,
            "duration_info": duration_info_de,
            "duration_info_de": duration_info_de or None,
            "duration_info_en": duration_info_en,
            "duration_info_ru": duration_info_ru,
            "duration_info_uk": duration_info_uk,
            "description": description_de,
            "description_de": description_de,
            "description_en": description_en,
            "description_ru": description_ru,
            "description_uk": description_uk,
            "content": content_de,
            "content_de": content_de,
            "content_en": content_en,
            "content_ru": content_ru,
            "content_uk": content_uk,
            "image": "",
            "is_active": True,
            "is_hit": is_hit,
            "is_addon": is_addon,
            "order": order,
            "masters": [],
            "excludes": [],
        },
    )


# ===================== HAIR (cat=1) =====================
hair = [deepcopy(existing[pk]) for pk in (1, 2, 3, 4)]

# ===================== NAILS (cat=2) =====================
nails = [
    deepcopy(existing[5]),  # Klassische Damenmaniküre
    deepcopy(existing[6]),  # Maniküre + Gellack (Premium)
    deepcopy(existing[7]),  # Maniküre + normaler Nagellack
    deepcopy(existing[8]),  # Maniküre für Männer
    deepcopy(existing[9]),  # Nagelverlängerungen (bis 3 cm)
    deepcopy(existing[10]),  # Russian Manicure Extreme
    deepcopy(existing[12]),  # Fremdmodellage entfernen
    deepcopy(existing[41]),  # Gel-Auffüllung
]
# Fix durations per old-list
nails[0]["fields"]["duration"] = 40  # was 45
nails[1]["fields"]["duration"] = 120  # was 90

# New: Nagelverlängerungen 4-6D
nails.append(
    make(
        pk=45,
        category=2,
        slug="nail-extensions-long-4-6",
        order=75,
        name_de="Nagelverlängerungen 4-6 cm",
        name_en="Nail Extensions 4-6 cm",
        name_ru="Наращивание ногтей 4-6 см",
        name_uk="Нарощування нігтів 4-6 см",
        price=90.00,
        duration=150,
        duration_info_de="150 Min",
        duration_info_en="150 min",
        duration_info_ru="150 мин",
        duration_info_uk="150 хв",
        description_de="Lange Nagelverlängerung (4-6 cm) mit Gel/Acrygel auf Ga&Ma & SAGA.",
        description_en="Long nail extensions (4-6 cm) with gel/acrygel on Ga&Ma & SAGA.",
        description_ru="Длинное наращивание ногтей (4-6 см) гелем/акригелем на Ga&Ma и SAGA.",
        description_uk="Довге нарощування нігтів (4-6 см) гелем/акригелем на Ga&Ma та SAGA.",
        content_de="<p>Extralange Modellierung (4-6 cm) für Liebhaber auffälliger Looks. Wir nutzen harte Gele von <strong>Ga&Ma</strong> (Strong Gel Snow) und Architekturgele <strong>SAGA Professional</strong> für eine widerstandsfähige, aber dünne Nagelform.</p><p>Design-Finish aus den Kollektionen <em>Lunamoon</em>, <em>Venalisa</em> oder mit <em>Glow Cat</em>-Effekten nach Wahl.</p>",
        content_en="<p>Extra long modelling (4-6 cm) for lovers of bold looks. We use hard gels by <strong>Ga&Ma</strong> (Strong Gel Snow) and architecture gels by <strong>SAGA Professional</strong> for a durable yet thin nail shape.</p><p>Design finish from <em>Lunamoon</em>, <em>Venalisa</em> collections or with <em>Glow Cat</em> effects on request.</p>",
        content_ru="<p>Экстра-длинное моделирование (4-6 см) для любительниц эффектных образов. Работаем на жёстких гелях <strong>Ga&Ma</strong> (Strong Gel Snow) и архитектурных гелях <strong>SAGA Professional</strong> — форма прочная, но при этом тонкая и элегантная.</p><p>Финальный дизайн — из коллекций <em>Lunamoon</em>, <em>Venalisa</em> или с дизайнерскими эффектами <em>Glow Cat</em>.</p>",
        content_uk="<p>Екстра-довге моделювання (4-6 см) для любительок ефектних образів. Працюємо на жорстких гелях <strong>Ga&Ma</strong> (Strong Gel Snow) та архітектурних гелях <strong>SAGA Professional</strong> — форма міцна, але тонка та елегантна.</p><p>Фінальний дизайн — з колекцій <em>Lunamoon</em>, <em>Venalisa</em> або з дизайнерськими ефектами <em>Glow Cat</em>.</p>",
        seo_title_de="Nagelverlängerungen 4-6 cm Köthen | Long Nails | LILY",
        seo_title_en="Long Nail Extensions 4-6 cm Köthen | LILY",
        seo_title_ru="Длинное наращивание ногтей 4-6 см Кётен | LILY",
        seo_title_uk="Довге нарощування нігтів 4-6 см Кьотен | LILY",
        seo_desc_de="Extralange Nagelverlängerung 4-6 cm in Köthen. Gel & Acrygel von Ga&Ma und SAGA.",
        seo_desc_en="Extra long nail extensions (4-6 cm) in Köthen. Gel & acrygel by Ga&Ma and SAGA.",
        seo_desc_ru="Экстра-длинное наращивание ногтей 4-6 см в Кётене. Гель и акригель Ga&Ma и SAGA.",
        seo_desc_uk="Екстра-довге нарощування нігтів 4-6 см у Кьотені. Гель та акригель Ga&Ma і SAGA.",
    )
)

# ===================== PEDICURE (cat=2) =====================
pedicure = [
    deepcopy(existing[11]),  # Smart-Pediküre Komplett
    deepcopy(existing[42]),  # Pediküre (nur Zehen)
    deepcopy(existing[43]),  # SMART-Pediküre (ohne Lack)
    deepcopy(existing[44]),  # Pediküre (nur Zehen) mit UV-Lack
]
# Price fix: Smart-Pediküre Komplett 55 -> 60 (old list "Pediküre + Gel-Lack €60")
pedicure[0]["fields"]["price"] = "60.00"

# ===================== COSMETOLOGY (cat=3) =====================
cosmetology = []
# Existing 7 with price fixes
e = deepcopy(existing[22])  # Kombinierte Gesichtsreinigung
e["fields"]["price"] = "65.00"
cosmetology.append(e)  # 50 -> 65
cosmetology.append(deepcopy(existing[23]))  # HydraFacial 80
cosmetology.append(deepcopy(existing[24]))  # AnubisMed Peel 65
cosmetology.append(deepcopy(existing[25]))  # Christina Forever Young 90
e = deepcopy(existing[26])  # Carboxytherapie
e["fields"]["price"] = "50.00"
cosmetology.append(e)  # 40 -> 50
e = deepcopy(existing[27])  # Kryotherapie
e["fields"]["price"] = "50.00"
cosmetology.append(e)  # 35 -> 50
cosmetology.append(deepcopy(existing[28]))  # Fruchtsäurepeeling 35

# New cosmetology services (pk 50-64) — 14 items
cosmetology.append(
    make(
        pk=50,
        category=3,
        slug="cosmetology-cleansing-peel",
        order=15,
        name_de="Gesichtsreinigung + Peeling",
        name_en="Facial Cleansing + Peeling",
        name_ru="Комбинированная чистка + пилинг",
        name_uk="Комбіноване очищення + пілінг",
        price=80.00,
        duration=60,
        duration_info_de="60 Min",
        duration_info_en="60 min",
        duration_info_ru="60 мин",
        duration_info_uk="60 хв",
        description_de="Tiefenreinigung mit abschließendem Säurepeeling für Leuchtkraft.",
        description_en="Deep cleansing finished with an acid peel for a radiant complexion.",
        description_ru="Глубокая чистка с финальным кислотным пилингом для сияния.",
        description_uk="Глибоке очищення з фінальним кислотним пілінгом для сяйва.",
        content_de="<p>Zwei Rituale in einer Sitzung: manuelle + Ultraschallreinigung und anschließendes mildes Säurepeeling. Die Haut wird glatter, der Teint heller und das Relief ebenmäßiger.</p>",
        content_en="<p>Two rituals in one visit: manual + ultrasound cleansing followed by a gentle acid peel. The skin becomes smoother, the complexion brighter and the texture more even.</p>",
        content_ru="<p>Два ритуала за один визит: мануальная и ультразвуковая чистка с последующим мягким кислотным пилингом. Кожа становится глаже, тон — ровнее, рельеф — мягче.</p>",
        content_uk="<p>Два ритуали за один візит: мануальна та ультразвукова чистка з подальшим м'яким кислотним пілінгом. Шкіра стає гладшою, тон рівнішим, рельєф м'якшим.</p>",
        seo_title_de="Gesichtsreinigung + Peeling Köthen | Kombi-Behandlung | LILY",
        seo_title_en="Facial Cleansing + Peeling Köthen | Combo | LILY",
        seo_title_ru="Чистка лица + пилинг Кётен | Комбо уход | LILY",
        seo_title_uk="Чистка обличчя + пілінг Кьотен | Комбо догляд | LILY",
        seo_desc_de="Kombinierte Gesichtsreinigung mit Säurepeeling. Tiefenreinigung und Erneuerung in Köthen.",
        seo_desc_en="Combined facial cleansing with acid peel. Deep cleanse and renewal in Köthen.",
        seo_desc_ru="Комбинированная чистка лица с кислотным пилингом. Глубокое очищение и обновление в Кётене.",
        seo_desc_uk="Комбінована чистка обличчя з кислотним пілінгом. Глибоке очищення та оновлення в Кьотені.",
    )
)

cosmetology.append(
    make(
        pk=51,
        category=3,
        slug="cosmetology-carboxy-neck-decolte",
        order=55,
        name_de="Carboxytherapie + Hals & Dekolleté",
        name_en="Carboxytherapy + Neck & Décolleté",
        name_ru="Карбокситерапия + шея и декольте",
        name_uk="Карбокситерапія + шия та декольте",
        price=80.00,
        duration=60,
        duration_info_de="60 Min",
        duration_info_en="60 min",
        duration_info_ru="60 мин",
        duration_info_uk="60 хв",
        description_de="Nicht-invasive CO₂-Therapie für Gesicht, Hals und Dekolleté.",
        description_en="Non-invasive CO₂ therapy for face, neck and décolleté.",
        description_ru="Безинъекционная карбокситерапия для лица, шеи и декольте.",
        description_uk="Безін'єкційна карбоксітерапія для обличчя, шиї та декольте.",
        content_de="<p>Erweitertes Carboxy-Protokoll: Sauerstoffanreicherung für Gesicht, Hals und Dekolleté in einer Sitzung. Gegen Schwellungen, fahle Haut und erste Anzeichen der Hautalterung in den empfindlichen Zonen.</p>",
        content_en="<p>Extended carboxy protocol: oxygen saturation for face, neck and décolleté in a single session. Targets puffiness, dull skin and early signs of ageing in sensitive zones.</p>",
        content_ru="<p>Расширенный протокол карбокситерапии: насыщение кислородом лица, шеи и декольте за один сеанс. Работает с отёчностью, тусклостью кожи и ранними признаками старения в деликатных зонах.</p>",
        content_uk="<p>Розширений протокол карбоксітерапії: насичення киснем обличчя, шиї та декольте за один сеанс. Працює з набряклістю, тьмяністю шкіри та ранніми ознаками старіння в делікатних зонах.</p>",
        seo_title_de="Carboxytherapie Hals Dekolleté Köthen | LILY",
        seo_title_en="Carboxytherapy Neck & Décolleté Köthen | LILY",
        seo_title_ru="Карбокситерапия шея декольте Кётен | LILY",
        seo_title_uk="Карбоксітерапія шия декольте Кьотен | LILY",
        seo_desc_de="Carboxytherapie mit Hals- und Dekolleté-Bereich in Köthen. Anti-Aging ohne Injektionen.",
        seo_desc_en="Carboxytherapy with neck and décolleté in Köthen. Anti-aging without injections.",
        seo_desc_ru="Карбокситерапия с зоной шеи и декольте в Кётене. Омоложение без инъекций.",
        seo_desc_uk="Карбоксітерапія із зоною шиї та декольте в Кьотені. Омолодження без ін'єкцій.",
    )
)

cosmetology.append(
    make(
        pk=52,
        category=3,
        slug="cosmetology-cleansing-carboxy",
        order=25,
        name_de="Gesichtsreinigung + Carboxytherapie",
        name_en="Facial Cleansing + Carboxytherapy",
        name_ru="Чистка лица + карбокситерапия",
        name_uk="Чистка обличчя + карбоксітерапія",
        price=100.00,
        duration=90,
        duration_info_de="90 Min",
        duration_info_en="90 min",
        duration_info_ru="90 мин",
        duration_info_uk="90 хв",
        description_de="Premium-Kombi: Tiefenreinigung und anschließende CO₂-Therapie.",
        description_en="Premium combo: deep cleansing followed by CO₂ therapy.",
        description_ru="Премиум-комбо: глубокая чистка с последующей карбокситерапией.",
        description_uk="Преміум-комбо: глибока чистка з подальшою карбокситерапією.",
        content_de="<p>Maximale Rundum-Behandlung: wir reinigen die Poren tief (manuell + Ultraschall) und beenden mit Carboxytherapie — Sauerstoff und Nährstoffe dringen in die frisch gereinigte Haut ein. Ergebnis: strahlender, praller Teint ohne Rötungen.</p>",
        content_en="<p>Maximum all-round treatment: deep pore cleansing (manual + ultrasound) followed by carboxytherapy — oxygen and nutrients penetrate the freshly cleansed skin. Result: a radiant, plumped complexion with no redness.</p>",
        content_ru="<p>Максимальный комплексный уход: глубокое очищение пор (мануальная + ультразвук) и финальная карбокситерапия — кислород и активы проникают в только что очищенную кожу. Итог: сияющий, наполненный тон без покраснений.</p>",
        content_uk="<p>Максимальний комплексний догляд: глибоке очищення пор (мануальна + ультразвук) та фінальна карбокситерапія — кисень та активи проникають у щойно очищену шкіру. Підсумок: сяючий, наповнений тон без почервонінь.</p>",
        seo_title_de="Gesichtsreinigung + Carboxy Köthen | Premium Kombi | LILY",
        seo_title_en="Facial Cleansing + Carboxy Köthen | Premium Combo | LILY",
        seo_title_ru="Чистка + карбокситерапия Кётен | Премиум уход | LILY",
        seo_title_uk="Чистка + карбоксітерапія Кьотен | Преміум догляд | LILY",
        seo_desc_de="Tiefenreinigung in Kombination mit Carboxytherapie in Köthen.",
        seo_desc_en="Deep cleansing combined with carboxytherapy in Köthen.",
        seo_desc_ru="Глубокая чистка в сочетании с карбокситерапией в Кётене.",
        seo_desc_uk="Глибока чистка в поєднанні з карбоксітерапією в Кьотені.",
    )
)

cosmetology.append(
    make(
        pk=53,
        category=3,
        slug="cosmetology-enzyme-therapy",
        order=80,
        name_de="Enzymtherapie",
        name_en="Enzyme Therapy",
        name_ru="Ферментная терапия",
        name_uk="Ферментна терапія",
        price=75.00,
        duration=50,
        duration_info_de="50 Min",
        duration_info_en="50 min",
        duration_info_ru="50 мин",
        duration_info_uk="50 хв",
        description_de="Schonende Enzym-Exfoliation für empfindliche Haut.",
        description_en="Gentle enzyme exfoliation for sensitive skin.",
        description_ru="Деликатная ферментная эксфолиация для чувствительной кожи.",
        description_uk="Делікатна ферментна ексфоліація для чутливої шкіри.",
        content_de="<p>Alternative zum Säurepeeling: pflanzliche Enzyme lösen abgestorbene Hautzellen sanft auf und regen die Regeneration an. Ideal für empfindliche oder gereizte Haut im Winter.</p>",
        content_en="<p>An alternative to acid peels: plant enzymes gently dissolve dead skin cells and stimulate regeneration. Ideal for sensitive or irritated skin, especially in winter.</p>",
        content_ru="<p>Альтернатива кислотным пилингам: растительные ферменты мягко растворяют ороговевшие клетки и активируют регенерацию. Идеально для чувствительной или раздражённой кожи в холодный сезон.</p>",
        content_uk="<p>Альтернатива кислотним пілінгам: рослинні ферменти м'яко розчиняють ороговілі клітини та активують регенерацію. Ідеально для чутливої або подразненої шкіри в холодний сезон.</p>",
        seo_title_de="Enzymtherapie Köthen | Sanftes Peeling | LILY",
        seo_title_en="Enzyme Therapy Köthen | Gentle Peel | LILY",
        seo_title_ru="Ферментная терапия Кётен | Мягкий пилинг | LILY",
        seo_title_uk="Ферментна терапія Кьотен | М'який пілінг | LILY",
        seo_desc_de="Sanfte Enzymtherapie für empfindliche Haut in Köthen. Ohne Reizungen.",
        seo_desc_en="Gentle enzyme therapy for sensitive skin in Köthen. Non-irritating.",
        seo_desc_ru="Мягкая ферментная терапия для чувствительной кожи в Кётене. Без раздражения.",
        seo_desc_uk="М'яка ферментна терапія для чутливої шкіри в Кьотені. Без подразнення.",
    )
)

cosmetology.append(
    make(
        pk=54,
        category=3,
        slug="cosmetology-anti-acne",
        order=85,
        name_de="Anti-Akne-Gesichtspflege",
        name_en="Anti-Acne Facial Care",
        name_ru="Уход за лицом против акне",
        name_uk="Догляд за обличчям проти акне",
        price=55.00,
        duration=45,
        duration_info_de="45 Min",
        duration_info_en="45 min",
        duration_info_ru="45 мин",
        duration_info_uk="45 хв",
        description_de="Protokoll gegen Akne und entzündete Haut mit Christina Comodex.",
        description_en="Protocol for acne-prone and inflamed skin with Christina Comodex.",
        description_ru="Протокол против акне и воспалённой кожи на Christina Comodex.",
        description_uk="Протокол проти акне та запаленої шкіри на Christina Comodex.",
        content_de="<p>Zielgerichtete Behandlung mit <strong>Christina Comodex</strong>: Reinigung, entzündungshemmende Masken und Wirkstoffe, die Talg normalisieren und Rötungen beruhigen. Regelmäßige Anwendung reduziert Ausbrüche sichtbar.</p>",
        content_en="<p>Targeted treatment with <strong>Christina Comodex</strong>: cleansing, anti-inflammatory masks and actives that normalise sebum and calm redness. Regular application visibly reduces breakouts.</p>",
        content_ru="<p>Целевая процедура на <strong>Christina Comodex</strong>: очищение, противовоспалительные маски и активы, нормализующие работу сальных желёз и снимающие покраснения. При курсе заметно уменьшает высыпания.</p>",
        content_uk="<p>Цільова процедура на <strong>Christina Comodex</strong>: очищення, протизапальні маски та активи, що нормалізують роботу сальних залоз і знімають почервоніння. Курсом помітно зменшує висипання.</p>",
        seo_title_de="Anti-Akne Gesichtspflege Köthen | Christina Comodex | LILY",
        seo_title_en="Anti-Acne Facial Köthen | Christina Comodex | LILY",
        seo_title_ru="Уход против акне Кётен | Christina Comodex | LILY",
        seo_title_uk="Догляд проти акне Кьотен | Christina Comodex | LILY",
        seo_desc_de="Professionelle Anti-Akne-Pflege mit Christina Comodex in Köthen.",
        seo_desc_en="Professional anti-acne facial with Christina Comodex in Köthen.",
        seo_desc_ru="Профессиональный уход против акне на Christina Comodex в Кётене.",
        seo_desc_uk="Професійний догляд проти акне на Christina Comodex у Кьотені.",
    )
)

cosmetology.append(
    make(
        pk=55,
        category=3,
        slug="cosmetology-line-correction",
        order=90,
        name_de="Gesichtspflege zur Linienkorrektur",
        name_en="Anti-Wrinkle Facial Care",
        name_ru="Уход за лицом для коррекции морщин",
        name_uk="Догляд за обличчям для корекції зморшок",
        price=50.00,
        duration=30,
        duration_info_de="30 Min",
        duration_info_en="30 min",
        duration_info_ru="30 мин",
        duration_info_uk="30 хв",
        description_de="Expresspflege mit Peptiden gegen feine Linien.",
        description_en="Express peptide care against fine lines.",
        description_ru="Экспресс-уход с пептидами против мелких морщин.",
        description_uk="Експрес-догляд з пептидами проти дрібних зморшок.",
        content_de="<p>Ein schneller Anti-Age-Fix: Peptid-Seren und straffende Masken glätten feine Linien und frischen die Haut auf. Perfekt vor einem Event oder einer Fotosession.</p>",
        content_en="<p>A quick anti-age fix: peptide serums and firming masks smooth fine lines and refresh the skin. Perfect before an event or a photo shoot.</p>",
        content_ru="<p>Быстрый антивозрастной ритуал: пептидные сыворотки и подтягивающие маски разглаживают мелкие морщины и освежают кожу. Отличный вариант перед выходом или съёмкой.</p>",
        content_uk="<p>Швидкий антивіковий ритуал: пептидні сироватки та підтягуючі маски розгладжують дрібні зморшки і освіжають шкіру. Чудовий варіант перед виходом чи зйомкою.</p>",
        seo_title_de="Anti-Falten Pflege Köthen | Linienkorrektur | LILY",
        seo_title_en="Anti-Wrinkle Facial Köthen | Line Correction | LILY",
        seo_title_ru="Уход против морщин Кётен | Коррекция линий | LILY",
        seo_title_uk="Догляд проти зморшок Кьотен | Корекція ліній | LILY",
        seo_desc_de="Anti-Falten-Pflege mit Peptiden in Köthen. Express-Lifting.",
        seo_desc_en="Anti-wrinkle peptide facial in Köthen. Express lifting.",
        seo_desc_ru="Уход против морщин с пептидами в Кётене. Экспресс-лифтинг.",
        seo_desc_uk="Догляд проти зморшок з пептидами в Кьотені. Експрес-ліфтинг.",
    )
)

cosmetology.append(
    make(
        pk=56,
        category=3,
        slug="cosmetology-nuance-care",
        order=95,
        name_de="Nuance Gesichtspflege",
        name_en="Nuance Facial Care",
        name_ru="Деликатный уход за лицом Nuance",
        name_uk="Делікатний догляд за обличчям Nuance",
        price=55.00,
        duration=30,
        duration_info_de="30 Min",
        duration_info_en="30 min",
        duration_info_ru="30 мин",
        duration_info_uk="30 хв",
        description_de="Beruhigende Pflege für reaktive und empfindliche Haut.",
        description_en="Soothing facial for reactive and sensitive skin.",
        description_ru="Успокаивающий уход за реактивной и чувствительной кожей.",
        description_uk="Заспокійливий догляд за реактивною та чутливою шкірою.",
        content_de="<p>Sanfte Pflegeroutine mit beruhigenden Wirkstoffen. Ideal bei Rötungen, Couperose oder nach apparativen Eingriffen. Stellt die Barriere wieder her und reduziert Spannungsgefühle.</p>",
        content_en="<p>A gentle care routine with soothing actives. Ideal for redness, couperose or after hardware treatments. Restores the barrier and reduces tightness.</p>",
        content_ru="<p>Деликатная уходовая процедура с успокаивающими активами. Идеально при покраснениях, куперозе или после аппаратных вмешательств. Восстанавливает барьер и снимает чувство стянутости.</p>",
        content_uk="<p>Делікатна процедура догляду із заспокійливими активами. Ідеально при почервоніннях, куперозі або після апаратних втручань. Відновлює бар'єр та знімає відчуття стягнутості.</p>",
        seo_title_de="Nuance Gesichtspflege Köthen | Sensitive Skin | LILY",
        seo_title_en="Nuance Facial Care Köthen | Sensitive Skin | LILY",
        seo_title_ru="Уход Nuance Кётен | Чувствительная кожа | LILY",
        seo_title_uk="Догляд Nuance Кьотен | Чутлива шкіра | LILY",
        seo_desc_de="Beruhigender Gesichtspflege für sensible Haut in Köthen.",
        seo_desc_en="Soothing facial for sensitive skin in Köthen.",
        seo_desc_ru="Успокаивающий уход для чувствительной кожи в Кётене.",
        seo_desc_uk="Заспокійливий догляд для чутливої шкіри в Кьотені.",
    )
)

cosmetology.append(
    make(
        pk=57,
        category=3,
        slug="cosmetology-rf-lifting",
        order=100,
        name_de="HF-Hebetechnik (RF-Lifting)",
        name_en="RF Lifting",
        name_ru="RF-лифтинг",
        name_uk="RF-ліфтинг",
        price=40.00,
        duration=15,
        duration_info_de="15 Min",
        duration_info_en="15 min",
        duration_info_ru="15 мин",
        duration_info_uk="15 хв",
        description_de="Radiofrequenz-Lifting mit Zemits für straffere Konturen.",
        description_en="Radiofrequency lifting with Zemits for firmer contours.",
        description_ru="Радиоволновой лифтинг на Zemits для подтяжки контуров.",
        description_uk="Радіохвильовий ліфтинг на Zemits для підтяжки контурів.",
        content_de="<p>Express-Lifting mit Radiofrequenz: wir erwärmen die tieferen Hautschichten mit <strong>Zemits</strong>-Geräten und HyaTight-Gelen. Das stimuliert Kollagen und strafft sichtbar Wangen, Kinnlinie und Oberlid-Bereich.</p>",
        content_en="<p>Express RF lifting: we warm the deeper skin layers with <strong>Zemits</strong> devices and HyaTight gels. This stimulates collagen and visibly firms cheeks, jawline and upper-eye area.</p>",
        content_ru="<p>Экспресс-лифтинг радиоволнами: прогреваем глубокие слои кожи аппаратами <strong>Zemits</strong> с гелями HyaTight. Стимулирует коллаген и заметно подтягивает щёки, овал и зону верхнего века.</p>",
        content_uk="<p>Експрес-ліфтинг радіохвилями: прогріваємо глибокі шари шкіри апаратами <strong>Zemits</strong> з гелями HyaTight. Стимулює колаген та помітно підтягує щоки, овал і зону верхньої повіки.</p>",
        seo_title_de="RF-Lifting Köthen | Hautstraffung Zemits | LILY",
        seo_title_en="RF Lifting Köthen | Skin Tightening Zemits | LILY",
        seo_title_ru="RF-лифтинг Кётен | Подтяжка кожи Zemits | LILY",
        seo_title_uk="RF-ліфтинг Кьотен | Підтяжка шкіри Zemits | LILY",
        seo_desc_de="RF-Lifting mit Zemits in Köthen. Straffe Konturen ohne OP.",
        seo_desc_en="RF lifting with Zemits in Köthen. Firmer contours without surgery.",
        seo_desc_ru="RF-лифтинг на Zemits в Кётене. Подтянутые контуры без операции.",
        seo_desc_uk="RF-ліфтинг на Zemits у Кьотені. Підтягнуті контури без операції.",
    )
)

cosmetology.append(
    make(
        pk=58,
        category=3,
        slug="cosmetology-oxygen-meso",
        order=105,
        name_de="Sauerstoff-Mesotherapie",
        name_en="Oxygen Mesotherapy",
        name_ru="Кислородная мезотерапия",
        name_uk="Киснева мезотерапія",
        price=45.00,
        duration=30,
        duration_info_de="30 Min",
        duration_info_en="30 min",
        duration_info_ru="30 мин",
        duration_info_uk="30 хв",
        description_de="Nicht-invasive Einschleusung von Wirkstoffen mit Sauerstoff.",
        description_en="Non-invasive delivery of active ingredients with oxygen.",
        description_ru="Безинъекционное проникновение активов в кожу потоком кислорода.",
        description_uk="Безін'єкційне проникнення активів у шкіру потоком кисню.",
        content_de="<p>Unter Druck eingeschleuste Sauerstoff-Cocktails mit Hyaluron, Peptiden und Vitaminen. Keine Nadeln — das Gerät schleust die Wirkstoffe über Mikrostrom und Sauerstoffdruck in die Haut.</p>",
        content_en="<p>Pressurised oxygen cocktails with hyaluronic acid, peptides and vitamins. No needles — the device delivers actives via micro-current and oxygen pressure.</p>",
        content_ru="<p>Кислородные коктейли с гиалуроновой кислотой, пептидами и витаминами подаются под давлением. Без игл — аппарат доставляет активы в кожу потоком кислорода и микротоками.</p>",
        content_uk="<p>Кисневі коктейлі з гіалуроновою кислотою, пептидами та вітамінами подаються під тиском. Без голок — апарат доставляє активи в шкіру потоком кисню та мікрострумами.</p>",
        seo_title_de="Sauerstoff-Mesotherapie Köthen | Ohne Nadeln | LILY",
        seo_title_en="Oxygen Mesotherapy Köthen | Needle-Free | LILY",
        seo_title_ru="Кислородная мезотерапия Кётен | Без игл | LILY",
        seo_title_uk="Киснева мезотерапія Кьотен | Без голок | LILY",
        seo_desc_de="Sauerstoff-Mesotherapie ohne Nadeln in Köthen.",
        seo_desc_en="Needle-free oxygen mesotherapy in Köthen.",
        seo_desc_ru="Безинъекционная кислородная мезотерапия в Кётене.",
        seo_desc_uk="Безін'єкційна киснева мезотерапія в Кьотені.",
    )
)

cosmetology.append(
    make(
        pk=59,
        category=3,
        slug="cosmetology-peeling-surface",
        order=72,
        name_de="Oberflächliches Peeling",
        name_en="Superficial Peel",
        name_ru="Поверхностный пилинг",
        name_uk="Поверхневий пілінг",
        price=45.00,
        duration=30,
        duration_info_de="30 Min",
        duration_info_en="30 min",
        duration_info_ru="30 мин",
        duration_info_uk="30 хв",
        description_de="Leichtes Peeling für frischen Teint ohne Ausfallzeit.",
        description_en="Light peel for a fresh complexion with no downtime.",
        description_ru="Лёгкий пилинг для свежего тона без восстановительного периода.",
        description_uk="Легкий пілінг для свіжого тону без відновлювального періоду.",
        content_de="<p>Sanfte Säurekombination, die obere Hautschüppchen löst und den Teint sofort aufhellt. Keine Rötung, Sie können direkt danach zurück in den Alltag.</p>",
        content_en="<p>A gentle acid blend that lifts surface flakes and instantly brightens the complexion. No redness — you can return to daily life right after.</p>",
        content_ru="<p>Мягкая кислотная композиция растворяет поверхностные чешуйки и сразу выравнивает тон. Без красноты — можно возвращаться к делам сразу после процедуры.</p>",
        content_uk="<p>М'яка кислотна композиція розчиняє поверхневі лусочки і одразу вирівнює тон. Без почервонінь — можна повертатися до справ одразу після процедури.</p>",
        seo_title_de="Oberflächliches Peeling Köthen | Express Glow | LILY",
        seo_title_en="Superficial Peel Köthen | Express Glow | LILY",
        seo_title_ru="Поверхностный пилинг Кётен | Экспресс сияние | LILY",
        seo_title_uk="Поверхневий пілінг Кьотен | Експрес сяйво | LILY",
        seo_desc_de="Oberflächliches Peeling für strahlende Haut in Köthen.",
        seo_desc_en="Superficial peel for radiant skin in Köthen.",
        seo_desc_ru="Поверхностный пилинг для сияющей кожи в Кётене.",
        seo_desc_uk="Поверхневий пілінг для сяючої шкіри в Кьотені.",
    )
)

cosmetology.append(
    make(
        pk=60,
        category=3,
        slug="cosmetology-peeling-medium",
        order=74,
        name_de="Mittleres Peeling",
        name_en="Medium Peel",
        name_ru="Срединный пилинг",
        name_uk="Серединний пілінг",
        price=55.00,
        duration=30,
        duration_info_de="30 Min",
        duration_info_en="30 min",
        duration_info_ru="30 мин",
        duration_info_uk="30 хв",
        description_de="Wirksamer Säure-Peel gegen Pigment und feine Falten.",
        description_en="Effective acid peel against pigmentation and fine lines.",
        description_ru="Эффективный кислотный пилинг против пигментации и мелких морщин.",
        description_uk="Ефективний кислотний пілінг проти пігментації та дрібних зморшок.",
        content_de="<p>Kraftvoller, aber kontrollierter Peel für sichtbare Ergebnisse: Pigmentflecken werden heller, die Hautstruktur ebenmäßiger. Nach der Behandlung ist eine leichte Schuppung möglich — das ist Teil der Hauterneuerung.</p>",
        content_en="<p>A powerful yet controlled peel for visible results: pigmentation fades, skin texture becomes more even. Mild flaking after treatment is part of the skin renewal.</p>",
        content_ru="<p>Мощный, но контролируемый пилинг с заметным результатом: пигментация светлеет, текстура кожи выравнивается. После процедуры возможно лёгкое шелушение — это часть обновления кожи.</p>",
        content_uk="<p>Потужний, але контрольований пілінг з помітним результатом: пігментація світлішає, текстура шкіри вирівнюється. Після процедури можливе легке лущення — це частина оновлення шкіри.</p>",
        seo_title_de="Mittleres Peeling Köthen | Anti-Pigment | LILY",
        seo_title_en="Medium Peel Köthen | Anti-Pigment | LILY",
        seo_title_ru="Срединный пилинг Кётен | Анти-пигмент | LILY",
        seo_title_uk="Серединний пілінг Кьотен | Анти-пігмент | LILY",
        seo_desc_de="Mittleres Säurepeeling gegen Pigment und feine Falten in Köthen.",
        seo_desc_en="Medium acid peel against pigmentation and fine lines in Köthen.",
        seo_desc_ru="Срединный кислотный пилинг против пигмента и морщин в Кётене.",
        seo_desc_uk="Серединний кислотний пілінг проти пігменту та зморшок у Кьотені.",
    )
)

cosmetology.append(
    make(
        pk=61,
        category=3,
        slug="cosmetology-alginate-mask",
        order=110,
        name_de="Alginatmaske",
        name_en="Alginate Mask",
        name_ru="Альгинатная маска",
        name_uk="Альгінатна маска",
        price=30.00,
        duration=30,
        duration_info_de="30 Min",
        duration_info_en="30 min",
        duration_info_ru="30 мин",
        duration_info_uk="30 хв",
        description_de="Modellierende Maske aus Meeresalgen für Glow-Effekt.",
        description_en="Modelling seaweed mask for a glow effect.",
        description_ru="Моделирующая маска из морских водорослей с эффектом сияния.",
        description_uk="Моделююча маска з морських водоростей з ефектом сяйва.",
        content_de="<p>Plastifizierende Maske auf Basis von Meeresalgen. Strafft die Haut, modelliert die Konturen und liefert Mineralien direkt in die oberen Schichten. Klassische Abschluss-Pflege bei Gesichts-Protokollen.</p>",
        content_en="<p>Plastifying mask based on seaweed. Tightens the skin, reshapes contours and delivers minerals into the upper layers. A classic finishing step for facial protocols.</p>",
        content_ru="<p>Пластифицирующая маска на основе морских водорослей. Подтягивает кожу, моделирует контуры и доставляет минералы в верхние слои. Классический финальный этап в протоколах ухода за лицом.</p>",
        content_uk="<p>Пластифікуюча маска на основі морських водоростей. Підтягує шкіру, моделює контури та доставляє мінерали у верхні шари. Класичний фінальний етап у протоколах догляду за обличчям.</p>",
        seo_title_de="Alginatmaske Köthen | Modellierende Pflege | LILY",
        seo_title_en="Alginate Mask Köthen | Modelling Care | LILY",
        seo_title_ru="Альгинатная маска Кётен | Моделирующий уход | LILY",
        seo_title_uk="Альгінатна маска Кьотен | Моделюючий догляд | LILY",
        seo_desc_de="Alginatmaske für straffe und strahlende Haut in Köthen.",
        seo_desc_en="Alginate mask for firm, glowing skin in Köthen.",
        seo_desc_ru="Альгинатная маска для упругой и сияющей кожи в Кётене.",
        seo_desc_uk="Альгінатна маска для пружної та сяючої шкіри в Кьотені.",
    )
)

cosmetology.append(
    make(
        pk=62,
        category=3,
        slug="cosmetology-face-massage",
        order=115,
        name_de="Gesichtsmassage",
        name_en="Facial Massage",
        name_ru="Массаж лица",
        name_uk="Масаж обличчя",
        price=30.00,
        duration=30,
        duration_info_de="30 Min",
        duration_info_en="30 min",
        duration_info_ru="30 мин",
        duration_info_uk="30 хв",
        description_de="Klassische Gesichtsmassage gegen Schwellungen und Müdigkeit.",
        description_en="Classic facial massage for puffiness and fatigue.",
        description_ru="Классический массаж лица против отёчности и усталости.",
        description_uk="Класичний масаж обличчя проти набряклості та втоми.",
        content_de="<p>Handmassage für Gesicht, Hals und Dekolleté. Fördert Lymphdrainage, mindert Schwellungen, entspannt mimische Falten und verleiht der Haut einen frischen, erholten Look.</p>",
        content_en="<p>Manual massage for face, neck and décolleté. Boosts lymphatic drainage, reduces puffiness, relaxes expression lines and gives the skin a fresh, rested look.</p>",
        content_ru="<p>Ручной массаж лица, шеи и декольте. Активирует лимфоток, убирает отёки, расслабляет мимические морщины и дарит коже свежий, отдохнувший вид.</p>",
        content_uk="<p>Ручний масаж обличчя, шиї та декольте. Активує лімфоток, прибирає набряки, розслаблює мімічні зморшки та дарує шкірі свіжий, відпочилий вигляд.</p>",
        seo_title_de="Gesichtsmassage Köthen | Lymphdrainage | LILY",
        seo_title_en="Facial Massage Köthen | Lymphatic Drainage | LILY",
        seo_title_ru="Массаж лица Кётен | Лимфодренаж | LILY",
        seo_title_uk="Масаж обличчя Кьотен | Лімфодренаж | LILY",
        seo_desc_de="Manuelle Gesichtsmassage gegen Schwellungen in Köthen.",
        seo_desc_en="Manual facial massage against puffiness in Köthen.",
        seo_desc_ru="Ручной массаж лица против отёчности в Кётене.",
        seo_desc_uk="Ручний масаж обличчя проти набряклості в Кьотені.",
    )
)

cosmetology.append(
    make(
        pk=63,
        category=3,
        slug="cosmetology-back-cleansing",
        order=120,
        name_de="Rückenreinigung",
        name_en="Back Cleansing",
        name_ru="Чистка спины",
        name_uk="Чистка спини",
        price=90.00,
        duration=60,
        duration_info_de="60 Min",
        duration_info_en="60 min",
        duration_info_ru="60 мин",
        duration_info_uk="60 хв",
        description_de="Tiefenreinigung der Rückenhaut — gegen Akne am Körper.",
        description_en="Deep cleansing of the back — for body acne.",
        description_ru="Глубокая чистка спины — против акне на теле.",
        description_uk="Глибока чистка спини — проти акне на тілі.",
        content_de="<p>Der Rücken ist oft schwerer zu pflegen als das Gesicht. Wir nutzen professionelle Peelings und manuelle Reinigung, um Poren zu befreien und Entzündungen sichtbar zu reduzieren. Abschließend beruhigende Masken.</p>",
        content_en="<p>The back is often harder to care for than the face. We use professional peels and manual cleansing to clear pores and visibly reduce inflammation. Soothing masks finish the treatment.</p>",
        content_ru="<p>Спина зачастую сложнее в уходе, чем лицо. Используем профессиональные пилинги и мануальную чистку, чтобы освободить поры и заметно уменьшить воспаления. В финале — успокаивающие маски.</p>",
        content_uk="<p>Спина часто складніша в догляді, ніж обличчя. Використовуємо професійні пілінги та мануальну чистку, щоб звільнити пори та помітно зменшити запалення. У фіналі — заспокійливі маски.</p>",
        seo_title_de="Rückenreinigung Köthen | Body Cleansing | LILY",
        seo_title_en="Back Cleansing Köthen | Body Acne Care | LILY",
        seo_title_ru="Чистка спины Кётен | Уход за телом | LILY",
        seo_title_uk="Чистка спини Кьотен | Догляд за тілом | LILY",
        seo_desc_de="Professionelle Rückenreinigung gegen Körperakne in Köthen.",
        seo_desc_en="Professional back cleansing against body acne in Köthen.",
        seo_desc_ru="Профессиональная чистка спины против акне тела в Кётене.",
        seo_desc_uk="Професійна чистка спини проти акне тіла в Кьотені.",
    )
)

cosmetology.append(
    make(
        pk=64,
        category=3,
        slug="cosmetology-mens-facial",
        order=125,
        name_de="Sauberes Gesicht für Männer",
        name_en="Men's Clean Skin Facial",
        name_ru="Чистое лицо для мужчин",
        name_uk="Чиста шкіра для чоловіків",
        price=80.00,
        duration=30,
        duration_info_de="30 Min",
        duration_info_en="30 min",
        duration_info_ru="30 мин",
        duration_info_uk="30 хв",
        description_de="Gezielte Gesichtsreinigung für Männerhaut.",
        description_en="Targeted facial cleansing for men's skin.",
        description_ru="Целевая чистка лица для мужской кожи.",
        description_uk="Цільова чистка обличчя для чоловічої шкіри.",
        content_de="<p>Schnelle, aber gründliche Gesichtsreinigung, abgestimmt auf die Besonderheiten der Männerhaut: dickere Struktur, stärkere Talgproduktion, Reizungen nach der Rasur. Wir reinigen die Poren und beruhigen die Haut.</p>",
        content_en="<p>Fast yet thorough facial cleansing tailored to men's skin: denser texture, higher sebum production, post-shave irritation. We clear pores and calm the skin.</p>",
        content_ru="<p>Быстрая, но тщательная чистка с учётом особенностей мужской кожи: более плотная структура, активная работа сальных желёз, раздражения после бритья. Очищаем поры и успокаиваем кожу.</p>",
        content_uk="<p>Швидка, але ретельна чистка з урахуванням особливостей чоловічої шкіри: щільніша структура, активна робота сальних залоз, подразнення після гоління. Очищуємо пори та заспокоюємо шкіру.</p>",
        seo_title_de="Gesichtsreinigung Männer Köthen | Men's Facial | LILY",
        seo_title_en="Men's Facial Cleansing Köthen | LILY",
        seo_title_ru="Чистка лица мужская Кётен | Men's Facial | LILY",
        seo_title_uk="Чистка обличчя чоловіча Кьотен | Men's Facial | LILY",
        seo_desc_de="Professionelle Gesichtsreinigung speziell für Männer in Köthen.",
        seo_desc_en="Professional facial cleansing for men in Köthen.",
        seo_desc_ru="Профессиональная мужская чистка лица в Кётене.",
        seo_desc_uk="Професійна чоловіча чистка обличчя в Кьотені.",
    )
)

# ===================== BROWS & LASHES (cat=4) =====================
brows_lashes = []
# Existing with fixes (pk=21 REMOVED)
e = deepcopy(existing[13])  # Augenbrauen Arch & Farbe
e["fields"]["duration"] = 30  # was 45
brows_lashes.append(e)

e = deepcopy(existing[14])  # Augenbrauenlaminierung
e["fields"]["duration"] = 60  # was 50
brows_lashes.append(e)

e = deepcopy(existing[15])  # Wimpernlaminierung
e["fields"]["duration"] = 60  # was 50
brows_lashes.append(e)

brows_lashes.append(deepcopy(existing[16]))  # Klassik 1D (90min €50)

e = deepcopy(existing[17])  # 2D-3D
e["fields"]["duration"] = 90  # was 120
e["fields"]["price"] = "75.00"  # was 70
brows_lashes.append(e)

e = deepcopy(existing[18])  # 4D-6D
e["fields"]["duration"] = 120  # was 180
brows_lashes.append(e)

brows_lashes.append(deepcopy(existing[19]))  # Wimpern entfernen

e = deepcopy(existing[20])  # Korrektur
e["fields"]["price"] = "60.00"  # was 30
brows_lashes.append(e)

# New: Effektzuschlag (addon)
brows_lashes.append(
    make(
        pk=46,
        category=4,
        slug="lashes-effect-surcharge",
        order=100,
        name_de="Effektzuschlag",
        name_en="Effect Surcharge",
        name_ru="Доплата за эффект",
        name_uk="Доплата за ефект",
        price=15.00,
        duration=5,
        duration_info_de="5 Min",
        duration_info_en="5 min",
        duration_info_ru="5 мин",
        duration_info_uk="5 хв",
        description_de="Aufpreis für Spezial-Effekte (Farbe, Mix).",
        description_en="Surcharge for special effects (colour, mix).",
        description_ru="Доплата за спецэффекты (цвет, микс).",
        description_uk="Доплата за спецефекти (колір, мікс).",
        content_de="<p>Zubuchung zu einer Wimpernverlängerung: farbige Akzente, Strasssteine, ungewöhnliche Mix-Techniken oder besondere Schwünge. Wählen Sie diese Option ergänzend zur Hauptleistung.</p>",
        content_en="<p>Add-on to a lash extension: colour accents, rhinestones, unusual mix techniques or special curls. Choose it in addition to the main service.</p>",
        content_ru="<p>Доплата к наращиванию ресниц: цветные акценты, стразы, необычные миксы или особый изгиб. Выбирается дополнительно к основной процедуре.</p>",
        content_uk="<p>Доплата до нарощування вій: кольорові акценти, стрази, незвичні мікси або особливий вигин. Обирається додатково до основної процедури.</p>",
        seo_title_de="Effektzuschlag Wimpern Köthen | Extras | LILY",
        seo_title_en="Lash Effect Surcharge Köthen | Extras | LILY",
        seo_title_ru="Доплата за эффект Кётен | Ресницы | LILY",
        seo_title_uk="Доплата за ефект Кьотен | Вії | LILY",
        seo_desc_de="Zubuchbare Effekte bei Wimpernverlängerung in Köthen.",
        seo_desc_en="Add-on effects for lash extensions in Köthen.",
        seo_desc_ru="Дополнительные эффекты к наращиванию ресниц в Кётене.",
        seo_desc_uk="Додаткові ефекти до нарощування вій у Кьотені.",
        is_addon=True,
    )
)

# ===================== MASSAGE (cat=5) =====================
massage = []
# Existing with fixes
e = deepcopy(existing[29])  # Ganzkörper classic
e["fields"]["price"] = "50.00"  # was 60 — old list says 50
massage.append(e)
massage.append(deepcopy(existing[30]))  # Rückenmassage €35/30
e = deepcopy(existing[31])  # Relax
e["fields"]["duration"] = 30  # was 60
e["fields"]["price"] = "35.00"  # was 60
massage.append(e)
massage.append(deepcopy(existing[32]))  # Anti-cellulite full €60/60 — keep as premium
massage.append(deepcopy(existing[33]))  # Anti-cellulite legs & po €35/30
massage.append(deepcopy(existing[34]))  # Custom zone €35/30

# New zone-based massages
massage.append(
    make(
        pk=47,
        category=5,
        slug="massage-legs-zone",
        order=40,
        name_de="Beinmassage",
        name_en="Legs Massage",
        name_ru="Массаж ног",
        name_uk="Масаж ніг",
        price=35.00,
        duration=30,
        duration_info_de="30 Min",
        duration_info_en="30 min",
        duration_info_ru="30 мин",
        duration_info_uk="30 хв",
        description_de="Zonenmassage für müde, schwere Beine.",
        description_en="Zonal massage for tired, heavy legs.",
        description_ru="Зональный массаж для уставших, тяжёлых ног.",
        description_uk="Зональний масаж для втомлених, важких ніг.",
        content_de="<p>Klassische Technik mit Betonung auf Waden und Oberschenkel. Lymphdrainage-Elemente lösen Schwellungen, entspannen die Muskeln und verbessern die Mikrozirkulation.</p>",
        content_en="<p>Classic technique focused on calves and thighs. Lymphatic-drainage elements relieve puffiness, relax muscles and improve micro-circulation.</p>",
        content_ru="<p>Классическая техника с акцентом на икры и бёдра. Элементы лимфодренажа снимают отёки, расслабляют мышцы и улучшают микроциркуляцию.</p>",
        content_uk="<p>Класична техніка з акцентом на литки та стегна. Елементи лімфодренажу знімають набряки, розслабляють м'язи та покращують мікроциркуляцію.</p>",
        seo_title_de="Beinmassage Köthen | Entspannung & Lymphe | LILY",
        seo_title_en="Legs Massage Köthen | Relaxation & Lymph | LILY",
        seo_title_ru="Массаж ног Кётен | Релакс и лимфа | LILY",
        seo_title_uk="Масаж ніг Кьотен | Релакс і лімфа | LILY",
        seo_desc_de="Entspannende Beinmassage mit Lymphdrainage-Elementen in Köthen.",
        seo_desc_en="Relaxing legs massage with lymph drainage elements in Köthen.",
        seo_desc_ru="Расслабляющий массаж ног с элементами лимфодренажа в Кётене.",
        seo_desc_uk="Розслабляючий масаж ніг з елементами лімфодренажу в Кьотені.",
    )
)

massage.append(
    make(
        pk=48,
        category=5,
        slug="massage-hips-zone",
        order=50,
        name_de="Hüftmassage",
        name_en="Hips Massage",
        name_ru="Массаж бёдер",
        name_uk="Масаж стегон",
        price=35.00,
        duration=30,
        duration_info_de="30 Min",
        duration_info_en="30 min",
        duration_info_ru="30 мин",
        duration_info_uk="30 хв",
        description_de="Intensive Zonenmassage für Oberschenkel und Hüfte.",
        description_en="Intense zonal massage for thighs and hips.",
        description_ru="Интенсивный зональный массаж бёдер и ягодиц.",
        description_uk="Інтенсивний зональний масаж стегон та сідниць.",
        content_de="<p>Prägnante Massage der Hüftzone: löst Spannungen, bekämpft Cellulite-Anzeichen und bringt die Haut in Topform. Kombinierbar mit Anti-Cellulite-Techniken.</p>",
        content_en="<p>A focused hips-zone massage: relieves tension, targets early cellulite signs and tones the skin. Can be combined with anti-cellulite techniques.</p>",
        content_ru="<p>Точечный массаж зоны бёдер: снимает напряжение, работает с ранними признаками целлюлита и тонизирует кожу. Комбинируется с антицеллюлитными техниками.</p>",
        content_uk="<p>Точковий масаж зони стегон: знімає напругу, працює з ранніми ознаками целюліту та тонізує шкіру. Комбінується з антицелюлітними техніками.</p>",
        seo_title_de="Hüftmassage Köthen | Anti-Cellulite | LILY",
        seo_title_en="Hips Massage Köthen | Anti-Cellulite | LILY",
        seo_title_ru="Массаж бёдер Кётен | Антицеллюлит | LILY",
        seo_title_uk="Масаж стегон Кьотен | Антицелюліт | LILY",
        seo_desc_de="Hüftmassage in Köthen — gegen Cellulite und Spannungen.",
        seo_desc_en="Hips massage in Köthen — against cellulite and tension.",
        seo_desc_ru="Массаж бёдер в Кётене — против целлюлита и зажимов.",
        seo_desc_uk="Масаж стегон у Кьотені — проти целюліту та затискань.",
    )
)

massage.append(
    make(
        pk=49,
        category=5,
        slug="massage-belly-zone",
        order=60,
        name_de="Bauchmassage",
        name_en="Belly Massage",
        name_ru="Массаж живота",
        name_uk="Масаж живота",
        price=35.00,
        duration=30,
        duration_info_de="30 Min",
        duration_info_en="30 min",
        duration_info_ru="30 мин",
        duration_info_uk="30 хв",
        description_de="Sanfte Bauchmassage für Entspannung und Körperformung.",
        description_en="Gentle belly massage for relaxation and body shaping.",
        description_ru="Мягкий массаж живота для релакса и моделирования.",
        description_uk="М'який масаж живота для релаксу та моделювання.",
        content_de="<p>Massage der Bauchzone mit sanften Knet- und Streichtechniken. Fördert die Darmtätigkeit, reduziert Aufblähung und formt sichtbar die Silhouette.</p>",
        content_en="<p>Belly-zone massage with gentle kneading and stroking techniques. Stimulates digestion, reduces bloating and visibly reshapes the silhouette.</p>",
        content_ru="<p>Массаж зоны живота с мягкими разминающими и поглаживающими техниками. Активирует работу ЖКТ, уменьшает вздутие и заметно моделирует силуэт.</p>",
        content_uk="<p>Масаж зони живота з м'якими розминальними та погладжувальними техніками. Активує роботу ШКТ, зменшує здуття та помітно моделює силует.</p>",
        seo_title_de="Bauchmassage Köthen | Body Shaping | LILY",
        seo_title_en="Belly Massage Köthen | Body Shaping | LILY",
        seo_title_ru="Массаж живота Кётен | Моделирование | LILY",
        seo_title_uk="Масаж живота Кьотен | Моделювання | LILY",
        seo_desc_de="Bauchmassage zur Entspannung und Körperformung in Köthen.",
        seo_desc_en="Belly massage for relaxation and body shaping in Köthen.",
        seo_desc_ru="Массаж живота для релакса и моделирования в Кётене.",
        seo_desc_uk="Масаж живота для релаксу та моделювання в Кьотені.",
    )
)

# ===================== DEPILATION (cat=6) =====================
# Strategy: add "(Damen)" / "(Herren)" to DE names, parallel in all languages.
# Slugs: depilation-w-* and depilation-m-*.
# Order: 100-199 women, 200-299 men.
# pk=39 (package) REMOVED entirely.
depilation = []


# Existing: rename to include gender marker, adjust durations, re-slug
def relabel(
    pk_src,
    *,
    slug,
    order,
    name_de,
    name_en,
    name_ru,
    name_uk,
    duration=None,
    price=None,
    duration_info_de=None,
    duration_info_en=None,
    duration_info_ru=None,
    duration_info_uk=None,
):
    e = deepcopy(existing[pk_src])
    f = e["fields"]
    f["slug"] = slug
    f["order"] = order
    f["name"] = name_de
    f["name_de"] = name_de
    f["name_en"] = name_en
    f["name_ru"] = name_ru
    f["name_uk"] = name_uk
    if duration is not None:
        f["duration"] = duration
    if price is not None:
        f["price"] = f"{price:.2f}"
    if duration_info_de is not None:
        f["duration_info"] = duration_info_de
        f["duration_info_de"] = duration_info_de
        f["duration_info_en"] = duration_info_en
        f["duration_info_ru"] = duration_info_ru
        f["duration_info_uk"] = duration_info_uk
    return e


# pk=35 Oberlippe — Damen, duration 15 -> 10
depilation.append(
    relabel(
        35,
        slug="depilation-w-upper-lip",
        order=100,
        name_de="Damendepilation — Oberlippe",
        name_en="Depilation (women) — Upper lip",
        name_ru="Депиляция (женская) — Верхняя губа",
        name_uk="Депіляція жіноча — Верхня губа",
        duration=10,
        duration_info_de="10 Min",
        duration_info_en="10 min",
        duration_info_ru="10 мин",
        duration_info_uk="10 хв",
    )
)
# pk=36 Achseln — Damen
depilation.append(
    relabel(
        36,
        slug="depilation-w-axilla",
        order=110,
        name_de="Damendepilation — Achselhöhlen",
        name_en="Depilation (women) — Armpits",
        name_ru="Депиляция (женская) — Подмышки",
        name_uk="Депіляція жіноча — Пахви",
    )
)
# pk=37 Bikini Klassik — Damen, duration 30 -> 45
depilation.append(
    relabel(
        37,
        slug="depilation-w-bikini-classic",
        order=170,
        name_de="Damendepilation — Klassischer Bikini",
        name_en="Depilation (women) — Classic bikini",
        name_ru="Депиляция (женская) — Классическое бикини",
        name_uk="Депіляція жіноча — Класичне бікіні",
        duration=45,
        duration_info_de="45 Min",
        duration_info_en="45 min",
        duration_info_ru="45 мин",
        duration_info_uk="45 хв",
    )
)
# pk=38 Bikini Hollywood — Damen, duration 45 -> 60
depilation.append(
    relabel(
        38,
        slug="depilation-w-bikini-hollywood",
        order=180,
        name_de="Damendepilation — Brasilianischer Bikini",
        name_en="Depilation (women) — Brazilian bikini",
        name_ru="Депиляция (женская) — Глубокое бикини",
        name_uk="Депіляція жіноча — Глибоке бікіні",
        duration=60,
        duration_info_de="60 Min",
        duration_info_en="60 min",
        duration_info_ru="60 мин",
        duration_info_uk="60 хв",
    )
)
# pk=40 Rücken Herren, duration 45 -> 25
depilation.append(
    relabel(
        40,
        slug="depilation-m-back",
        order=240,
        name_de="Herrendepilation — Rücken",
        name_en="Depilation (men) — Back",
        name_ru="Депиляция (мужская) — Спина",
        name_uk="Депіляція чоловіча — Спина",
        duration=25,
        duration_info_de="25 Min",
        duration_info_en="25 min",
        duration_info_ru="25 мин",
        duration_info_uk="25 хв",
    )
)


# New depilation services — women (pk 70-77)
def dep_new(pk, *, slug, order, gender, zone_de, zone_en, zone_ru, zone_uk, price, duration):
    prefix_de = "Damendepilation" if gender == "w" else "Herrendepilation"
    prefix_en = "Depilation (women)" if gender == "w" else "Depilation (men)"
    prefix_ru = "Депиляция (женская)" if gender == "w" else "Депиляция (мужская)"
    prefix_uk = "Депіляція жіноча" if gender == "w" else "Депіляція чоловіча"
    # dur_str not used in make() currently
    return make(
        pk=pk,
        category=6,
        slug=slug,
        order=order,
        name_de=f"{prefix_de} — {zone_de}",
        name_en=f"{prefix_en} — {zone_en}",
        name_ru=f"{prefix_ru} — {zone_ru}",
        name_uk=f"{prefix_uk} — {zone_uk}",
        price=price,
        duration=duration,
        duration_info_de=f"{duration} Min",
        duration_info_en=f"{duration} min",
        duration_info_ru=f"{duration} мин",
        duration_info_uk=f"{duration} хв",
        description_de=f"Sanfte Haarentfernung Zone '{zone_de}' mit Wachs oder Zuckerpaste.",
        description_en=f"Gentle hair removal in the '{zone_en}' zone with wax or sugar paste.",
        description_ru=f"Бережное удаление волос в зоне «{zone_ru}» воском или шугарингом.",
        description_uk=f"Дбайливе видалення волосся у зоні «{zone_uk}» воском або шугарингом.",
        content_de=f"<p>Haarentfernung der Zone '{zone_de}' mit Premium-Wachs <strong>Italwax</strong> oder Zuckerpaste <strong>Enova</strong>. Wir wählen die schonendste Methode für Ihren Hauttyp und pflegen die Haut abschließend mit beruhigenden Lotionen.</p>",
        content_en=f"<p>Hair removal in the '{zone_en}' zone using premium <strong>Italwax</strong> wax or <strong>Enova</strong> sugar paste. We choose the gentlest method for your skin type and finish with soothing lotions.</p>",
        content_ru=f"<p>Удаление волос в зоне «{zone_ru}» премиальным воском <strong>Italwax</strong> или сахарной пастой <strong>Enova</strong>. Подбираем самый деликатный метод под ваш тип кожи и завершаем процедуру успокаивающими лосьонами.</p>",
        content_uk=f"<p>Видалення волосся у зоні «{zone_uk}» преміальним воском <strong>Italwax</strong> або цукровою пастою <strong>Enova</strong>. Підбираємо найбільш делікатний метод під ваш тип шкіри та завершуємо процедуру заспокійливими лосьйонами.</p>",
        seo_title_de=f"{prefix_de} {zone_de} Köthen | LILY",
        seo_title_en=f"{prefix_en} — {zone_en} Köthen | LILY",
        seo_title_ru=f"{prefix_ru} — {zone_ru} Кётен | LILY",
        seo_title_uk=f"{prefix_uk} — {zone_uk} Кьотен | LILY",
        seo_desc_de=f"Haarentfernung {zone_de} in Köthen. Italwax & Enova.",
        seo_desc_en=f"Hair removal — {zone_en} in Köthen. Italwax & Enova.",
        seo_desc_ru=f"Депиляция {zone_ru} в Кётене. Italwax и Enova.",
        seo_desc_uk=f"Депіляція {zone_uk} у Кьотені. Italwax та Enova.",
    )


# Women — new
depilation.append(
    dep_new(
        70,
        slug="depilation-w-face",
        order=105,
        gender="w",
        zone_de="Gesichtsbereich",
        zone_en="Face area",
        zone_ru="Зона лица",
        zone_uk="Зона обличчя",
        price=10.00,
        duration=15,
    )
)
depilation.append(
    dep_new(
        71,
        slug="depilation-w-forearm",
        order=120,
        gender="w",
        zone_de="Unterarm",
        zone_en="Forearm",
        zone_ru="Руки до локтя",
        zone_uk="Руки до ліктя",
        price=15.00,
        duration=15,
    )
)
depilation.append(
    dep_new(
        72,
        slug="depilation-w-arms-full",
        order=125,
        gender="w",
        zone_de="Arme vollständig",
        zone_en="Full arms",
        zone_ru="Руки полностью",
        zone_uk="Руки повністю",
        price=20.00,
        duration=25,
    )
)
depilation.append(
    dep_new(
        73,
        slug="depilation-w-belly",
        order=130,
        gender="w",
        zone_de="Bauch",
        zone_en="Belly",
        zone_ru="Живот",
        zone_uk="Живіт",
        price=10.00,
        duration=15,
    )
)
depilation.append(
    dep_new(
        74,
        slug="depilation-w-lower-legs",
        order=140,
        gender="w",
        zone_de="Unterschenkel",
        zone_en="Lower legs",
        zone_ru="Голени",
        zone_uk="Гомілки",
        price=15.00,
        duration=30,
    )
)
depilation.append(
    dep_new(
        75,
        slug="depilation-w-legs-full",
        order=150,
        gender="w",
        zone_de="Beine vollständig",
        zone_en="Full legs",
        zone_ru="Ноги полностью",
        zone_uk="Ноги повністю",
        price=35.00,
        duration=45,
    )
)
depilation.append(
    dep_new(
        76,
        slug="depilation-w-hips",
        order=160,
        gender="w",
        zone_de="Hüften",
        zone_en="Hips",
        zone_ru="Бёдра",
        zone_uk="Стегна",
        price=20.00,
        duration=30,
    )
)

# Men — new
depilation.append(
    dep_new(
        77,
        slug="depilation-m-axilla",
        order=210,
        gender="m",
        zone_de="Achselhöhlen",
        zone_en="Armpits",
        zone_ru="Подмышки",
        zone_uk="Пахви",
        price=15.00,
        duration=15,
    )
)
depilation.append(
    dep_new(
        78,
        slug="depilation-m-shoulders",
        order=220,
        gender="m",
        zone_de="Schultern",
        zone_en="Shoulders",
        zone_ru="Плечи",
        zone_uk="Плечі",
        price=30.00,
        duration=15,
    )
)
depilation.append(
    dep_new(
        79,
        slug="depilation-m-chest-belly",
        order=230,
        gender="m",
        zone_de="Brust & Bauch",
        zone_en="Chest & Belly",
        zone_ru="Грудь и живот",
        zone_uk="Груди та живіт",
        price=35.00,
        duration=20,
    )
)
depilation.append(
    dep_new(
        80,
        slug="depilation-m-buttocks",
        order=250,
        gender="m",
        zone_de="Pobacken",
        zone_en="Buttocks",
        zone_ru="Ягодицы",
        zone_uk="Сідниці",
        price=20.00,
        duration=20,
    )
)
depilation.append(
    dep_new(
        81,
        slug="depilation-m-bikini-brazilian",
        order=260,
        gender="m",
        zone_de="Brasilianischer Bikini",
        zone_en="Brazilian bikini",
        zone_ru="Глубокое бикини",
        zone_uk="Глибоке бікіні",
        price=50.00,
        duration=30,
    )
)

# ===================== WRITE FILES =====================
files = {
    "services_hair.json": hair,
    "services_nails.json": nails,
    "services_pedicure.json": pedicure,
    "services_cosmetology.json": cosmetology,
    "services_brows_lashes.json": brows_lashes,
    "services_massage.json": massage,
    "services_depilation.json": depilation,
}

for fname, items in files.items():
    out = SERVICE_DIR / fname
    with open(out, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print(f"Wrote {out} ({len(items)} services)")

# ===================== CONFLICT RULES =====================
# Reload conflict rules and drop any rule that references pk=21 (removed) or pk=39 (removed).
# Add rules for new cosmetology services so they replace each other and existing 22-28.
with open(FX / "conflict_rules.json", encoding="utf-8") as f:
    rules = json.load(f)

removed_pks = {21, 39}
filtered = [r for r in rules if r["fields"]["source"] not in removed_pks and r["fields"]["target"] not in removed_pks]

# Next pk for new rules
next_pk = max(r["pk"] for r in filtered) + 1 if filtered else 1

# Cosmetology: all pairs among {22,23,24,25,26,28,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64} replace each other.
# NOTE: pk=27 (Kryotherapie 30min) excluded (existing rules already excluded it — short/addon-like).
cosmo_ids = [22, 23, 24, 25, 26, 28, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 62, 63, 64]
# We include facial procedures that truly conflict (can't do 2 at same time). 61 Alginate and 57 RF exclude — Alginate is a mask finisher, RF is express.
existing_pairs = set()
for r in filtered:
    if r["fields"]["source"] in cosmo_ids and r["fields"]["target"] in cosmo_ids:
        existing_pairs.add((r["fields"]["source"], r["fields"]["target"]))

for _, s in enumerate(cosmo_ids):
    for t in cosmo_ids:
        if s == t:
            continue
        if (s, t) in existing_pairs:
            continue
        filtered.append(
            {
                "model": "main.serviceconflictrule",
                "pk": next_pk,
                "fields": {"source": s, "target": t, "rule_type": "replaces", "is_active": True, "note": "cosmo-auto"},
            }
        )
        next_pk += 1

# New 4-6D (pk=45) should replace all manicure/extension pks 5-10, 41
ext_ids = [5, 6, 7, 8, 9, 10, 41, 45]
ext_pairs = set()
for r in filtered:
    if r["fields"]["source"] in ext_ids and r["fields"]["target"] in ext_ids:
        ext_pairs.add((r["fields"]["source"], r["fields"]["target"]))
for s in ext_ids:
    for t in ext_ids:
        if s == t or (s, t) in ext_pairs:
            continue
        # Only add rules involving pk=45 (others already exist)
        if 45 not in (s, t):
            continue
        filtered.append(
            {
                "model": "main.serviceconflictrule",
                "pk": next_pk,
                "fields": {
                    "source": s,
                    "target": t,
                    "rule_type": "replaces",
                    "is_active": True,
                    "note": "nails-46-auto",
                },
            }
        )
        next_pk += 1

# Depilation: classic <-> hollywood women
# Existing rules pk=81,82 were for pk=37<->38. After pk=39 removed, keep 37<->38.
# Also add men classic bikini logic? No — men only has brazilian (pk=81 new). Skip.

with open(FX / "conflict_rules.json", "w", encoding="utf-8") as f:
    json.dump(filtered, f, ensure_ascii=False, indent=2)
print(f"Wrote conflict_rules.json ({len(filtered)} rules)")

# ===================== Clear old monolithic services.json =====================
# Replace with just servicecategory entries — still needed? No, categories is separate.
# We'll leave just an empty array to avoid breakage if something still loads it.
with open(FX / "services.json", "w", encoding="utf-8") as f:
    json.dump([], f, ensure_ascii=False, indent=2)
print("Cleared services.json (now empty array)")

total = sum(len(v) for v in files.values())
print(f"\nTotal services across all new files: {total}")
