from __future__ import annotations

from open_webui.orchestration.schema import OrchestrationPlan


def validate_plan(plan: OrchestrationPlan) -> OrchestrationPlan:
    available_artifacts = {artifact.id for artifact in plan.input_artifacts}

    for operation in plan.operations:
        for input_id in operation.inputs:
            if input_id not in available_artifacts:
                raise ValueError(f'Unknown input artifact: {input_id}')
        available_artifacts.add(operation.output_id)

    for output_id in plan.output_artifact_ids:
        if output_id not in available_artifacts:
            raise ValueError(f'Unknown output artifact: {output_id}')

    return plan

