from typing import TypedDict, Dict, List


class ReviewState(TypedDict):
    article: str

    grammar_result: Dict
    style_result: Dict
    structure_result: Dict

    issues: List[str]

    final_decision: str