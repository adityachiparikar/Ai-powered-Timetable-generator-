from app.services.llm.nlp_service import NLPConstraintService


def test_timetable_parser_accepts_common_day_typo():
    service = NLPConstraintService()

    action = service._parse_timetable_action_locally(
        "FROM TY B REMOVE THE SESSION FROM WEDNSDAY AND SHIFT IT OTHER DAY"
    )

    assert action == {
        "type": "MOVE_GROUP_DAY_SESSIONS",
        "params": {
            "group_name": "TY B",
            "teacher_name": None,
            "from_day": "Wednesday",
            "target_days": [],
        },
    }


def test_timetable_parser_accepts_exact_day_name():
    service = NLPConstraintService()

    action = service._parse_timetable_action_locally(
        "move TY B sessions from Wednesday to Saturday"
    )

    assert action["type"] == "MOVE_GROUP_DAY_SESSIONS"
    assert action["params"]["group_name"] == "TY B"
    assert action["params"]["from_day"] == "Wednesday"
    assert action["params"]["target_days"] == ["Saturday"]


def test_local_config_update_does_not_need_llm():
    service = NLPConstraintService()

    result = service.process_chat_request(
        "set max daily load to 5",
        {
            "max_daily_load": 4,
            "minimize_gaps": True,
            "consecutive_labs": True,
            "parallel_labs": True,
        },
    )

    assert result["updated_config"] == {"max_daily_load": 5}
