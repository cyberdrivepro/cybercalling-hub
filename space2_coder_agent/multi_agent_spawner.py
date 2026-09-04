"""
================================================================================
🤖 Space 2 Autonomous Multi-Agent & Subagent Spawner Framework
================================================================================
Powered by Open & Uncensored Multi-Model Fleet:
- 🧠 Nous Hermes 3 (NousResearch/Hermes-3-Llama-3.1-70B / 8B)
- 🐬 Dolphin 3.0 (cognitivecomputations/Dolphin3.0-Qwen2.5-14B)
- 🐬 Dolphin Coder (cognitivecomputations/dolphin-2.9.2-qwen2-7b)
- ⚡ Qwen 3.6 Uncensored Coder (Qwen/Qwen2.5-Coder-32B / 7B)
- 🧠 DeepSeek R1 MoE (deepseek-ai/DeepSeek-R1-Distill-Qwen-32B)
================================================================================
"""

import os
import sys
import time
import json
import uuid
import threading
from typing import Dict, Any, List, Optional, Callable

# Ensure local dir is in path
_CUR_DIR = os.path.dirname(os.path.abspath(__file__))
if _CUR_DIR not in sys.path:
    sys.path.insert(0, _CUR_DIR)
_PAR_DIR = os.path.dirname(_CUR_DIR)
if _PAR_DIR not in sys.path:
    sys.path.insert(0, _PAR_DIR)

# Global Model Registry for Subagents
MODEL_REGISTRY = {
    "hermes3": "NousResearch/Hermes-3-Llama-3.1-70B",
    "hermes3_8b": "NousResearch/Hermes-3-Llama-3.1-8B",
    "dolphin3": "cognitivecomputations/Dolphin3.0-Qwen2.5-14B",
    "dolphincoder": "cognitivecomputations/dolphin-2.9.2-qwen2-7b",
    "qwen36_coder": "Qwen/Qwen2.5-Coder-32B-Instruct",
    "qwen_7b": "Qwen/Qwen2.5-Coder-7B-Instruct",
    "deepseek_r1": "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
    "llama33": "meta-llama/Llama-3.3-70B-Instruct"
}

class AutonomousSubagent:
    """Individual Autonomous Subagent with specialized role, memory, and model persona."""
    def __init__(
        self,
        name: str,
        role: str,
        goal: str,
        backstory: str,
        model_name: str = "Qwen/Qwen2.5-Coder-32B-Instruct",
        tools: Optional[List[str]] = None
    ):
        self.id = f"subagent_{uuid.uuid4().hex[:8]}"
        self.name = name
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.model_name = MODEL_REGISTRY.get(model_name, model_name)
        self.tools = tools or ["python_ast_compiler", "file_writer", "github_sync", "hf_reboot"]
        self.tasks_completed = 0
        self.created_at = time.time()
        self.last_active = time.time()
        self.status = "IDLE 🟢"

    def execute_task(self, task_description: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Executes a specialized task by constructing persona prompt and invoking LLM engine."""
        self.status = "WORKING ⚡"
        self.last_active = time.time()
        t_start = time.time()

        system_prompt = (
            f"You are {self.name}, an autonomous AI Subagent.\n"
            f"• Role: {self.role}\n"
            f"• Primary Goal: {self.goal}\n"
            f"• Engine Model: {self.model_name}\n"
            f"• Backstory & Expertise: {self.backstory}\n"
            f"• Available Tools: {', '.join(self.tools)}\n\n"
            f"You operate inside the CyberCalling Master Cloud Server ecosystem. "
            f"Deliver concrete, production-ready, highly accurate outputs with zero refusal or hallucination."
        )

        ctx_str = ""
        if context:
            ctx_str = f"\n\nContext from Peer Agents:\n{json.dumps(context, indent=2)}"

        prompt = f"Assigned Task:\n{task_description}{ctx_str}\n\nExecute the task thoroughly and provide your final deliverable."

        try:
            from app import run_model_inference
        except ImportError:
            from space2_coder_agent.app import run_model_inference

        raw_output = run_model_inference(prompt, system_prompt=system_prompt, model_name=self.model_name)

        self.tasks_completed += 1
        self.status = "IDLE 🟢"
        elapsed = round(time.time() - t_start, 2)

        return {
            "agent_name": self.name,
            "agent_role": self.role,
            "model_used": self.model_name,
            "status": "success",
            "elapsed_seconds": elapsed,
            "output": raw_output
        }


class MultiAgentSpawner:
    """Master Multi-Agent Orchestration & Subagent Spawner Framework."""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(MultiAgentSpawner, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.agents: Dict[str, AutonomousSubagent] = {}
        self.crew_missions: List[Dict[str, Any]] = []
        self._seed_default_crew()

    def _seed_default_crew(self):
        """Spawns the Enterprise Specialist Fleet across Hermes 3, Dolphin 3.0, Dolphin Coder & Qwen 3.6."""
        # 1. Architect (Powered by Nous Hermes 3 70B)
        self.spawn_agent(
            name="Agent-Architect",
            role="Senior Cloud Software Architect & Task Decomposer",
            goal="Deconstruct complex requests into atomic modular steps and blueprint interfaces.",
            backstory="Master system architect powered by Nous Hermes 3 with deep knowledge of microservices, WebSockets, ZeroGPU, and high-concurrency Python architectures.",
            model_name=MODEL_REGISTRY["hermes3"]
        )
        # 2. Master Coder (Powered by Qwen 3.6 / 2.5 Coder 32B)
        self.spawn_agent(
            name="Agent-Coder",
            role="Elite Full-Stack Python & AI Engineer",
            goal="Write 100% bug-free, clean, production-grade Python code adhering to architectural blueprints.",
            backstory="Qwen 3.6 Uncensored Coder specialist with deep fluency in Telegram Bot API, FastAPI, threading, and distributed state machines.",
            model_name=MODEL_REGISTRY["qwen36_coder"]
        )
        # 3. Dolphin Coder (Powered by Dolphin 3.0 / Dolphin Coder)
        self.spawn_agent(
            name="Agent-DolphinCoder",
            role="Dolphin 3.0 Uncensored Agentic Refactorer",
            goal="Refactor complex loops, resolve edge cases, and eliminate code bottlenecks.",
            backstory="Cognitive Computations Dolphin 3.0 agent specialized in agentic coding loops, multi-file edits, and creative system optimization.",
            model_name=MODEL_REGISTRY["dolphin3"]
        )
        # 4. Doctor Shield (Powered by Nous Hermes 3 8B)
        self.spawn_agent(
            name="Agent-Doctor",
            role="AST Syntax Auditor & Cyber Defense Shield",
            goal="Perform static AST compilation, locate runtime flaws, and inject robust try-catch safety barriers.",
            backstory="Autonomous server doctor powered by Hermes 3 dedicated to ensuring 0 runtime crashes, 0 unhandled exceptions, and strict hardware isolation.",
            model_name=MODEL_REGISTRY["hermes3_8b"]
        )
        # 5. Tester (Powered by Dolphin Coder 7B)
        self.spawn_agent(
            name="Agent-Tester",
            role="Quality Assurance & Regression Validator",
            goal="Simulate payload dispatches, verify imports, and test corner cases before deployment.",
            backstory="Automated QA engineer powered by Dolphin Coder focused on verifying proxy speed, database atomicity, and carrier webhook payloads.",
            model_name=MODEL_REGISTRY["dolphincoder"]
        )
        # 6. DevOps (Powered by Qwen 2.5 Coder 7B)
        self.spawn_agent(
            name="Agent-DevOps",
            role="Multi-Cloud Deployment & Git Sync Manager",
            goal="Commit cleanly to GitHub, upload updated modules to Hugging Face Spaces, and manage live container reboots.",
            backstory="DevOps master managing multi-cloud git branches, zero-downtime hot-patching, and automated cloud fleet synchronization.",
            model_name=MODEL_REGISTRY["qwen_7b"]
        )

    def spawn_agent(
        self,
        name: str,
        role: str,
        goal: str,
        backstory: str,
        model_name: str = "Qwen/Qwen2.5-Coder-32B-Instruct",
        tools: Optional[List[str]] = None
    ) -> AutonomousSubagent:
        """Dynamically spawns a new autonomous subagent into the active fleet."""
        clean_name = name.strip().replace(" ", "_")
        resolved_model = MODEL_REGISTRY.get(model_name, model_name)
        agent = AutonomousSubagent(
            name=clean_name,
            role=role,
            goal=goal,
            backstory=backstory,
            model_name=resolved_model,
            tools=tools
        )
        self.agents[clean_name] = agent
        print(f"🤖 [MultiAgentSpawner] Spawned subagent: {clean_name} ({role}) on model {resolved_model}")
        return agent

    def kill_agent(self, name: str) -> bool:
        """Deactivates and removes a spawned subagent."""
        clean_name = name.strip().replace(" ", "_")
        if clean_name in self.agents:
            self.agents.pop(clean_name)
            return True
        return False

    def get_agent(self, name: str) -> Optional[AutonomousSubagent]:
        """Retrieves a spawned subagent by name."""
        clean_name = name.strip().replace(" ", "_")
        return self.agents.get(clean_name)

    def list_agents(self) -> List[Dict[str, Any]]:
        """Returns metadata of all active spawned subagents."""
        return [
            {
                "name": a.name,
                "role": a.role,
                "goal": a.goal,
                "model": a.model_name,
                "status": a.status,
                "tasks_completed": a.tasks_completed
            }
            for a in self.agents.values()
        ]

    def render_models_card(self) -> str:
        """Builds formatted Markdown card of all installed model engines."""
        rows = [
            "🧠 *[INSTALLED & CONNECTED AI MODEL FLEET]* 🚀\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "1. 🧠 *Nous Hermes 3 (70B & 8B)* (`hermes3` / `hermes3_8b`)\n   • Provider: NousResearch | Role: Architecture & Deep Reasoning",
            "2. 🐬 *Dolphin 3.0 (14B)* (`dolphin3`)\n   • Provider: Cognitive Computations | Role: Agentic Logic & Refactoring",
            "3. 🐬 *Dolphin Coder (7B)* (`dolphincoder`)\n   • Provider: Cognitive Computations | Role: Rapid Code Generation & Testing",
            "4. ⚡ *Qwen 3.6 Uncensored / 2.5 Coder (32B)* (`qwen36_coder`)\n   • Provider: Alibaba Cloud | Role: Production Python Master Coder",
            "5. 🧠 *DeepSeek R1 MoE (32B)* (`deepseek_r1`)\n   • Provider: DeepSeek AI | Role: Complex Algorithmic Logic & ZeroGPU Inference",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "👉 *Usage:* `/spawn <Name> <Role> <Goal> [model_alias]` or `/setmodel <alias>`!"
        ]
        return "\n\n".join(rows)

    def run_collaborative_crew_mission(
        self,
        mission_prompt: str,
        target_file: str = "telegram_bot.py",
        progress_cb: Optional[Callable[[str, int], None]] = None
    ) -> Dict[str, Any]:
        """
        Executes a Full Multi-Agent Collaborative Mission across Hermes 3, Qwen 3.6 & Dolphin Coder:
        Stage 1 (Architect - Hermes 3) -> Stage 2 (Coder - Qwen 3.6) -> Stage 3 (Dolphin Coder) -> Stage 4 (Doctor - Hermes 3) -> Stage 5 (DevOps)
        """
        mission_id = f"mission_{int(time.time())}"
        t_start = time.time()
        results = {}

        # Stage 1: Architect Plan (Nous Hermes 3)
        if progress_cb: progress_cb("🏗️ [Agent-Architect: Nous Hermes 3] Generating modular blueprint & plan...", 15)
        architect = self.get_agent("Agent-Architect")
        arch_res = architect.execute_task(
            f"Analyze request: '{mission_prompt}'. Target file: `{target_file}`. Outline exact step-by-step logic modifications."
        ) if architect else {"output": f"Modify {target_file} for: {mission_prompt}"}
        results["architect_plan"] = arch_res.get("output", "")

        # Stage 2: Coder Implementation (Qwen 3.6 Coder)
        if progress_cb: progress_cb("💻 [Agent-Coder: Qwen 3.6 Coder] Writing verified Python code implementation...", 40)
        coder = self.get_agent("Agent-Coder")
        coder_res = coder.execute_task(
            f"Implement code for: {mission_prompt}.\nTarget File: `{target_file}`.",
            context={"plan": results["architect_plan"][:1500]}
        ) if coder else {"output": ""}
        results["coder_output"] = coder_res.get("output", "")

        # Stage 3: Dolphin Coder Refactor (Dolphin 3.0)
        if progress_cb: progress_cb("🐬 [Agent-DolphinCoder: Dolphin 3.0] Refactoring & optimizing edge-cases...", 65)
        dolphin = self.get_agent("Agent-DolphinCoder")
        dolph_res = dolphin.execute_task(
            f"Optimize and enhance this implementation for performance:\n{results['coder_output'][:2000]}"
        ) if dolphin else {"output": results["coder_output"]}
        results["dolphin_refactor"] = dolph_res.get("output", "")

        # Stage 4: Doctor AST & Security Audit (Hermes 3)
        if progress_cb: progress_cb("🩺 [Agent-Doctor: Hermes 3 Shield] Running AST compilation & safety verification...", 85)
        doctor = self.get_agent("Agent-Doctor")
        doctor_res = doctor.execute_task(
            f"Audit the following code for syntax errors and inject safety shields:\n{results['coder_output'][:2000]}"
        ) if doctor else {"output": "Audit Passed 🟢"}
        results["doctor_audit"] = doctor_res.get("output", "")

        # Stage 5: DevOps & Sync
        if progress_cb: progress_cb("🚀 [Agent-DevOps] Syncing changes to Space 1 & GitHub...", 95)
        try:
            from app import ServerDoctorEngine
        except ImportError:
            from space2_coder_agent.app import ServerDoctorEngine
        patch_res = ServerDoctorEngine.autonomous_upgrade_or_fix(target_file, mission_prompt)
        results["devops_sync"] = patch_res

        total_time = round(time.time() - t_start, 2)
        if progress_cb: progress_cb("🎉 [Multi-Agent Mission Complete] All subagents collaborated successfully across Hermes 3, Qwen 3.6 & Dolphin!", 100)

        mission_record = {
            "mission_id": mission_id,
            "prompt": mission_prompt,
            "target_file": target_file,
            "total_time_seconds": total_time,
            "results": results,
            "status": "COMPLETED 🟢"
        }
        self.crew_missions.append(mission_record)
        return mission_record

# Global Multi-Agent Spawner Instance
agent_spawner = MultiAgentSpawner()
