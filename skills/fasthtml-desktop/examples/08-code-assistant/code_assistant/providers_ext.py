# -*- coding: utf-8 -*-
"""providers_ext.py — 给「LLM provider」下拉扩充 DeepSeek / OpenRouter / Agnes 2

上游 code-assistant 的厂商下拉直接遍历 `astra_assistants.utils.provider_env_var_map`，
Key 表单、请求头也都从这张表推导。本模块在进程启动早期**就地**往这张表里追加三个
厂商，并补齐它们缺失的「厂商识别」与「请求头」两处逻辑，使三处口径一致：

  厂商         Key 环境变量                        典型模型串
  ---------   --------------------------------   ------------------------------------
  deepseek    DEEPSEEK_API_KEY                   deepseek/deepseek-chat
  openrouter  OPENROUTER_API_KEY                 openrouter/deepseek/deepseek-chat
  agnes2      AGNES_API_KEY + AGNES_API_BASE     agnes2/<模型名>

实现要点（三处必须同时打通，缺一下拉能选但用不了）：
 1) provider_env_var_map  —— 决定下拉里有哪些厂商、每个厂商要填哪些框；
 2) litellm.utils.get_llm_provider —— 决定「模型串属于哪个厂商」。deepseek/openrouter
    litellm 原生认识；agnes2 是国内 OpenAI 兼容服务，litellm 不认识，故本模块识别
    "agnes2/" 前缀并直接返回四元组（模型名, 厂商, key, base_url）；
 3) astra_assistants.patch.get_headers_for_model —— 决定往 Assistants 服务发什么
    LLM-PARAM-* 头。agnes2 走「api-key + base_url」直传，和上游 ollama 的写法同源。

注意（诚实声明）：DeepSeek / OpenRouter 是 litellm 内置厂商，端到端可用；Agnes 2 属于
OpenAI 兼容协议的占位接入，需要用户自己填 API 基础地址（形如 https://.../v1）。若上游
Assistants 服务端不识别该厂商名，可改选下拉里的 "other" 手工指定模型与 key。
"""
import os
import sys

import astra_assistants.patch  # noqa: F401  仅为把子模块塞进 sys.modules
from astra_assistants import utils as _aa_utils
from litellm import utils as _litellm_utils

# 注意：astra_assistants/__init__.py 里有 `from .patch import patch`，
# 所以 `from astra_assistants import patch` 拿到的是**函数**不是模块。
# 必须从 sys.modules 取真正的子模块，否则改不到 get_headers_for_model。
_aa_patch = sys.modules["astra_assistants.patch"]

AGNES_PREFIX = "agnes2/"

# 追加的厂商 → 表单字段名: 环境变量名
NEW_PROVIDERS = {
    "deepseek": {
        "api_key": "DEEPSEEK_API_KEY",
        "astra_token": "ASTRA_DB_APPLICATION_TOKEN",
    },
    "openrouter": {
        "api_key": "OPENROUTER_API_KEY",
        "astra_token": "ASTRA_DB_APPLICATION_TOKEN",
    },
    "agnes2": {
        "api_key": "AGNES_API_KEY",
        "base_url": "AGNES_API_BASE",
        "astra_token": "ASTRA_DB_APPLICATION_TOKEN",
    },
}

# 选中厂商时，Model 输入框的默认填充值（上游默认留空，用户容易忘了改而报错）
DEFAULT_MODELS = {
    "openai": "gpt-4o-2024-08-06",
    # 带厂商前缀，litellm 才认（裸的 claude-3-5-sonnet-20240620 在 1.44 会报 BadRequest）
    "anthropic": "anthropic/claude-3-5-sonnet-20240620",
    "groq": "groq/llama-3.1-70b-versatile",
    "gemini": "gemini/gemini-1.5-pro",
    "perplexity": "perplexity/llama-3.1-sonar-large-128k-online",
    "cohere": "cohere/command-r-plus",
    "deepseek": "deepseek/deepseek-chat",
    "openrouter": "openrouter/deepseek/deepseek-chat",
    "agnes2": "agnes2/agnes-2",
}

_APPLIED = False


def _patch_provider_map() -> None:
    """就地扩表：必须 update 而非重新赋值，因为 home.py 已经 from...import 了这个对象。"""
    for name, env_map in NEW_PROVIDERS.items():
        _aa_utils.provider_env_var_map.setdefault(name, env_map)

    # "other" 永远排在最后，观感更像「其它」
    if "other" in _aa_utils.provider_env_var_map:
        other = _aa_utils.provider_env_var_map.pop("other")
        _aa_utils.provider_env_var_map["other"] = other


def _patch_llm_provider_lookup() -> None:
    """让 litellm 认识 agnes2/ 前缀（litellm 内置表里没有这个国内厂商）。"""
    original = _litellm_utils.get_llm_provider

    if getattr(original, "_agnes_patched", False):
        return

    def get_llm_provider(model, *args, **kwargs):
        if isinstance(model, str) and model.startswith(AGNES_PREFIX):
            return (
                model[len(AGNES_PREFIX):],
                "agnes2",
                os.getenv("AGNES_API_KEY"),
                os.getenv("AGNES_API_BASE"),
            )
        return original(model, *args, **kwargs)

    get_llm_provider._agnes_patched = True
    get_llm_provider._original = original
    _litellm_utils.get_llm_provider = get_llm_provider

    # litellm 顶层也导出了同名函数，一并换掉，避免不同调用路径口径不一致
    try:
        import litellm

        if getattr(litellm, "get_llm_provider", None) is original:
            litellm.get_llm_provider = get_llm_provider
    except Exception:
        pass


def _patch_headers_for_model() -> None:
    """补齐新增厂商的凭证请求头。

    两个坑：
      1) agnes2 litellm 完全不认识 → 全部自己组（api-key + base_url）；
      2) openrouter litellm 认识，但 litellm 1.44 的 get_api_key() 里**没有**
         openrouter 分支，取不到 OPENROUTER_API_KEY，headers 会是空的 → 兜底
         直接按 NEW_PROVIDERS 里登记的环境变量名去取。
    """
    original = _aa_patch.get_headers_for_model

    if getattr(original, "_agnes_patched", False):
        return

    def get_headers_for_model(model):
        if isinstance(model, str) and model.startswith(AGNES_PREFIX):
            headers = {}
            key = os.getenv("AGNES_API_KEY")
            base_url = os.getenv("AGNES_API_BASE")
            if key:
                headers["api-key"] = key
            if base_url:
                headers["base_url"] = base_url
            return headers

        headers = original(model)
        if isinstance(headers, dict) and "api-key" not in headers:
            try:
                provider = _litellm_utils.get_llm_provider(model)[1]
            except Exception:
                provider = None
            env_map = NEW_PROVIDERS.get(provider or "")
            if env_map:
                key = os.getenv(env_map.get("api_key", ""), "")
                if key:
                    headers["api-key"] = key
        return headers

    get_headers_for_model._agnes_patched = True
    get_headers_for_model._original = original
    _aa_patch.get_headers_for_model = get_headers_for_model


async def provider_page(provider: str):
    """替代上游 update_provider.page：切换厂商时把 Model 框预填成该厂商的常用模型。

    上游行为是「厂商和当前模型不一致就把 Model 框清空」，用户很容易只填了 Key、
    忘了改模型串，结果保存后又被弹回来要 OPENAI_API_KEY。这里给个默认值。
    延迟导入是为了避开 code_assistant.main ←→ routes.home 的循环导入。
    """
    from astra_assistants.utils import get_env_vars_for_provider
    from code_assistant.constants.config import MODEL
    from code_assistant.routes.home import key_modal_page
    from litellm import utils as lu

    env_vars = get_env_vars_for_provider(provider)
    try:
        model_provider = lu.get_llm_provider(MODEL)[1]
    except Exception:
        model_provider = None

    if provider == model_provider:
        model = MODEL
    else:
        model = DEFAULT_MODELS.get(provider, "")
    return key_modal_page(provider, env_vars, model)


def apply() -> None:
    """幂等应用全部扩展。code_assistant.main 导入时调用一次即可。"""
    global _APPLIED
    if _APPLIED:
        return
    _patch_provider_map()
    _patch_llm_provider_lookup()
    _patch_headers_for_model()
    _APPLIED = True


apply()
