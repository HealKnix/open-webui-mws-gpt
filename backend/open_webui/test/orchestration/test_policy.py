from types import SimpleNamespace

from open_webui.orchestration.policy import select_operation_assignment


def _registry_with_text_models():
    models = [
        {'id': 'mws-gpt-alpha', 'capabilities': {'text_reasoning': True}},
        {'id': 'qwen2.5-72b-instruct', 'capabilities': {'text_reasoning': True}},
        {'id': 'qwen3-coder-480b-a35b', 'capabilities': {'text_reasoning': True, 'coding': True}},
    ]
    return {'models': models, 'by_id': {model['id']: model for model in models}}


def test_select_operation_assignment_for_retrieval_uses_retriever_role():
    registry = _registry_with_text_models()
    plan = SimpleNamespace(user_goal='Сделай deep research по документу', operations=[1, 2, 3])
    operation = SimpleNamespace(
        prompt='Найди релевантные фрагменты и источники',
        inputs=['inp_text_1'],
        options={'deep_research': True},
    )

    assignment = select_operation_assignment(
        registry=registry,
        operation_kind='retrieve_context',
        policy_mode='balanced',
        plan=plan,
        operation=operation,
    )

    assert assignment.role == 'retriever'
    assert assignment.primary is not None


def test_select_operation_assignment_for_code_critique_uses_coder_role():
    registry = _registry_with_text_models()
    plan = SimpleNamespace(user_goal='Проверь этот код и исправь баг', operations=[1, 2])
    operation = SimpleNamespace(
        prompt='Проанализируй stacktrace и предложи patch для python кода',
        inputs=['draft_text_1'],
        options={},
    )

    assignment = select_operation_assignment(
        registry=registry,
        operation_kind='critique_text',
        policy_mode='quality',
        plan=plan,
        operation=operation,
    )

    assert assignment.role == 'coder'
    assert assignment.primary is not None


def test_select_operation_assignment_respects_explicit_ms_agent_role():
    registry = _registry_with_text_models()
    plan = SimpleNamespace(user_goal='Сделай deep research по теме', operations=[1, 2, 3, 4, 5])
    operation = SimpleNamespace(
        prompt='Собери evidence по теме',
        inputs=['inp_text_1', 'research_plan_1'],
        options={'deep_research': True, 'agent': 'searcher'},
    )

    assignment = select_operation_assignment(
        registry=registry,
        operation_kind='retrieve_context',
        policy_mode='balanced',
        plan=plan,
        operation=operation,
    )

    assert assignment.role == 'searcher'
    assert assignment.primary is not None
