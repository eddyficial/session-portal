from Codebase.v2.ui.app import compact_number


def test_compact_number_keeps_large_token_counts_short():
    assert compact_number(232_979_455) == "232.98M"
    assert compact_number(709_279) == "709.3K"
    assert compact_number(0) == "0"
