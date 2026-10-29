# בדיקות ל-Lock: בודקים את מספר האישורים ואת המצב הסופי - לא איזה Thread זכה
import pytest

from AirMatrix.threaded_processing import PetHoldCapacity, run_checkin_counters


@pytest.mark.parametrize("slots, counters", [(1, 10), (3, 20)])
def test_reservations_never_exceed_capacity(slots, counters):
    capacity = PetHoldCapacity("LY001", total_slots=slots)
    outcomes = run_checkin_counters(capacity, [f"PET-{i}" for i in range(counters)])

    assert sum(outcomes.values()) == slots          # בדיוק כמספר המקומות
    assert len(outcomes) == counters                # כל דלפק קיבל תשובה
    assert capacity.available_slots() == 0
    assert len(set(capacity.reserved)) == slots     # אין כפילות ברשימת המשוריינים
