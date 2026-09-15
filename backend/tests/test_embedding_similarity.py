from app.embeddings.similarity import cosine_similarity


def test_identical_vectors_have_similarity_one():
    v = [1.0, 2.0, 3.0]
    assert cosine_similarity(v, v) == 1.0


def test_orthogonal_vectors_have_similarity_zero():
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0


def test_opposite_vectors_have_similarity_negative_one():
    assert cosine_similarity([1.0, 0.0], [-1.0, 0.0]) == -1.0


def test_zero_vector_returns_zero_instead_of_dividing_by_zero():
    assert cosine_similarity([0.0, 0.0], [1.0, 2.0]) == 0.0
