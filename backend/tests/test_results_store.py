from app.services.results_store import ResultsStore


def test_create_returns_a_retrievable_completed_result():
    store = ResultsStore()
    result_id = store.create(media_type="image", output_url="/outputs/x.jpg")

    record = store.get(result_id)
    assert record is not None
    assert record["status"] == "completed"
    assert record["progress"] == 100
    assert record["media_type"] == "image"
    assert record["output_url"] == "/outputs/x.jpg"


def test_unknown_result_id_returns_none():
    store = ResultsStore()
    assert store.get("does-not-exist") is None


def test_each_create_call_gets_a_distinct_id():
    store = ResultsStore()
    id_a = store.create(media_type="image", output_url="/outputs/a.jpg")
    id_b = store.create(media_type="image", output_url="/outputs/b.jpg")
    assert id_a != id_b
