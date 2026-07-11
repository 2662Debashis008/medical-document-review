import difflib
from typing import Any

COMMON_MEDICINES = [
    # Analgesics & Anti-inflammatories
    "Paracetamol", "Acetaminophen", "Ibuprofen", "Diclofenac", "Aceclofenac",
    "Tramadol", "Ketorolac", "Mefenamic Acid", "Naproxen", "Aspirin", "Nimesulide",
    # Antibiotics & Antifungals
    "Amoxicillin", "Augmentin", "Clavulanate", "Azithromycin", "Ciprofloxacin",
    "Levofloxacin", "Ofloxacin", "Cefixime", "Cefuroxime", "Ceftriaxone",
    "Doxycycline", "Metronidazole", "Fluconazole", "Itraconazole",
    # Gastrointestinal
    "Pantoprazole", "Omeprazole", "Rabeprazole", "Esomeprazole", "Ranitidine",
    "Famotidine", "Domperidone", "Ondansetron", "Metoclopramide", "Loperamide",
    "Sucralfate", "Pancreatin", "Pan-D", "Pantocid", "Spasmonil",
    # Cardiovascular & Antidiabetics
    "Metformin", "Glimepiride", "Teneligliptin", "Atorvastatin", "Rosuvastatin",
    "Amlodipine", "Telmisartan", "Losartan", "Ramipril", "Enalapril", "Metoprolol",
    "Atenolol", "Clopidogrel", "Aspisol",
    # Respiratory & Anti-allergics
    "Montelukast", "Levocetirizine", "Cetirizine", "Bilastine", "Fexofenadine",
    "Phenylephrine", "Ambroxol", "Guaiphenesin", "Dextromethorphan", "Salbutamol",
    "Levosalbutamol", "Ipratropium", "Budecort", "Duolin", "Ascoril", "Solvin Cold",
    # Vitamins & Supplements
    "Calcium", "Vitamin D3", "Methylcobalamin", "Vitamin B12", "Folic Acid",
    "Iron", "Zinc", "Limcee", "A to Z", "Becosules", "Neurobion Forte",
    # Others / Neuro & Anticoagulants
    "Gabapentin", "Pregabalin", "Levothyroxine", "Alprazolam", "Clonazepam",
    "Atarax", "Voveran", "Combiflam", "O2", "Norflox TZ", "Sildenafil",
]

ABBREVIATION_EXPANSIONS = {
    "od": "once daily",
    "bd": "twice daily",
    "tds": "three times daily",
    "tid": "three times daily",
    "qid": "four times daily",
    "hs": "at bedtime",
    "ac": "before meals",
    "pc": "after meals",
    "sos": "as needed",
    "prn": "as needed",
    "stat": "immediately",
}

ROUTE_EXPANSIONS = {
    "po": "oral",
    "iv": "intravenous",
    "im": "intramuscular",
    "sc": "subcutaneous",
    "topical": "apply on skin",
}


class MedicineValidationService:
    @staticmethod
    def validate_and_correct_medicine(name: str | None) -> str | None:
        if not name:
            return name
        name_clean = name.strip()
        if not name_clean or name_clean.lower() == "unknown":
            return name_clean

        # Attempt to match parts of combined drug names (e.g. "Paracetamol + Domperidone")
        parts = [p.strip() for p in name_clean.split("+")]
        corrected_parts = []
        for part in parts:
            # Look for close matches
            matches = difflib.get_close_matches(part, COMMON_MEDICINES, n=1, cutoff=0.8)
            if matches:
                corrected_parts.append(matches[0])
            else:
                # Fall back to capitalized original part
                corrected_parts.append(part.capitalize())

        return " + ".join(corrected_parts)

    @staticmethod
    def expand_frequency(freq: str | None) -> str | None:
        if not freq:
            return freq
        freq_lower = freq.strip().lower()
        return ABBREVIATION_EXPANSIONS.get(freq_lower, freq)

    @staticmethod
    def expand_route(route: str | None) -> str | None:
        if not route:
            return route
        route_lower = route.strip().lower()
        return ROUTE_EXPANSIONS.get(route_lower, route)
