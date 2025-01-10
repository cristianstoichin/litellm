from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, TypedDict

from litellm.types.llms.openai import AllMessageValues
from litellm.types.utils import StandardCallbackDynamicParams


class PromptManagementClient(TypedDict):
    prompt_id: str
    prompt_template: List[AllMessageValues]
    model: Optional[str]
    optional_params: Optional[Dict[str, Any]]
    completed_messages: Optional[List[AllMessageValues]]


class PromptManagementBase(ABC):
    @property
    @abstractmethod
    def integration_name(self):
        pass

    @abstractmethod
    def should_run_prompt_management(
        self,
        prompt_id: str,
        dynamic_callback_params: StandardCallbackDynamicParams,
    ) -> bool:
        pass

    @abstractmethod
    def _compile_prompt_helper(
        self, prompt_id: str, prompt_variables: Optional[dict]
    ) -> PromptManagementClient:
        pass

    def compile_prompt(
        self,
        prompt_id: str,
        prompt_variables: Optional[dict],
        client_messages: List[AllMessageValues],
    ) -> PromptManagementClient:
        compiled_prompt_client = self._compile_prompt_helper(
            prompt_id=prompt_id,
            prompt_variables=prompt_variables,
        )

        messages = compiled_prompt_client["prompt_template"] + client_messages

        compiled_prompt_client["completed_messages"] = messages
        return compiled_prompt_client

    def _get_model_from_prompt(
        self, prompt_management_client: PromptManagementClient, model: str
    ) -> str:
        if prompt_management_client["model"] is not None:
            return prompt_management_client["model"]
        else:
            return model.replace("{}/".format(self.integration_name), "")

    def get_chat_completion_prompt(
        self,
        model: str,
        messages: List[AllMessageValues],
        non_default_params: dict,
        prompt_id: str,
        prompt_variables: Optional[dict],
        dynamic_callback_params: StandardCallbackDynamicParams,
    ) -> Tuple[
        str,
        List[AllMessageValues],
        dict,
    ]:
        if not self.should_run_prompt_management(
            prompt_id=prompt_id, dynamic_callback_params=dynamic_callback_params
        ):
            return model, messages, non_default_params

        prompt_template = self.compile_prompt(
            prompt_id=prompt_id,
            prompt_variables=prompt_variables,
            client_messages=messages,
        )

        completed_messages = prompt_template["completed_messages"] or messages

        prompt_template_optional_params = prompt_template["optional_params"] or {}

        updated_non_default_params = {
            **non_default_params,
            **prompt_template_optional_params,
        }

        model = self._get_model_from_prompt(
            prompt_management_client=prompt_template, model=model
        )

        return model, completed_messages, updated_non_default_params
