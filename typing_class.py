from typing import NamedTuple
from dataclasses import dataclass


class ItemInput(NamedTuple):
    code: int
    isbn: str
    ean: int
    publishing_house: str
    year: int


class Item(NamedTuple):
    """Информация о товаре"""
    code: int
    isbn: str
    ean: int
    publishing_house: str
    name: str
    author: str
    series: str
    year_of_issue: str
    cover_type: str
    illustrator: str
    age_restrictions: str
    number_of_pages: str
    paper_type: str
    reader_age: str
    product_weight: str
    description: str


class DisplaySelf:
    def waitgrab(self):
        pass

    def stop(self):
        pass


if __name__ == '__main__':


    x = ItemInput(1, 1, 1, 1)

    print(*x)

    y = Item(*x, 2)
    print(y)
