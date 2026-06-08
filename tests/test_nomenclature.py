"""
Тестове за pif_engine/nomenclature.py
"""
import pytest
from pif_engine.nomenclature import (
    canonical_inci,
    declarable_name,
    is_declarable,
    localize_inci,
    validate_inci,
    DECLARABLE_ALLERGENS,
)
from pif_engine import build_product, generate_inci


# ---------------------------------------------------------------------------
# canonical_inci
# ---------------------------------------------------------------------------

class TestCanonicalInci:
    def test_synonym_water(self):
        assert canonical_inci("water") == "Aqua"
        assert canonical_inci("Water") == "Aqua"
        assert canonical_inci("WATER") == "Aqua"

    def test_synonym_eau(self):
        assert canonical_inci("eau") == "Aqua"

    def test_synonym_fragrance(self):
        assert canonical_inci("fragrance") == "Parfum"
        assert canonical_inci("parfum/aroma") == "Parfum"

    def test_synonym_sunflower_oil(self):
        assert canonical_inci("sunflower oil") == "Helianthus Annuus Seed Oil"
        assert canonical_inci("sunflower seed oil") == "Helianthus Annuus Seed Oil"

    def test_synonym_bht(self):
        assert canonical_inci("butylhydroxytoluol") == "BHT"
        assert canonical_inci("butylated hydroxytoluene") == "BHT"

    def test_acronym_uppercase(self):
        # PEG, PPG, EDTA etc. should stay upper
        result = canonical_inci("peg-40 hydrogenated castor oil")
        assert result.startswith("PEG")

    def test_ci_colour(self):
        assert canonical_inci("CI 77891") == "CI 77891"
        assert canonical_inci("ci77891") == "CI 77891"
        assert canonical_inci("CI  15985") == "CI 15985"

    def test_title_case_normal(self):
        assert canonical_inci("sodium chloride") == "Sodium Chloride"
        assert canonical_inci("glycerin") == "Glycerin"

    def test_empty_string(self):
        assert canonical_inci("") == ""

    def test_whitespace_normalised(self):
        assert canonical_inci("  aqua  ") == "Aqua"

    def test_vitamin_e(self):
        assert canonical_inci("vitamin e") == "Tocopherol"

    def test_mixed_tocopherols(self):
        assert canonical_inci("mixed tocopherols") == "Tocopherol"

    def test_castor_oil(self):
        assert canonical_inci("castor oil") == "Ricinus Communis Seed Oil"

    def test_argan_oil(self):
        assert canonical_inci("argan oil") == "Argania Spinosa Kernel Oil"


# ---------------------------------------------------------------------------
# declarable_name / is_declarable
# ---------------------------------------------------------------------------

class TestDeclarableAllergens:
    def test_linalool_is_declarable(self):
        assert is_declarable("linalool") is True
        assert declarable_name("linalool") == "Linalool"

    def test_limonene_is_declarable(self):
        assert is_declarable("Limonene") is True

    def test_geraniol_is_declarable(self):
        assert is_declarable("geraniol") is True

    def test_eugenol_is_declarable(self):
        assert is_declarable("eugenol") is True

    def test_coumarin_is_declarable(self):
        assert is_declarable("coumarin") is True

    def test_citral_is_declarable(self):
        assert is_declarable("citral") is True

    def test_alpha_isomethyl_ionone(self):
        assert is_declarable("alpha-isomethyl ionone") is True

    def test_non_allergen_returns_none(self):
        assert declarable_name("sodium chloride") is None
        assert declarable_name("glycerin") is None
        assert declarable_name("aqua") is None

    def test_non_allergen_is_declarable_false(self):
        assert is_declarable("propylene glycol") is False

    def test_all_26_present(self):
        # The 26 classic allergens must all be in the dict
        assert len(DECLARABLE_ALLERGENS) >= 26

    def test_benzyl_alcohol_canonical(self):
        # Input via canonical synonym shouldn't break lookup
        assert is_declarable("Benzyl Alcohol") is True


class TestDeclarableExtra:
    """Новите Анекс III алергени от Регламент (ЕС) 2023/1545."""

    def test_hexamethylindanopyran(self):
        assert is_declarable("Hexamethylindanopyran") is True
        assert declarable_name("Hexamethylindanopyran") == "Hexamethylindanopyran"

    def test_amyl_salicylate(self):
        assert is_declarable("Amyl Salicylate") is True
        assert declarable_name("Amyl Salicylate") == "Amyl Salicylate"

    def test_camphor(self):
        assert is_declarable("Camphor") is True

    def test_beta_caryophyllene(self):
        assert is_declarable("Beta-Caryophyllene") is True
        assert declarable_name("Beta-Caryophyllene") == "beta-Caryophyllene"

    def test_carvone(self):
        assert is_declarable("Carvone") is True

    def test_linalyl_acetate(self):
        assert is_declarable("Linalyl Acetate") is True

    def test_geranyl_acetate(self):
        assert is_declarable("Geranyl Acetate") is True
        assert declarable_name("Geranyl Acetate") == "Geranyl Acetate"

    def test_alpha_terpinene(self):
        assert is_declarable("Alpha-Terpinene") is True
        assert declarable_name("Alpha-Terpinene") == "alpha-Terpinene"

    def test_3_propylidenephthalide(self):
        assert is_declarable("3-Propylidenephthalide") is True

    def test_citrus_aurantium_peel_oil(self):
        assert is_declarable("Citrus Aurantium Peel Oil") is True
        assert declarable_name("Citrus Aurantium Peel Oil") == "Citrus Aurantium Peel Oil"

    def test_lavandula_oil_extract_alias(self):
        # IFRA certificates use "Lavandula Oil/Extract" — must resolve
        assert is_declarable("Lavandula Oil/Extract") is True
        assert declarable_name("Lavandula Oil/Extract") == "Lavandula Angustifolia Oil"

    def test_lavandula_oil_alias(self):
        assert is_declarable("Lavandula Oil") is True

    def test_eucalyptus_globulus_oil_alias(self):
        assert is_declarable("Eucalyptus Globulus Oil") is True
        assert declarable_name("Eucalyptus Globulus Oil") == "Eucalyptus Globulus Leaf Oil"

    def test_eucalyptus_globulus_oil_extract_alias(self):
        assert is_declarable("Eucalyptus Globulus Oil/Extract") is True

    def test_non_extra_not_affected(self):
        # Classic Annex III entries still work
        assert is_declarable("Limonene") is True
        assert is_declarable("Linalool") is True
        assert is_declarable("Coumarin") is True


# ---------------------------------------------------------------------------
# localize_inci
# ---------------------------------------------------------------------------

class TestLocalizeInci:
    def test_eu_country_no_change(self):
        assert localize_inci("Aqua", ["DE"]) == "Aqua"
        assert localize_inci("Parfum", ["FR", "IT"]) == "Parfum"

    def test_us_only_remaps_aqua(self):
        assert localize_inci("Aqua", ["US"]) == "Water"

    def test_us_only_remaps_parfum(self):
        assert localize_inci("Parfum", ["US"]) == "Fragrance"

    def test_us_only_remaps_aroma(self):
        assert localize_inci("Aroma", ["US"]) == "Flavor"

    def test_unknown_non_eu_country_remaps(self):
        assert localize_inci("Aqua", ["CA"]) == "Water"

    def test_mixed_eu_us_keeps_eu(self):
        # If at least one EU country is present, keep EU naming
        assert localize_inci("Aqua", ["DE", "US"]) == "Aqua"

    def test_empty_countries_no_change(self):
        assert localize_inci("Aqua", []) == "Aqua"
        assert localize_inci("Aqua", None) == "Aqua"

    def test_non_mapped_name_passes_through(self):
        assert localize_inci("Glycerin", ["US"]) == "Glycerin"


# ---------------------------------------------------------------------------
# validate_inci
# ---------------------------------------------------------------------------

class TestValidateInci:
    def test_valid_list_no_issues(self):
        names = ["Aqua", "Glycerin", "Sodium Chloride"]
        assert validate_inci(names) == []

    def test_duplicate_detected(self):
        issues = validate_inci(["Aqua", "Glycerin", "Aqua"])
        assert any("Дубликат" in i for i in issues)

    def test_ppm_flagged(self):
        issues = validate_inci(["Aqua (20 ppm)"])
        assert any("Съмнително" in i for i in issues)

    def test_percent_flagged(self):
        issues = validate_inci(["Aqua 50%"])
        assert any("Съмнително" in i for i in issues)

    def test_colon_flagged(self):
        issues = validate_inci(["REACH: Registration 12345"])
        assert any("Съмнително" in i for i in issues)

    def test_long_name_flagged(self):
        long_name = "A" * 61
        issues = validate_inci([long_name])
        assert any("Съмнително" in i for i in issues)

    def test_reach_keyword_flagged(self):
        issues = validate_inci(["REACH Annex XVII"])
        assert any("Съмнително" in i for i in issues)


# ---------------------------------------------------------------------------
# Round-trip: fragrance with junk non-declarable allergens is filtered
# ---------------------------------------------------------------------------

class TestFragranceRoundTrip:
    """
    Продукт с парфюм, съдържащ:
      - Linalool (Анекс III — трябва да премине)
      - Limonene (Анекс III — трябва да премине)
      - Propylene Glycol (НЕ е в Анекс III — трябва да се филтрира)
      - Sodium Chloride (НЕ е в Анекс III — трябва да се филтрира)
    """

    _DOC = {
        "product": {
            "name": "Test Lotion",
            "product_type": "leave-on",
            "sale_countries": ["BG"],
        },
        "raw_materials": [
            {
                "name": "Water Phase",
                "dose_pct": 95.0,
                "composition": [
                    {"inci_name": "water", "pct": 100.0, "function": "solvent"},
                ],
            },
            {
                "name": "Fragrance Mix X",
                "dose_pct": 5.0,
                "is_fragrance": True,
                "inci_name": "fragrance",
                "allergens": [
                    {"name": "Linalool", "pct_in_fragrance": 3.0},
                    {"name": "Limonene", "pct_in_fragrance": 2.0},
                    # junk — not in Annex III
                    {"name": "Propylene Glycol", "pct_in_fragrance": 5.0},
                    {"name": "Sodium Chloride", "pct_in_fragrance": 1.0},
                ],
            },
        ],
    }

    def _build(self):
        product, warnings = build_product(self._DOC)
        return product, warnings

    def test_fragrance_inci_canonicalized(self):
        product, _ = self._build()
        frag_lines = [l for l in product.formula if l.ingredient.is_fragrance]
        assert frag_lines, "Парфюмена линия не е намерена"
        assert frag_lines[0].ingredient.inci_name == "Parfum"

    def test_junk_allergens_filtered(self):
        product, _ = self._build()
        frag_lines = [l for l in product.formula if l.ingredient.is_fragrance]
        allergen_names = [a.name for a in frag_lines[0].ingredient.allergens]
        assert "Propylene Glycol" not in allergen_names
        assert "Sodium Chloride" not in allergen_names

    def test_annex_iii_allergens_kept(self):
        product, _ = self._build()
        frag_lines = [l for l in product.formula if l.ingredient.is_fragrance]
        allergen_names = [a.name for a in frag_lines[0].ingredient.allergens]
        assert "Linalool" in allergen_names
        assert "Limonene" in allergen_names

    def test_water_canonicalized_in_inci_list(self):
        product, _ = self._build()
        inci = generate_inci(product)
        assert "Aqua" in inci

    def test_eu_country_keeps_aqua(self):
        product, _ = self._build()
        inci = generate_inci(product)
        assert "Aqua" in inci
        assert "Water" not in inci
