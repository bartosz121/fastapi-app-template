from todo_api.core import pagination


def test_paginated_calculates_pages():
    items = list(range(100))
    paginated = pagination.Paginated[int].model_validate(
        {"items": items, "page": 1, "size": 100, "total": 1000}
    )

    assert paginated.items == items
    assert paginated.page == 1
    assert paginated.size == 100
    assert paginated.pages == 10
    assert paginated.total == 1000
