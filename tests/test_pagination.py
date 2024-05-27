import pytest

from todo_api.core import pagination


def test_paginated_create():
    items = list(range(100))
    paginated = pagination.Paginated[int].create(items, page=1, size=100, total=1000)

    assert paginated.items == items
    assert paginated.page == 1
    assert paginated.size == 100
    assert paginated.pages == 10
    assert paginated.total_count == 1000


def test_paginated_create_raises_if_size_is_le_zero():
    with pytest.raises(pagination.PaginationError):
        pagination.Paginated[int].create(list(range(100)), page=1, size=0, total=100)
