import pytest

pytest.importorskip('peewee_migrate')

from open_webui.orchestration.planner import build_plan


def test_build_plan_enables_deep_research_when_files_attached():
    form_data = {
        'model': 'mts-router',
        'messages': [{'role': 'user', 'content': 'Сделай глубокий анализ документа и дай структурированный ответ.'}],
        'metadata': {
            'files': [{'type': 'file', 'id': 'file-123', 'name': 'doc.pdf'}],
        },
    }

    plan = build_plan(form_data, policy_mode='balanced')
    kinds = [operation.kind for operation in plan.operations]
    roles = [operation.options.get('agent') for operation in plan.operations]

    assert plan.intent_mode == 'analyze_text'
    assert kinds == [
        'generate_text',
        'generate_text',
        'retrieve_context',
        'generate_text',
        'critique_text',
        'retrieve_context',
        'generate_text',
        'generate_text',
    ]
    assert roles == ['researcher', 'researcher', 'searcher', 'analyst', 'reviewer', 'searcher', 'analyst', 'reporter']
    assert plan.output_artifact_ids == ['out_text_1']
    assert plan.metadata.get('deep_research') is True


def test_build_plan_does_not_enable_deep_research_from_keywords_only():
    form_data = {
        'model': 'mts-router',
        'messages': [{'role': 'user', 'content': 'Сделай deep research рынка вкладов в России'}],
        'metadata': {},
    }

    plan = build_plan(form_data, policy_mode='balanced')

    assert plan.intent_mode == 'analyze_text'
    assert len(plan.operations) == 1
    assert plan.operations[0].kind == 'generate_text'
    assert plan.metadata.get('deep_research') is False


def test_build_plan_keeps_simple_single_step_for_short_text_prompt():
    form_data = {
        'model': 'mts-router',
        'messages': [{'role': 'user', 'content': 'Коротко объясни, что такое API.'}],
        'metadata': {},
    }

    plan = build_plan(form_data, policy_mode='fast')

    assert plan.intent_mode == 'analyze_text'
    assert len(plan.operations) == 1
    assert plan.operations[0].kind == 'generate_text'


def test_build_plan_enables_presentation_pipeline_from_feature_flag():
    form_data = {
        'model': 'mts-router',
        'messages': [{'role': 'user', 'content': 'Сделай презентацию по рынку вкладов России за 2025 год.'}],
        'features': {'presentation_generation': True},
        'metadata': {},
    }

    plan = build_plan(form_data, policy_mode='balanced')
    stages = [str(operation.options.get('stage') or '') for operation in plan.operations]
    kinds = [operation.kind for operation in plan.operations]

    assert plan.intent_mode == 'analyze_text'
    assert plan.metadata.get('presentation_generation') is True
    assert len(plan.operations) == 9
    assert kinds == [
        'generate_text',
        'generate_text',
        'retrieve_context',
        'generate_text',
        'generate_text',
        'critique_text',
        'retrieve_context',
        'generate_text',
        'generate_text',
    ]
    assert stages[0] == 'presentation_plan'
    assert stages[-1] == 'presentation_finalize'


def test_build_plan_enables_presentation_pipeline_from_goal_intent():
    form_data = {
        'model': 'mts-router',
        'messages': [{'role': 'user', 'content': 'Сделай презентацию по банковскому рынку РФ на 12 слайдов.'}],
        'metadata': {},
    }

    plan = build_plan(form_data, policy_mode='balanced')
    stages = [str(operation.options.get('stage') or '') for operation in plan.operations]

    assert plan.intent_mode == 'analyze_text'
    assert plan.metadata.get('presentation_generation') is True
    assert len(plan.operations) == 9
    assert stages[0] == 'presentation_plan'
    assert stages[-1] == 'presentation_finalize'
