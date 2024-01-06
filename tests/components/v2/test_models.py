from typing import List, Literal, Optional

import marvin.v2
import pytest
from pydantic import BaseModel, Field

from tests.utils import pytest_mark_class


@pytest_mark_class("llm")
class TestModels:
    def test_arithmetic(self):
        @marvin.v2.model
        class Arithmetic(BaseModel):
            sum: float = Field(
                ..., description="The resolved sum of provided arguments"
            )
            is_odd: bool

        x = Arithmetic("One plus six")
        assert x.sum == 7
        assert x.is_odd

    def test_geospatial(self):
        @marvin.v2.model
        class Location(BaseModel):
            latitude: float
            longitude: float
            city: str
            state: str
            country: str = Field(..., description="The abbreviated country name")

        x = Location("The capital city of the Cornhusker State.")
        assert x.city == "Lincoln"
        assert x.state == "Nebraska"
        assert x.country in {"US", "USA", "U.S.", "U.S.A.", "United States"}
        assert x.latitude // 1 == 40
        assert x.longitude // 1 == -97

    @pytest.mark.xfail(reason="TODO: flaky on 3.5")
    def test_depth(self):
        from typing import List

        class Country(BaseModel):
            name: str

        class City(BaseModel):
            name: str
            country: Country

        class Neighborhood(BaseModel):
            name: str
            city: City

        @marvin.v2.model
        class RentalHistory(BaseModel):
            neighborhood: List[Neighborhood]

        assert RentalHistory(
            """\
            I lived in Palms, then Mar Vista, then Pico Robertson.
        """
        )

    @pytest.mark.flaky(max_runs=3)
    def test_resume(self):
        class Experience(BaseModel):
            technology: str
            years_of_experience: int
            supporting_phrase: Optional[str]

        @marvin.v2.model
        class Resume(BaseModel):
            """Details about a person's work experience."""

            greater_than_three_years_management_experience: bool
            greater_than_ten_years_management_experience: bool
            technologies: List[Experience]

        x = Resume(
            """\
            Data Engineering Manager, 2017-2022
            • Managed team of three engineers and data scientists
            • Deployed and maintained internal Apache Kafka pipeline
            • Built tree-based classifier to predict customer churn (xgboost)\
        """
        )

        assert x.greater_than_three_years_management_experience
        assert not x.greater_than_ten_years_management_experience
        assert len(x.technologies) == 2

    def test_literal(self):
        @marvin.v2.model
        class LLMConference(BaseModel):
            speakers: list[
                Literal["Adam", "Nate", "Jeremiah", "Marvin", "Billy Bob Thornton"]
            ]

        x = LLMConference(
            """
            The conference for best LLM framework will feature talks by
            Adam, Nate, Jeremiah, Marvin, and Billy Bob Thornton.
        """
        )
        assert len(set(x.speakers)) == 5
        assert set(x.speakers) == set(
            ["Adam", "Nate", "Jeremiah", "Marvin", "Billy Bob Thornton"]
        )

    @pytest.mark.xfail(reason="regression in OpenAI function-using models")
    def test_history(self):
        from typing import List

        class Location(BaseModel):
            city: str
            state: str

        class Candidate(BaseModel):
            name: str
            political_party: str
            campaign_slogan: str
            birthplace: Location

        @marvin.v2.model
        class Election(BaseModel):
            candidates: List[Candidate]
            winner: Candidate

        x = Election("The United States Election of 1800")

        assert x.winner in x.candidates
        assert x.winner.name == "Thomas Jefferson"
        assert x.winner.political_party == "Democratic-Republican"
        assert x.winner.birthplace.city == "Shadwell"
        assert x.winner.birthplace.state == "Virginia"
        assert set([candidate.name for candidate in x.candidates]).issubset(
            set(
                [
                    "Thomas Jefferson",
                    "John Adams",
                    "Aaron Burr",
                    "Charles C. Pinckney",
                    "Charles Pinckney",
                    "Charles Cotesworth Pinckney",
                ]
            )
        )

    @pytest.mark.skip(reason="old behavior, may revisit")
    def test_correct_class_is_returned(self):
        @marvin.v2.model
        class Fruit(BaseModel):
            color: str
            name: str

        fruit = Fruit("loved by monkeys")

        assert isinstance(fruit, Fruit)


@pytest.mark.skip(reason="old behavior, may revisit")
@pytest_mark_class("llm")
class TestInstructions:
    def test_instructions_error(self):
        @marvin.v2.model
        class Test(BaseModel):
            text: str

        with pytest.raises(
            ValueError, match="(Received `instructions` but this model)"
        ):
            Test("Hello!", instructions="Translate to French")
        with pytest.raises(ValueError, match="(Received `model` but this model)"):
            Test("Hello!", model=None)

    def test_instructions(self):
        @marvin.v2.model
        class Text(BaseModel):
            text: str

        t1 = Text("Hello")
        assert t1.text == "Hello"

        # this model is identical except it has an instruction
        @marvin.v2.model(instructions="first translate the text to French")
        class Text(BaseModel):
            text: str

        t2 = Text("Hello")
        assert t2.text == "Bonjour"

    def test_follow_instance_instructions(self):
        @marvin.v2.model
        class Test(BaseModel):
            text: str

        t1 = Test("Hello")
        assert t1.text == "Hello"

        # this model is identical except it has an instruction
        @marvin.v2.model
        class Test(BaseModel):
            text: str

        t2 = Test("Hello", instructions_="first translate the text to French")
        assert t2.text == "Bonjour"

    def test_follow_global_and_instance_instructions(self):
        @marvin.v2.model(instructions="Always set color_1 to 'red'")
        class Test(BaseModel):
            color_1: str
            color_2: str

        t1 = Test("Hello", instructions_="Always set color_2 to 'blue'")
        assert t1 == Test(color_1="red", color_2="blue")

    def test_follow_docstring_and_global_and_instance_instructions(self):
        @marvin.v2.model(instructions="Always set color_1 to 'red'")
        class Test(BaseModel):
            """Always set color_3 to 'orange'"""

            color_1: str
            color_2: str
            color_3: str

        t1 = Test("Hello", instructions_="Always set color_2 to 'blue'")
        assert t1 == Test(color_1="red", color_2="blue", color_3="orange")

    def test_follow_multiple_instructions(self):
        # ensure that instructions don't bleed to other invocations
        @marvin.v2.model
        class Translation(BaseModel):
            """Translates from one language to another language"""

            original_text: str
            translated_text: str

        t1 = Translation("Hello, world!", instructions_="Translate to French")
        t2 = Translation("Hello, world!", instructions_="Translate to German")

        assert t1 == Translation(
            original_text="Hello, world!", translated_text="Bonjour, monde!"
        )
        assert t2 == Translation(
            original_text="Hello, world!", translated_text="Hallo, Welt!"
        )


@pytest_mark_class("llm")
class TestModelMapping:
    def test_arithmetic(self):
        @marvin.v2.model
        class Arithmetic(BaseModel):
            sum: float

        x = Arithmetic.map(["One plus six", "Two plus 100 minus one"])
        assert len(x) == 2
        assert x[0].sum == 7
        assert x[1].sum == 101

    @pytest.mark.skip(reason="TODO: flaky on 3.5")
    def test_fix_misspellings(self):
        @marvin.v2.model
        class City(BaseModel):
            """Standardize misspelled or informal city names"""

            name: str = Field(
                description=(
                    "The OFFICIAL, correctly-spelled name of a city - must be"
                    " capitalized. Do not include the state or country, or use any"
                    " abbreviations. e.g. 'big apple' -> 'New York City'"
                ),
            )

        results = City.map(
            [
                "Chicago",
                "America's third-largest city",
                "chicago, Illinois, USA",
                "colloquially known as 'chi-town'",
            ]
        )
        assert len(results) == 4
        for result in results:
            assert result.name == "Chicago"
