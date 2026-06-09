"""
Allergen DB completeness guard.

Verifies that DECLARABLE_ALLERGENS contains every entry we know about
from Annex III of Reg. 1223/2009 as amended by Reg. (EU) 2023/1545.

WHY THIS EXISTS: In SK5071025 validation we found that 5 Annex III entries
added by Reg. 2023/1545 were simply missing from _DECLARABLE_EXTRA, causing
silent drops in the declaration. This test catches that class of regression
immediately when nomenclature.py is modified.

If this test fails after adding new allergens, update EXPECTED_MIN_COUNT.
If it fails after removing allergens, that is a regulatory regression — fix
nomenclature.py, not this test.
"""
import pytest
from pif_engine.nomenclature import DECLARABLE_ALLERGENS, declarable_name

# The 26 original Annex III/1 allergens (Reg. 1223/2009, as counted in _DECLARABLE_26)
ORIGINAL_26 = [
    "Amyl Cinnamal", "Amylcinnamyl Alcohol", "Anise Alcohol", "Benzyl Alcohol",
    "Benzyl Benzoate", "Benzyl Cinnamate", "Benzyl Salicylate", "Cinnamal",
    "Cinnamyl Alcohol", "Citral", "Citronellol", "Coumarin", "Eugenol", "Farnesol",
    "Geraniol", "Hexyl Cinnamal", "Hydroxycitronellal", "Isoeugenol", "Limonene",
    "Linalool", "Methyl 2-Octynoate", "alpha-Isomethyl Ionone",
    "Butylphenyl Methylpropional", "Evernia Prunastri Extract",
    "Evernia Furfuracea Extract", "Hydroxyisohexyl 3-Cyclohexene Carboxaldehyde",
]

# Critical Reg. 2023/1545 entries that were previously missing (SK5071025 Finding B).
# Keyed by Annex III entry number for traceability.
ANNEX_III_2023 = {
    "III/133":  "Terpinolene",
    "III/175":  "3-Propylidenephthalide",
    "III/328":  "Amyl Salicylate",
    "III/329":  "Anethole",
    "III/330":  "Benzaldehyde",
    "III/331":  "Camphor",
    "III/332":  "beta-Caryophyllene",
    "III/333":  "Carvone",
    "III/334":  "Dimethyl Phenethyl Acetate",
    "III/335":  "Hexadecanolactone",
    "III/336":  "Hexamethylindanopyran",
    "III/337":  "Linalyl Acetate",
    "III/343":  "Terpineol",
    "III/344":  "Tetramethyl Acetyloctahydronaphthalenes",
    "III/347":  "Cananga Odorata Flower Oil",
    "III/348":  "Cinnamomum Cassia Leaf Oil",
    "III/349":  "Cinnamomum Zeylanicum Bark Oil",
    "III/350":  "Citrus Aurantium Dulcis Flower Oil",
    "III/351":  "Citrus Aurantium Peel Oil",
    "III/352":  "Citrus Aurantium Bergamia Peel Oil",
    "III/353":  "Citrus Limon Peel Oil",
    "III/354":  "Lemongrass Oil",
    "III/355":  "Eucalyptus Globulus Leaf Oil",
    "III/356":  "Eugenia Caryophyllus Flower Oil",
    "III/357":  "Jasminum Grandiflorum Flower Oil",
    "III/358":  "Juniperus Virginiana Wood Oil",
    "III/359":  "Laurus Nobilis Leaf Oil",
    "III/360":  "Lavandula Angustifolia Oil",
    "III/361":  "Mentha Piperita Herb Oil",
    "III/365":  "Pogostemon Cablin Oil",
    "III/368":  "Eugenyl Acetate",
    "III/369":  "Geranyl Acetate",
    "III/370":  "Isoeugenyl Acetate",
    "III/371":  "Pinene",
}

# Minimum total entries expected. Raise this when new allergens are legitimately added.
EXPECTED_MIN_COUNT = 56


def test_minimum_entry_count():
    """DB must contain at least EXPECTED_MIN_COUNT entries."""
    count = len(DECLARABLE_ALLERGENS)
    assert count >= EXPECTED_MIN_COUNT, (
        f"DECLARABLE_ALLERGENS has {count} entries; expected ≥ {EXPECTED_MIN_COUNT}. "
        "If entries were removed, restore them — this is a regulatory regression."
    )


@pytest.mark.parametrize("canonical_name", ORIGINAL_26)
def test_original_26_present(canonical_name):
    """Every one of the original 26 Annex III allergens must be resolvable."""
    result = declarable_name(canonical_name)
    assert result is not None, (
        f"Original Annex III allergen '{canonical_name}' is missing from "
        "DECLARABLE_ALLERGENS. Restore it in nomenclature.py."
    )


@pytest.mark.parametrize("annex_ref,canonical_name", ANNEX_III_2023.items())
def test_annex_iii_2023_present(annex_ref, canonical_name):
    """Every Reg. 2023/1545 allergen must be resolvable by its canonical name."""
    result = declarable_name(canonical_name)
    assert result is not None, (
        f"Annex III entry {annex_ref} '{canonical_name}' is missing from "
        "DECLARABLE_ALLERGENS. Add it to _DECLARABLE_EXTRA in nomenclature.py."
    )


def test_all_keys_round_trip():
    """Every key in DECLARABLE_ALLERGENS must resolve via declarable_name()."""
    failures = []
    for key, expected_value in DECLARABLE_ALLERGENS.items():
        result = declarable_name(key)
        if result != expected_value:
            failures.append(f"key={key!r}: expected {expected_value!r}, got {result!r}")
    assert not failures, (
        f"{len(failures)} keys don't round-trip through declarable_name():\n"
        + "\n".join(failures)
    )


def test_sk5071025_previously_dropped_allergens():
    """Regression guard: the 5 allergens silently dropped before SK5071025 fix."""
    previously_dropped = [
        "Tetramethyl Acetyloctahydronaphthalenes",  # III/344, was #3 by concentration
        "Pogostemon Cablin Oil",                    # III/365
        "Pinene",                                   # III/371
        "Terpineol",                                # III/343
        "Terpinolene",                              # III/133
    ]
    for name in previously_dropped:
        assert declarable_name(name) is not None, (
            f"'{name}' was previously silently dropped (SK5071025 Finding B). "
            "It must remain in DECLARABLE_ALLERGENS."
        )
