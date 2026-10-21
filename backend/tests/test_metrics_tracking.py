from evaluation.metrics_tracking import fragmentation_count, id_switches, identity_consistency

# Object A: tracked every frame, but the tracker relabels it partway through.
# Object B: tracked, briefly lost, then re-found with the SAME id (no switch,
# but a fragmentation).
FRAMES = [
    {"A": 1, "B": 5},
    {"A": 1, "B": None},
    {"A": 1, "B": 5},
    {"A": 2, "B": 5},
    {"A": 2, "B": None},
]


def test_id_switches_counts_only_genuine_relabels():
    # A: 1 -> 1 -> 1 -> 2 -> 2  => exactly one switch (1->2).
    # B: 5 -> (gap) -> 5 -> 5 -> (gap) => same id before/after gaps, no switch.
    assert id_switches(FRAMES) == 1


def test_fragmentation_counts_lost_and_reacquired_tracks():
    # A: tracked continuously => 1 segment => 0 fragmentations.
    # B: tracked, gap, tracked, tracked, gap => 2 segments => 1 fragmentation.
    assert fragmentation_count(FRAMES) == 1


def test_identity_consistency_is_micro_averaged_across_objects():
    # A: ids [1,1,1,2,2] -> majority id 1 appears 3/5 times -> 3 matches / 5 frames.
    # B: ids [5,5,5] (None frames excluded) -> majority id 5, 3/3 matches.
    # Overall: (3 + 3) / (5 + 3) = 6/8 = 0.75
    assert identity_consistency(FRAMES) == 0.75


def test_no_switches_when_every_object_keeps_one_id():
    frames = [{"A": 1}, {"A": 1}, {"A": 1}]
    assert id_switches(frames) == 0
    assert fragmentation_count(frames) == 0
    assert identity_consistency(frames) == 1.0


def test_empty_sequence_does_not_crash():
    assert id_switches([]) == 0
    assert fragmentation_count([]) == 0
    assert identity_consistency([]) == 0.0


def test_object_never_detected_contributes_no_switches_or_consistency_credit():
    frames = [{"A": None}, {"A": None}]
    assert id_switches(frames) == 0
    assert fragmentation_count(frames) == 0
    assert identity_consistency(frames) == 0.0
