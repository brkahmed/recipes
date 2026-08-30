#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "beautifulsoup4",
#     "jinja2",
#     "lxml",
#     "markdown",
# ]
# ///
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from pprint import pprint

import markdown
from bs4 import BeautifulSoup
from jinja2 import Template

SCRIPT_DIR = Path(__file__).parent
RECIPES_DIR = SCRIPT_DIR.parent / "recipes"


with open(SCRIPT_DIR / "template.html") as f:
    RECIPE_TEMPLATE: Template = Template(f.read())


@dataclass
class Recipe:
    title: str
    image: Image
    description: str
    preparation_time: list[str]
    ingredients: list[str]
    steps: list[str]
    nutrition: str


@dataclass
class Image:
    src: str
    alt: str
    width: int
    height: int


def main() -> None:
    for path in (p for p in SCRIPT_DIR.iterdir() if p.is_file() and p.suffix == ".md"):
        print(f"{path.name:<40}", end=" ")
        try:
            recipe = parse_recipe(path)
        except ValueError as e:
            print(f"❌ failed — {e}")
        else:
            print("✅ done")
            render_recipe(recipe, RECIPES_DIR / f"{path.stem}.html")


def parse_recipe(md_path: Path) -> Recipe:
    with open(md_path) as f:
        md_text = f.read()
    html = markdown.markdown(md_text, extensions=["tables"])
    soup = BeautifulSoup(html, "lxml")

    try:
        title = soup.find("h1").text
        img = soup.find("img")
        img_src = img["src"]
        img_alt = img.get("alt", "")
        img_width, img_height = (
            int(s) for s in Path(img_src).stem.rpartition("-")[-1].split("x")
        )
        image = Image(
            src=img_src,
            alt=img_alt,
            width=img_width,
            height=img_height,
        )
        description = soup.find(
            "h2", string="Description"
        ).next_sibling.next_sibling.text
        preparation_time = [
            e.decode_contents()
            for e in soup.find(
                "h2", string="Preparation time"
            ).next_sibling.next_sibling.children
            if e.text.strip()
        ]
        ingredients = [
            e.text
            for e in soup.find(
                "h2", string="Ingredients"
            ).next_sibling.next_sibling.children
            if e.text.strip()
        ]
        steps = [
            e.decode_contents()
            for e in soup.find("h2", string="Steps").next_sibling.next_sibling.children
            if e.text.strip()
        ]
    except (AttributeError, TypeError) as e:
        raise ValueError("Invalid schema") from e

    return Recipe(
        title=title,
        image=image,
        description=description,
        preparation_time=preparation_time,
        ingredients=ingredients,
        steps=steps,
        nutrition="",
    )


def render_recipe(recipe: Recipe, path: Path) -> None:
    recipe_html = RECIPE_TEMPLATE.render(recipe=recipe)
    with open(path, mode="w") as f:
        f.write(recipe_html)


if __name__ == "__main__":
    main()
