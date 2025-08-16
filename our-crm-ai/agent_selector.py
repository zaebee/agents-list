#!/usr/bin/env python3
"""
Enhanced AI Agent Selector with Semantic Matching
Advanced agent selection with semantic analysis, context awareness, and learning capabilities.
"""

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import logging
from pathlib import Path
import re
from typing import Any

# Optional dependencies for semantic matching
try:
    import numpy as np
    from sentence_transformers import SentenceTransformer

    HAS_SEMANTIC = True
except ImportError:
    HAS_SEMANTIC = False
    np = None
    SentenceTransformer = None

try:
    import faiss

    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False
    faiss = None

import difflib

from exceptions import ConfigurationError
from models import AgentSuggestion

# Agent categories and keywords for intelligent task routing
AGENT_KEYWORDS = {
    # Programming Languages
    "python-pro": [
        "python",
        "django",
        "flask",
        "fastapi",
        "pandas",
        "numpy",
        "py",
        "pip",
        "pytest",
    ],
    "javascript-pro": [
        "javascript",
        "js",
        "node",
        "npm",
        "react",
        "vue",
        "angular",
        "express",
    ],
    "typescript-pro": ["typescript", "ts", "type", "interface", "generic", "tsc"],
    "golang-pro": ["go", "golang", "goroutine", "channel", "gin", "echo", "mod"],
    "rust-pro": ["rust", "cargo", "ownership", "lifetime", "borrow", "tokio", "serde"],
    "java-pro": ["java", "spring", "maven", "gradle", "jvm", "kotlin", "hibernate"],
    "csharp-pro": [
        "c#",
        "csharp",
        "dotnet",
        ".net",
        "asp.net",
        "entity framework",
        "nuget",
    ],
    "cpp-pro": ["c++", "cpp", "stl", "boost", "cmake", "template", "raii"],
    "c-pro": ["c language", "embedded", "system call", "memory", "pointer", "malloc"],
    "php-pro": ["php", "laravel", "symfony", "composer", "wordpress"],
    "scala-pro": [
        "scala",
        "akka",
        "spark",
        "sbt",
        "functional programming",
        "cats",
        "zio",
    ],
    "elixir-pro": ["elixir", "phoenix", "otp", "erlang", "genserver", "supervisor"],
    "sql-pro": ["sql", "database", "query", "mysql", "postgresql", "sqlite", "index"],
    # Frontend & Mobile
    "frontend-developer": [
        "frontend",
        "ui",
        "component",
        "css",
        "html",
        "responsive",
        "browser",
    ],
    "ui-ux-designer": [
        "design",
        "wireframe",
        "prototype",
        "user experience",
        "accessibility",
        "figma",
    ],
    "mobile-developer": [
        "mobile",
        "react native",
        "flutter",
        "ios",
        "android",
        "app store",
    ],
    "ios-developer": [
        "ios",
        "swift",
        "swiftui",
        "xcode",
        "app store",
        "iphone",
        "ipad",
    ],
    "unity-developer": [
        "unity",
        "game",
        "c# script",
        "gameobject",
        "3d",
        "2d",
        "animation",
    ],
    # Architecture & Backend
    "backend-architect": [
        "api",
        "microservice",
        "architecture",
        "service",
        "endpoint",
        "restful",
    ],
    "architect-reviewer": [
        "architecture",
        "design pattern",
        "solid",
        "review",
        "structure",
    ],
    "graphql-architect": ["graphql", "schema", "resolver", "federation", "apollo"],
    # Infrastructure & DevOps
    "cloud-architect": [
        "aws",
        "azure",
        "gcp",
        "cloud",
        "serverless",
        "lambda",
        "infrastructure",
    ],
    "devops-troubleshooter": [
        "deployment",
        "pipeline",
        "build",
        "ci/cd",
        "docker",
        "logs",
    ],
    "deployment-engineer": [
        "deploy",
        "ci/cd",
        "pipeline",
        "docker",
        "kubernetes",
        "github actions",
    ],
    "terraform-specialist": ["terraform", "infrastructure", "iac", "hcl", "tfstate"],
    "network-engineer": [
        "network",
        "dns",
        "ssl",
        "tls",
        "load balancer",
        "proxy",
        "firewall",
    ],
    "incident-responder": [
        "outage",
        "down",
        "incident",
        "emergency",
        "urgent",
        "critical",
    ],
    # Database & Data
    "database-optimizer": [
        "slow query",
        "performance",
        "index",
        "optimization",
        "explain",
    ],
    "database-admin": [
        "backup",
        "replication",
        "migration",
        "database admin",
        "user",
        "permission",
    ],
    "data-scientist": [
        "analysis",
        "sql",
        "bigquery",
        "data",
        "insight",
        "report",
        "metrics",
    ],
    "data-engineer": ["etl", "pipeline", "airflow", "kafka", "stream", "warehouse"],
    # AI & ML
    "ai-engineer": [
        "llm",
        "openai",
        "anthropic",
        "rag",
        "vector",
        "embedding",
        "chatbot",
    ],
    "ml-engineer": ["machine learning", "tensorflow", "pytorch", "model", "training"],
    "mlops-engineer": [
        "mlflow",
        "kubeflow",
        "experiment",
        "model registry",
        "ml pipeline",
    ],
    "prompt-engineer": ["prompt", "llm optimization", "ai prompt", "language model"],
    # Security & Quality
    "security-auditor": [
        "security",
        "vulnerability",
        "owasp",
        "auth",
        "encryption",
        "jwt",
    ],
    "code-reviewer": ["code review", "quality", "best practice", "refactor"],
    "test-automator": ["test", "testing", "unit test", "integration", "e2e", "mock"],
    "debugger": ["debug", "error", "bug", "issue", "troubleshoot", "fix"],
    "error-detective": ["log", "trace", "exception", "error analysis", "investigation"],
    # Performance & Monitoring
    "performance-engineer": [
        "performance",
        "optimization",
        "bottleneck",
        "slow",
        "cache",
    ],
    "search-specialist": [
        "search",
        "research",
        "investigation",
        "analysis",
        "competitive",
    ],
    # Documentation & Content
    "docs-architect": ["documentation", "technical writing", "manual", "guide"],
    "api-documenter": ["api doc", "openapi", "swagger", "endpoint documentation"],
    "reference-builder": ["reference", "api reference", "parameter", "configuration"],
    "tutorial-engineer": [
        "tutorial",
        "guide",
        "learning",
        "educational",
        "walkthrough",
    ],
    "mermaid-expert": ["diagram", "flowchart", "sequence", "architecture diagram"],
    "content-marketer": ["blog", "content", "marketing", "seo", "social media"],
    # Business & Support
    "business-analyst": [
        "metrics",
        "kpi",
        "analytics",
        "business",
        "revenue",
        "growth",
    ],
    "sales-automator": ["sales", "email", "lead", "proposal", "cold outreach"],
    "customer-support": ["support", "help", "faq", "customer", "ticket"],
    "legal-advisor": ["privacy", "terms", "legal", "gdpr", "compliance", "policy"],
    "risk-manager": ["risk", "portfolio", "trading", "position", "hedge"],
    "quant-analyst": ["financial", "trading", "backtest", "strategy", "market data"],
    # Specialized
    "payment-integration": ["payment", "stripe", "paypal", "checkout", "billing"],
    "legacy-modernizer": ["legacy", "migration", "modernize", "refactor", "upgrade"],
    "minecraft-bukkit-pro": ["minecraft", "bukkit", "spigot", "plugin", "server"],
    "dx-optimizer": ["developer experience", "tooling", "workflow", "setup"],
    "context-manager": ["multi-agent", "coordination", "context", "workflow"],
    "documentation-linter": [
        "documentation",
        "linter",
        "consistency",
        "sync",
        "update",
    ],
    "test-generator": ["test", "generator", "coverage", "unit", "integration", "e2e"],
    "project-scaffolder": ["scaffold", "generator", "project", "feature", "new"],
}


def fuzzy_keyword_match(text: str, keyword: str, threshold: float = 0.8) -> bool:
    """Use fuzzy matching for more flexible keyword detection."""
    words = text.lower().split()
    keyword_lower = keyword.lower()

    # Direct substring match (fastest)
    if keyword_lower in text.lower():
        return True

    # Fuzzy match against individual words
    for word in words:
        if difflib.SequenceMatcher(None, word, keyword_lower).ratio() >= threshold:
            return True

    # Fuzzy match against word combinations for multi-word keywords
    if " " in keyword_lower:
        keyword_words = keyword_lower.split()
        text_words = words

        for i in range(len(text_words) - len(keyword_words) + 1):
            text_phrase = " ".join(text_words[i : i + len(keyword_words)])
            if (
                difflib.SequenceMatcher(None, text_phrase, keyword_lower).ratio()
                >= threshold
            ):
                return True

    return False


@dataclass
class TaskOutcome:
    """Record of task outcome for learning."""

    task_id: str
    task_description: str
    assigned_agent: str
    success: bool
    completion_time_hours: float
    user_rating: float | None = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class SemanticMatch:
    """Semantic similarity match result."""

    agent_name: str
    similarity_score: float
    matched_embeddings: list[str]
    confidence: float


class SemanticMatcher:
    """Semantic similarity matcher using sentence transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        if not HAS_SEMANTIC:
            raise ConfigurationError(
                "sentence-transformers not available for semantic matching"
            )

        self.model_name = model_name
        self.model = None
        self.agent_embeddings = {}
        self.agent_descriptions = {}
        self.logger = logging.getLogger("semantic_matcher")

        # FAISS index for fast similarity search
        self.faiss_index = None
        self.agent_names_index = []

    def _load_model(self):
        """Lazy load the sentence transformer model."""
        if self.model is None:
            try:
                self.model = SentenceTransformer(self.model_name)
                self.logger.info(f"Loaded semantic model: {self.model_name}")
            except Exception as e:
                self.logger.error(f"Failed to load semantic model: {e}")
                raise ConfigurationError(f"Failed to load semantic model: {e!s}")

    def _create_agent_descriptions(
        self, agent_keywords: dict[str, list[str]]
    ) -> dict[str, str]:
        """Create rich descriptions for agents based on keywords."""
        descriptions = {}

        for agent_name, keywords in agent_keywords.items():
            # Create descriptive text from keywords
            keyword_text = " ".join(keywords)

            # Add contextual information based on agent type
            context = self._get_agent_context(agent_name)

            full_description = f"{agent_name} specialist: {keyword_text}. {context}"
            descriptions[agent_name] = full_description

        return descriptions

    def _get_agent_context(self, agent_name: str) -> str:
        """Get contextual description for agent."""
        contexts = {
            "python-pro": "Expert in Python development, frameworks, and ecosystem",
            "javascript-pro": "Specializes in JavaScript, Node.js, and web technologies",
            "frontend-developer": "Builds user interfaces and client-side applications",
            "backend-architect": "Designs and implements server-side architecture",
            "devops-troubleshooter": "Handles deployment, infrastructure, and operations",
            "security-auditor": "Focuses on security, vulnerabilities, and compliance",
            "data-scientist": "Analyzes data and builds predictive models",
            "ai-engineer": "Develops AI/ML systems and integrations",
            "documentation-linter": "Ensures documentation is consistent with the codebase",
            "test-generator": "Generates new tests for the codebase",
            "project-scaffolder": "Scaffolds new projects and features",
        }

        return contexts.get(agent_name, "Specialized technical expert")

    async def initialize_embeddings(self, agent_keywords: dict[str, list[str]]):
        """Initialize agent embeddings for semantic matching."""
        try:
            self._load_model()

            # Create rich descriptions
            self.agent_descriptions = self._create_agent_descriptions(agent_keywords)

            # Generate embeddings
            descriptions = list(self.agent_descriptions.values())
            agent_names = list(self.agent_descriptions.keys())

            embeddings = self.model.encode(descriptions)

            # Store embeddings
            for agent_name, embedding in zip(agent_names, embeddings, strict=False):
                self.agent_embeddings[agent_name] = embedding

            # Create FAISS index if available
            if HAS_FAISS and len(embeddings) > 0:
                dimension = embeddings[0].shape[0]
                self.faiss_index = faiss.IndexFlatIP(
                    dimension
                )  # Inner product for cosine similarity

                # Normalize embeddings for cosine similarity
                embeddings_normalized = embeddings / np.linalg.norm(
                    embeddings, axis=1, keepdims=True
                )
                self.faiss_index.add(embeddings_normalized.astype(np.float32))
                self.agent_names_index = agent_names

                self.logger.info(
                    f"Created FAISS index with {len(embeddings)} agent embeddings"
                )

            self.logger.info(f"Initialized embeddings for {len(agent_names)} agents")

        except Exception as e:
            self.logger.error(f"Failed to initialize embeddings: {e}")
            raise

    async def find_semantic_matches(
        self, task_description: str, top_k: int = 5
    ) -> list[SemanticMatch]:
        """Find semantically similar agents."""
        if not self.model or not self.agent_embeddings:
            return []

        try:
            # Encode task description
            task_embedding = self.model.encode([task_description])

            matches = []

            if self.faiss_index is not None and HAS_FAISS:
                # Use FAISS for fast similarity search
                task_embedding_normalized = task_embedding / np.linalg.norm(
                    task_embedding
                )

                similarities, indices = self.faiss_index.search(
                    task_embedding_normalized.astype(np.float32), top_k
                )

                for similarity, idx in zip(similarities[0], indices[0], strict=False):
                    if idx < len(self.agent_names_index):
                        agent_name = self.agent_names_index[idx]
                        confidence = min(float(similarity) * 100, 100.0)

                        matches.append(
                            SemanticMatch(
                                agent_name=agent_name,
                                similarity_score=float(similarity),
                                matched_embeddings=[
                                    self.agent_descriptions[agent_name]
                                ],
                                confidence=confidence,
                            )
                        )

            else:
                # Fallback to manual similarity calculation
                similarities = {}

                for agent_name, agent_embedding in self.agent_embeddings.items():
                    # Calculate cosine similarity
                    similarity = np.dot(task_embedding[0], agent_embedding) / (
                        np.linalg.norm(task_embedding[0])
                        * np.linalg.norm(agent_embedding)
                    )
                    similarities[agent_name] = float(similarity)

                # Sort by similarity and take top k
                sorted_agents = sorted(
                    similarities.items(), key=lambda x: x[1], reverse=True
                )

                for agent_name, similarity in sorted_agents[:top_k]:
                    confidence = min(similarity * 100, 100.0)

                    matches.append(
                        SemanticMatch(
                            agent_name=agent_name,
                            similarity_score=similarity,
                            matched_embeddings=[self.agent_descriptions[agent_name]],
                            confidence=confidence,
                        )
                    )

            return matches

        except Exception as e:
            self.logger.error(f"Semantic matching failed: {e}")
            return []


class LearningSystem:
    """Learning system that improves agent selection based on outcomes."""

    def __init__(self, storage_path: str = "agent_learning.json"):
        self.storage_path = Path(storage_path)
        self.outcomes: list[TaskOutcome] = []
        self.agent_performance: dict[str, dict[str, Any]] = {}
        self.logger = logging.getLogger("learning_system")

        self._load_data()

    def _load_data(self):
        """Load learning data from storage."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path) as f:
                    data = json.load(f)

                # Load outcomes
                for outcome_data in data.get("outcomes", []):
                    outcome = TaskOutcome(
                        task_id=outcome_data["task_id"],
                        task_description=outcome_data["task_description"],
                        assigned_agent=outcome_data["assigned_agent"],
                        success=outcome_data["success"],
                        completion_time_hours=outcome_data["completion_time_hours"],
                        user_rating=outcome_data.get("user_rating"),
                        timestamp=datetime.fromisoformat(outcome_data["timestamp"]),
                    )
                    self.outcomes.append(outcome)

                # Load performance data
                self.agent_performance = data.get("agent_performance", {})

                self.logger.info(f"Loaded {len(self.outcomes)} task outcomes")

            except Exception as e:
                self.logger.warning(f"Failed to load learning data: {e}")

    def _save_data(self):
        """Save learning data to storage."""
        try:
            data = {
                "outcomes": [
                    {
                        "task_id": outcome.task_id,
                        "task_description": outcome.task_description,
                        "assigned_agent": outcome.assigned_agent,
                        "success": outcome.success,
                        "completion_time_hours": outcome.completion_time_hours,
                        "user_rating": outcome.user_rating,
                        "timestamp": outcome.timestamp.isoformat(),
                    }
                    for outcome in self.outcomes
                ],
                "agent_performance": self.agent_performance,
            }

            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            self.logger.error(f"Failed to save learning data: {e}")

    def record_outcome(self, outcome: TaskOutcome):
        """Record a task outcome for learning."""
        self.outcomes.append(outcome)
        self._update_agent_performance(outcome)
        self._save_data()

        self.logger.info(f"Recorded outcome for agent {outcome.assigned_agent}")

    def _update_agent_performance(self, outcome: TaskOutcome):
        """Update agent performance metrics."""
        agent_name = outcome.assigned_agent

        if agent_name not in self.agent_performance:
            self.agent_performance[agent_name] = {
                "total_tasks": 0,
                "successful_tasks": 0,
                "total_hours": 0.0,
                "success_rate": 0.0,
                "average_completion_time": 0.0,
                "user_ratings": [],
                "task_types": {},
            }

        perf = self.agent_performance[agent_name]

        # Update counters
        perf["total_tasks"] += 1
        if outcome.success:
            perf["successful_tasks"] += 1

        perf["total_hours"] += outcome.completion_time_hours

        # Calculate averages
        perf["success_rate"] = perf["successful_tasks"] / perf["total_tasks"]
        perf["average_completion_time"] = perf["total_hours"] / perf["total_tasks"]

        # Track user ratings
        if outcome.user_rating is not None:
            perf["user_ratings"].append(outcome.user_rating)

        # Track task types (simple keyword extraction)
        task_hash = self._extract_task_type(outcome.task_description)
        if task_hash not in perf["task_types"]:
            perf["task_types"][task_hash] = {
                "count": 0,
                "success_rate": 0.0,
                "keywords": self._extract_keywords(outcome.task_description),
            }

        task_type_perf = perf["task_types"][task_hash]
        task_type_perf["count"] += 1
        if outcome.success:
            task_type_perf["success_rate"] = (
                task_type_perf["success_rate"] * (task_type_perf["count"] - 1) + 1.0
            ) / task_type_perf["count"]
        else:
            task_type_perf["success_rate"] = (
                task_type_perf["success_rate"]
                * (task_type_perf["count"] - 1)
                / task_type_perf["count"]
            )

    def _extract_task_type(self, description: str) -> str:
        """Extract task type hash for categorization."""
        # Simple keyword-based hashing
        keywords = self._extract_keywords(description)
        keyword_str = " ".join(sorted(keywords[:5]))  # Use top 5 keywords
        return hashlib.md5(keyword_str.encode()).hexdigest()[:8]

    def _extract_keywords(self, text: str) -> list[str]:
        """Extract relevant keywords from text."""
        # Simple keyword extraction
        words = re.findall(r"\b\w+\b", text.lower())

        # Filter common words
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
        }
        keywords = [word for word in words if len(word) > 3 and word not in stop_words]

        return keywords[:10]  # Return top 10 keywords

    def get_agent_performance_score(
        self, agent_name: str, task_description: str
    ) -> float:
        """Get performance-adjusted score for agent."""
        if agent_name not in self.agent_performance:
            return 1.0  # Default neutral score

        perf = self.agent_performance[agent_name]

        # Base score from success rate
        base_score = perf["success_rate"]

        # Adjust for task similarity
        task_hash = self._extract_task_type(task_description)
        if task_hash in perf["task_types"]:
            task_type_score = perf["task_types"][task_hash]["success_rate"]
            # Weight task-specific performance more heavily
            adjusted_score = (base_score * 0.3) + (task_type_score * 0.7)
        else:
            adjusted_score = base_score

        # Factor in user ratings if available
        if perf["user_ratings"]:
            avg_rating = sum(perf["user_ratings"]) / len(perf["user_ratings"])
            rating_score = avg_rating / 5.0  # Normalize to 0-1
            adjusted_score = (adjusted_score * 0.8) + (rating_score * 0.2)

        return max(0.1, adjusted_score)  # Minimum score to avoid complete exclusion

    def get_performance_insights(self) -> dict[str, Any]:
        """Get insights from learning data."""
        if not self.outcomes:
            return {"message": "No learning data available"}

        insights = {
            "total_outcomes": len(self.outcomes),
            "overall_success_rate": sum(1 for o in self.outcomes if o.success)
            / len(self.outcomes),
            "top_performers": [],
            "underperformers": [],
            "average_completion_time": sum(
                o.completion_time_hours for o in self.outcomes
            )
            / len(self.outcomes),
        }

        # Rank agents by performance
        agent_scores = []
        for agent_name, perf in self.agent_performance.items():
            if perf["total_tasks"] >= 3:  # Minimum tasks for reliable statistics
                agent_scores.append(
                    (agent_name, perf["success_rate"], perf["total_tasks"])
                )

        agent_scores.sort(key=lambda x: x[1], reverse=True)

        insights["top_performers"] = agent_scores[:5]
        insights["underperformers"] = agent_scores[-3:] if len(agent_scores) > 5 else []

        return insights


class EnhancedAgentSelector:
    """
    Enhanced agent selector with semantic matching, learning, and context awareness.
    """

    def __init__(self, enable_semantic: bool = None):
        self.logger = logging.getLogger("enhanced_agent_selector")

        # Auto-detect semantic capabilities
        if enable_semantic is None:
            enable_semantic = HAS_SEMANTIC

        self.enable_semantic = enable_semantic
        self.semantic_matcher = None
        self.learning_system = LearningSystem()

        # Original keyword-based matching
        self.agent_keywords = AGENT_KEYWORDS

        # Performance weights for different matching methods
        self.method_weights = {
            "keyword": 0.4,
            "semantic": 0.4 if enable_semantic else 0.0,
            "learning": 0.2,
        }

        # Normalize weights
        total_weight = sum(self.method_weights.values())
        self.method_weights = {
            k: v / total_weight for k, v in self.method_weights.items()
        }

    async def initialize(self):
        """Initialize the enhanced agent selector."""
        try:
            if self.enable_semantic:
                self.semantic_matcher = SemanticMatcher()
                await self.semantic_matcher.initialize_embeddings(self.agent_keywords)
                self.logger.info("Semantic matching enabled")
            else:
                self.logger.info(
                    "Semantic matching disabled (dependencies not available)"
                )

        except Exception as e:
            self.logger.warning(f"Failed to initialize semantic matching: {e}")
            self.enable_semantic = False

    def _keyword_match_score(
        self, task_description: str, agent_keywords: list[str]
    ) -> tuple[float, list[str]]:
        """Calculate keyword matching score."""
        task_lower = task_description.lower()
        matched_keywords = []
        score = 0.0
        context_score = 0.0

        for keyword in agent_keywords:
            if fuzzy_keyword_match(task_lower, keyword, threshold=0.75):
                matched_keywords.append(keyword)
                # Weight multi-word keywords higher
                score += len(keyword.split()) ** 2

        # Context score
        if matched_keywords:
            for i in range(len(matched_keywords)):
                for j in range(i + 1, len(matched_keywords)):
                    if (
                        matched_keywords[i] in task_lower
                        and matched_keywords[j] in task_lower
                    ):
                        context_score += 1

        # Normalize by the number of matched keywords and total keywords
        if matched_keywords:
            # Factor in the ratio of matched keywords to total keywords
            specificity_factor = len(matched_keywords) / len(agent_keywords)
            normalized_score = (
                (score / len(agent_keywords)) * specificity_factor
            ) + context_score
        else:
            normalized_score = 0.0

        return normalized_score, matched_keywords

    async def suggest_agents(
        self,
        task_description: str,
        max_suggestions: int = 5,
        context: dict[str, Any] | None = None,
    ) -> list[AgentSuggestion]:
        """
        Suggest agents using multiple matching methods and learning.
        """
        if not task_description or not task_description.strip():
            return []
        try:
            agent_scores = {}
            all_matched_keywords = {}

            # 1. Keyword-based matching
            for agent_name, keywords in self.agent_keywords.items():
                keyword_score, matched_keywords = self._keyword_match_score(
                    task_description, keywords
                )
                agent_scores[agent_name] = {
                    "keyword_score": keyword_score,
                    "semantic_score": 0.0,
                    "learning_score": 1.0,  # Default neutral
                    "matched_keywords": matched_keywords,
                }
                all_matched_keywords[agent_name] = matched_keywords

            # 2. Semantic matching (if available)
            if self.semantic_matcher:
                semantic_matches = await self.semantic_matcher.find_semantic_matches(
                    task_description, top_k=len(self.agent_keywords)
                )

                for match in semantic_matches:
                    if match.agent_name in agent_scores:
                        agent_scores[match.agent_name]["semantic_score"] = (
                            match.similarity_score
                        )

            # 3. Learning-based adjustment
            for agent_name in agent_scores:
                learning_score = self.learning_system.get_agent_performance_score(
                    agent_name, task_description
                )
                agent_scores[agent_name]["learning_score"] = learning_score

            # 4. Calculate composite scores
            suggestions = []
            for agent_name, scores in agent_scores.items():
                composite_score = (
                    scores["keyword_score"] * self.method_weights["keyword"]
                    + scores["semantic_score"] * self.method_weights["semantic"]
                    + scores["learning_score"] * self.method_weights["learning"]
                )

                # Only include agents with positive scores
                if composite_score > 0.01:
                    confidence = min(composite_score * 100, 100.0)

                    # Create reasoning
                    reasoning_parts = []
                    if scores["matched_keywords"]:
                        reasoning_parts.append(
                            f"Keywords: {', '.join(scores['matched_keywords'][:3])}"
                        )
                    if scores["semantic_score"] > 0.1:
                        reasoning_parts.append(
                            f"Semantic similarity: {scores['semantic_score']:.2f}"
                        )
                    if scores["learning_score"] != 1.0:
                        reasoning_parts.append(
                            f"Performance factor: {scores['learning_score']:.2f}"
                        )

                    reasoning = (
                        "; ".join(reasoning_parts) if reasoning_parts else "Basic match"
                    )

                    suggestions.append(
                        AgentSuggestion(
                            agent_name=agent_name,
                            confidence=confidence,
                            reasoning=reasoning,
                            matched_keywords=scores["matched_keywords"],
                            workload_factor=1.0,  # Will be updated by service layer
                            availability_status="unknown",  # Will be updated by service layer
                        )
                    )

            # Sort by confidence and return top suggestions
            suggestions.sort(key=lambda x: x.confidence, reverse=True)

            self.logger.info(f"Generated {len(suggestions)} agent suggestions for task")

            return suggestions[:max_suggestions]

        except Exception as e:
            self.logger.error(f"Agent suggestion failed: {e}")
            return []

    def record_task_outcome(
        self,
        task_id: str,
        task_description: str,
        assigned_agent: str,
        success: bool,
        completion_time_hours: float,
        user_rating: float | None = None,
    ):
        """Record task outcome for learning."""
        outcome = TaskOutcome(
            task_id=task_id,
            task_description=task_description,
            assigned_agent=assigned_agent,
            success=success,
            completion_time_hours=completion_time_hours,
            user_rating=user_rating,
        )

        self.learning_system.record_outcome(outcome)
        self.logger.info(f"Recorded outcome for task {task_id}")

    def get_learning_insights(self) -> dict[str, Any]:
        """Get insights from the learning system."""
        return self.learning_system.get_performance_insights()


# Factory function and backward compatibility
_enhanced_selector = None


async def get_enhanced_selector() -> EnhancedAgentSelector:
    """Get initialized enhanced selector instance."""
    global _enhanced_selector

    if _enhanced_selector is None:
        _enhanced_selector = EnhancedAgentSelector()
        await _enhanced_selector.initialize()

    return _enhanced_selector


# Backward compatibility functions
def suggest_agents(
    task_description: str, max_suggestions: int = 5
) -> list[dict[str, Any]]:
    """Backward compatibility function for original agent selector interface."""
    try:
        # Use async wrapper
        import asyncio

        async def async_suggest():
            selector = await get_enhanced_selector()
            suggestions = await selector.suggest_agents(
                task_description, max_suggestions
            )

            # Convert to original format
            return [
                {
                    "agent": s.agent_name,
                    "confidence": s.confidence,
                    "matched_keywords": s.matched_keywords,
                    "reasoning": s.reasoning,
                }
                for s in suggestions
            ]

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Create new event loop for nested async call
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, async_suggest())
                    return future.result(timeout=30)
            else:
                return asyncio.run(async_suggest())
        except RuntimeError:
            return asyncio.run(async_suggest())

    except Exception as e:
        logging.error(f"Enhanced suggestion failed, falling back to basic: {e}")

        # Fallback to basic keyword matching
        # This part is being removed as the functionality is now self-contained.

        return []
