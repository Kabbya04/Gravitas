from app.rag.fusion import reciprocal_rank_fusion


def test_rrf_orders_union():
    a = ["c1", "c2", "c3"]
    b = ["c3", "c1", "c4"]
    fused = reciprocal_rank_fusion([a, b], k=60)
    assert fused[0] == "c1"
    assert set(fused) == {"c1", "c2", "c3", "c4"}
