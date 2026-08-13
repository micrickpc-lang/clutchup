import pytest
from pydantic import ValidationError

from schemas import ProfileUpdate, SearchPreferences, SwipeRequest


def test_cannot_swipe_invalid_user():
    with pytest.raises(ValidationError):
        SwipeRequest(target_user_id=0, direction="like")


def test_filter_elo_order():
    with pytest.raises(ValidationError):
        SearchPreferences(elo_min=2000, elo_max=1000)


def test_profile_rejects_unknown_map():
    with pytest.raises(ValidationError):
        ProfileUpdate(preferred_maps=["FakeMap"])


def test_profile_normalizes_languages():
    assert ProfileUpdate(languages=[" RU ", "ru", "EN"]).languages == ["ru", "en"]
