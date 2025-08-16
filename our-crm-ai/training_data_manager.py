#!/usr/bin/env python3
"""
Training Data Manager - Advanced data collection, curation, and management system.

This module provides:
1. Automated training data collection from CRM interactions
2. Data quality assessment and validation
3. Domain-specific data augmentation
4. Training dataset versioning and management
5. Privacy and compliance features
"""

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import hashlib
import json
import logging
import re
import sqlite3
from typing import Any
import uuid

# Privacy and security imports
from cryptography.fernet import Fernet


class DataQualityScore(Enum):
    """Data quality scoring levels."""

    EXCELLENT = 5
    GOOD = 4
    ACCEPTABLE = 3
    POOR = 2
    UNUSABLE = 1


class DataSource(Enum):
    """Sources of training data."""

    USER_INTERACTION = "user_interaction"
    TASK_COMPLETION = "task_completion"
    PM_GATEWAY_DECISION = "pm_gateway_decision"
    AGENT_COLLABORATION = "agent_collaboration"
    ERROR_CORRECTION = "error_correction"
    EXPERT_ANNOTATION = "expert_annotation"
    SYNTHETIC_GENERATION = "synthetic_generation"


class PrivacyLevel(Enum):
    """Privacy levels for training data."""

    PUBLIC = 1
    INTERNAL = 2
    CONFIDENTIAL = 3
    RESTRICTED = 4


@dataclass
class TrainingDataset:
    """Training dataset metadata and versioning."""

    dataset_id: str
    name: str
    version: str
    agent_name: str
    creation_date: datetime
    data_sources: list[DataSource]
    quality_metrics: dict[str, float]
    size: int
    privacy_level: PrivacyLevel
    validation_status: str
    tags: list[str]
    description: str


@dataclass
class DataValidationRule:
    """Data validation rule definition."""

    rule_id: str
    name: str
    description: str
    agent_names: list[str]
    validation_function: str
    severity: str  # 'error', 'warning', 'info'
    enabled: bool


class TrainingDataCurator:
    """Advanced training data curation and quality management."""

    def __init__(self, db_path: str = "training_data.db", encryption_key: bytes = None):
        """Initialize training data curator."""
        self.db_path = db_path
        self.encryption_key = encryption_key or Fernet.generate_key()
        self.fernet = Fernet(self.encryption_key)
        self.validation_rules = []
        self.quality_cache = {}
        self.augmentation_templates = {}
        self.setup_database()
        self.load_validation_rules()
        self.load_augmentation_templates()

    def setup_database(self):
        """Setup advanced database schema for training data management."""
        with sqlite3.connect(self.db_path) as conn:
            # Enhanced training data table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS training_data_v2 (
                    id TEXT PRIMARY KEY,
                    dataset_id TEXT,
                    agent_name TEXT NOT NULL,
                    data_source TEXT NOT NULL,
                    input_text TEXT NOT NULL,
                    expected_output TEXT,
                    actual_output TEXT,
                    context_data TEXT,  -- JSON blob
                    quality_score REAL DEFAULT 0.0,
                    privacy_level INTEGER DEFAULT 2,
                    validation_status TEXT DEFAULT 'pending',
                    validation_errors TEXT,  -- JSON array
                    created_at TEXT,
                    updated_at TEXT,
                    tags TEXT,  -- JSON array
                    metadata TEXT,  -- JSON blob
                    content_hash TEXT,
                    encrypted_fields TEXT  -- JSON with encrypted sensitive data
                )
            """)

            # Dataset management table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS training_datasets (
                    dataset_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    version TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    creation_date TEXT,
                    data_sources TEXT,  -- JSON array
                    quality_metrics TEXT,  -- JSON object
                    size INTEGER DEFAULT 0,
                    privacy_level INTEGER,
                    validation_status TEXT,
                    tags TEXT,  -- JSON array
                    description TEXT
                )
            """)

            # Data validation rules table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS validation_rules (
                    rule_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    agent_names TEXT,  -- JSON array
                    validation_function TEXT,
                    severity TEXT,
                    enabled INTEGER DEFAULT 1,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)

            # Data augmentation templates
            conn.execute("""
                CREATE TABLE IF NOT EXISTS augmentation_templates (
                    template_id TEXT PRIMARY KEY,
                    agent_name TEXT NOT NULL,
                    template_type TEXT,
                    template_data TEXT,  -- JSON object
                    success_rate REAL DEFAULT 0.0,
                    usage_count INTEGER DEFAULT 0,
                    created_at TEXT
                )
            """)

            # Performance tracking for data quality
            conn.execute("""
                CREATE TABLE IF NOT EXISTS data_quality_metrics (
                    metric_id TEXT PRIMARY KEY,
                    dataset_id TEXT,
                    metric_name TEXT,
                    metric_value REAL,
                    benchmark_value REAL,
                    measured_at TEXT,
                    notes TEXT
                )
            """)

    def load_validation_rules(self):
        """Load data validation rules."""
        default_rules = [
            DataValidationRule(
                rule_id="min_input_length",
                name="Minimum Input Length",
                description="Input text must be at least 10 characters",
                agent_names=["*"],  # All agents
                validation_function="len(input_text) >= 10",
                severity="warning",
                enabled=True,
            ),
            DataValidationRule(
                rule_id="no_sensitive_data",
                name="No Sensitive Data",
                description="Check for potential sensitive information",
                agent_names=["*"],
                validation_function="not contains_sensitive_patterns(input_text)",
                severity="error",
                enabled=True,
            ),
            DataValidationRule(
                rule_id="output_quality_check",
                name="Output Quality Check",
                description="Expected output should be meaningful",
                agent_names=["*"],
                validation_function="is_meaningful_output(expected_output)",
                severity="warning",
                enabled=True,
            ),
            DataValidationRule(
                rule_id="domain_relevance",
                name="Domain Relevance",
                description="Content should be relevant to agent domain",
                agent_names=["python-pro", "javascript-pro", "database-optimizer"],
                validation_function="check_domain_relevance(agent_name, input_text)",
                severity="info",
                enabled=True,
            ),
        ]

        self.validation_rules = default_rules

        # Load from database if exists
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT * FROM validation_rules WHERE enabled = 1"
                )
                for row in cursor.fetchall():
                    rule = DataValidationRule(
                        rule_id=row[0],
                        name=row[1],
                        description=row[2],
                        agent_names=json.loads(row[3]) if row[3] else ["*"],
                        validation_function=row[4],
                        severity=row[5],
                        enabled=bool(row[6]),
                    )

                    # Replace default rule if exists
                    existing_idx = next(
                        (
                            i
                            for i, r in enumerate(self.validation_rules)
                            if r.rule_id == rule.rule_id
                        ),
                        None,
                    )
                    if existing_idx is not None:
                        self.validation_rules[existing_idx] = rule
                    else:
                        self.validation_rules.append(rule)
        except sqlite3.Error:
            pass  # Use defaults if database doesn't exist yet

    def load_augmentation_templates(self):
        """Load data augmentation templates."""
        self.augmentation_templates = {
            "python-pro": [
                {
                    "type": "code_variation",
                    "template": "Rewrite this Python code using {alternative}: {original_code}",
                    "alternatives": [
                        "list comprehension",
                        "lambda functions",
                        "generator expressions",
                        "functional approach",
                    ],
                },
                {
                    "type": "error_injection",
                    "template": "Debug this Python code that has a {error_type}: {buggy_code}",
                    "error_types": [
                        "syntax error",
                        "runtime error",
                        "logic error",
                        "performance issue",
                    ],
                },
            ],
            "frontend-developer": [
                {
                    "type": "component_variation",
                    "template": "Create a {component_type} component for {use_case}",
                    "component_types": ["React", "Vue", "Angular", "Svelte"],
                    "use_cases": [
                        "user authentication",
                        "data visualization",
                        "form handling",
                        "navigation",
                    ],
                }
            ],
            "database-optimizer": [
                {
                    "type": "query_optimization",
                    "template": "Optimize this {db_type} query for better performance: {original_query}",
                    "db_types": ["MySQL", "PostgreSQL", "MongoDB", "Redis"],
                }
            ],
            "security-auditor": [
                {
                    "type": "vulnerability_analysis",
                    "template": "Analyze this code for {vulnerability_type} vulnerabilities: {code}",
                    "vulnerability_types": [
                        "SQL injection",
                        "XSS",
                        "CSRF",
                        "authentication bypass",
                    ],
                }
            ],
        }

    def validate_training_data(self, data_point: dict) -> tuple[bool, list[dict]]:
        """Validate a training data point against all applicable rules."""
        agent_name = data_point.get("agent_name", "")
        input_text = data_point.get("input_text", "")
        expected_output = data_point.get("expected_output", "")

        validation_errors = []
        is_valid = True

        for rule in self.validation_rules:
            if not rule.enabled:
                continue

            # Check if rule applies to this agent
            if "*" not in rule.agent_names and agent_name not in rule.agent_names:
                continue

            try:
                # Execute validation function
                result = self._execute_validation_function(
                    rule.validation_function, data_point
                )

                if not result:
                    error = {
                        "rule_id": rule.rule_id,
                        "rule_name": rule.name,
                        "severity": rule.severity,
                        "message": rule.description,
                    }
                    validation_errors.append(error)

                    if rule.severity == "error":
                        is_valid = False

            except Exception as e:
                logging.warning(f"Validation rule {rule.rule_id} failed: {e}")

        return is_valid, validation_errors

    def _execute_validation_function(
        self, function_code: str, data_point: dict
    ) -> bool:
        """Execute validation function safely."""
        # Extract variables for validation
        input_text = data_point.get("input_text", "")
        expected_output = data_point.get("expected_output", "")
        agent_name = data_point.get("agent_name", "")

        # Define safe validation functions
        def contains_sensitive_patterns(text: str) -> bool:
            """Check for sensitive patterns in text."""
            sensitive_patterns = [
                r"\b\d{4}-\d{4}-\d{4}-\d{4}\b",  # Credit card
                r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
                r"\b[\w\.-]+@[\w\.-]+\.\w+\b",  # Email (basic)
                r"\b(?:\d{1,3}\.){3}\d{1,3}\b",  # IP address
                r"password\s*[:=]\s*\S+",  # Password
                r"api[_\s]*key\s*[:=]\s*\S+",  # API key
            ]

            for pattern in sensitive_patterns:
                if re.search(pattern, text.lower()):
                    return True
            return False

        def is_meaningful_output(output: str) -> bool:
            """Check if output is meaningful."""
            if not output or len(output.strip()) < 5:
                return False

            # Check for common non-meaningful responses
            meaningless_responses = [
                "ok",
                "yes",
                "no",
                "done",
                "error",
                "failed",
                "success",
                "true",
                "false",
                "...",
                "todo",
            ]

            return output.lower().strip() not in meaningless_responses

        def check_domain_relevance(agent_name: str, text: str) -> bool:
            """Check if text is relevant to agent domain."""
            from agent_selector import AGENT_KEYWORDS

            if agent_name not in AGENT_KEYWORDS:
                return True  # Default to true for unknown agents

            agent_keywords = AGENT_KEYWORDS[agent_name]
            text_lower = text.lower()

            # Check if any agent keywords appear in the text
            for keyword in agent_keywords:
                if keyword.lower() in text_lower:
                    return True

            return False

        # Safe execution environment
        safe_globals = {
            "len": len,
            "input_text": input_text,
            "expected_output": expected_output,
            "agent_name": agent_name,
            "contains_sensitive_patterns": contains_sensitive_patterns,
            "is_meaningful_output": is_meaningful_output,
            "check_domain_relevance": check_domain_relevance,
            # Add more safe functions as needed
        }

        try:
            return bool(eval(function_code, {"__builtins__": {}}, safe_globals))
        except Exception:
            return False

    def calculate_data_quality_score(self, data_point: dict) -> float:
        """Calculate comprehensive quality score for a data point."""
        score = 0.0
        max_score = 100.0

        # Input quality (20 points)
        input_text = data_point.get("input_text", "")
        if len(input_text) >= 50:
            score += 20
        elif len(input_text) >= 20:
            score += 15
        elif len(input_text) >= 10:
            score += 10

        # Output quality (25 points)
        expected_output = data_point.get("expected_output", "")
        if expected_output and len(expected_output) >= 20:
            score += 25
        elif expected_output and len(expected_output) >= 10:
            score += 15
        elif expected_output:
            score += 10

        # Context richness (15 points)
        context = data_point.get("context_data", {})
        if isinstance(context, dict):
            context_keys = len(context.keys())
            score += min(context_keys * 3, 15)

        # Domain relevance (20 points)
        agent_name = data_point.get("agent_name", "")
        if self._check_domain_relevance(agent_name, input_text):
            score += 20

        # Validation status (10 points)
        is_valid, errors = self.validate_training_data(data_point)
        if is_valid:
            score += 10
        elif len(errors) == 0:
            score += 5

        # Performance score bonus (10 points)
        performance_score = data_point.get("performance_score", 0.0)
        if performance_score > 0.8:
            score += 10
        elif performance_score > 0.6:
            score += 7
        elif performance_score > 0.4:
            score += 4

        return min(score / max_score, 1.0)

    def _check_domain_relevance(self, agent_name: str, text: str) -> bool:
        """Check domain relevance for quality scoring."""
        try:
            return self._execute_validation_function(
                "check_domain_relevance(agent_name, input_text)",
                {"agent_name": agent_name, "input_text": text},
            )
        except:
            return False

    def create_training_dataset(
        self,
        name: str,
        agent_name: str,
        data_sources: list[DataSource],
        description: str = "",
        tags: list[str] = None,
    ) -> str:
        """Create a new training dataset."""
        dataset_id = str(uuid.uuid4())

        dataset = TrainingDataset(
            dataset_id=dataset_id,
            name=name,
            version="1.0",
            agent_name=agent_name,
            creation_date=datetime.now(),
            data_sources=data_sources,
            quality_metrics={},
            size=0,
            privacy_level=PrivacyLevel.INTERNAL,
            validation_status="created",
            tags=tags or [],
            description=description,
        )

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO training_datasets 
                (dataset_id, name, version, agent_name, creation_date, data_sources,
                 quality_metrics, size, privacy_level, validation_status, tags, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    dataset.dataset_id,
                    dataset.name,
                    dataset.version,
                    dataset.agent_name,
                    dataset.creation_date.isoformat(),
                    json.dumps([ds.value for ds in dataset.data_sources]),
                    json.dumps(dataset.quality_metrics),
                    dataset.size,
                    dataset.privacy_level.value,
                    dataset.validation_status,
                    json.dumps(dataset.tags),
                    dataset.description,
                ),
            )

        logging.info(f"Created training dataset {dataset_id} for agent {agent_name}")
        return dataset_id

    def add_data_to_dataset(
        self, dataset_id: str, data_points: list[dict]
    ) -> dict[str, int]:
        """Add training data points to a dataset."""
        results = {"added": 0, "rejected": 0, "validation_errors": 0}

        with sqlite3.connect(self.db_path) as conn:
            for data_point in data_points:
                # Validate data point
                is_valid, validation_errors = self.validate_training_data(data_point)

                # Calculate quality score
                quality_score = self.calculate_data_quality_score(data_point)

                # Generate content hash for deduplication
                content_hash = self._generate_content_hash(data_point)

                # Check for duplicates
                cursor = conn.execute(
                    "SELECT id FROM training_data_v2 WHERE content_hash = ?",
                    (content_hash,),
                )
                if cursor.fetchone():
                    results["rejected"] += 1
                    continue

                # Encrypt sensitive fields if needed
                encrypted_fields = self._encrypt_sensitive_fields(data_point)

                # Insert data point
                data_id = str(uuid.uuid4())
                conn.execute(
                    """
                    INSERT INTO training_data_v2 
                    (id, dataset_id, agent_name, data_source, input_text, expected_output,
                     actual_output, context_data, quality_score, privacy_level,
                     validation_status, validation_errors, created_at, updated_at,
                     tags, metadata, content_hash, encrypted_fields)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        data_id,
                        dataset_id,
                        data_point.get("agent_name", ""),
                        data_point.get(
                            "data_source", DataSource.USER_INTERACTION.value
                        ),
                        data_point.get("input_text", ""),
                        data_point.get("expected_output", ""),
                        data_point.get("actual_output", ""),
                        json.dumps(data_point.get("context_data", {})),
                        quality_score,
                        data_point.get("privacy_level", PrivacyLevel.INTERNAL.value),
                        "valid" if is_valid else "invalid",
                        json.dumps(validation_errors),
                        datetime.now().isoformat(),
                        datetime.now().isoformat(),
                        json.dumps(data_point.get("tags", [])),
                        json.dumps(data_point.get("metadata", {})),
                        content_hash,
                        json.dumps(encrypted_fields),
                    ),
                )

                if is_valid:
                    results["added"] += 1
                else:
                    results["validation_errors"] += 1

            # Update dataset size
            conn.execute(
                """
                UPDATE training_datasets 
                SET size = (
                    SELECT COUNT(*) FROM training_data_v2 
                    WHERE dataset_id = ? AND validation_status = 'valid'
                )
                WHERE dataset_id = ?
            """,
                (dataset_id, dataset_id),
            )

        return results

    def _generate_content_hash(self, data_point: dict) -> str:
        """Generate hash for content deduplication."""
        content = f"{data_point.get('agent_name', '')}{data_point.get('input_text', '')}{data_point.get('expected_output', '')}"
        return hashlib.sha256(content.encode()).hexdigest()

    def _encrypt_sensitive_fields(self, data_point: dict) -> dict:
        """Encrypt sensitive fields in data point."""
        sensitive_fields = ["actual_output", "context_data"]
        encrypted = {}

        for field in sensitive_fields:
            if data_point.get(field):
                try:
                    value = (
                        json.dumps(data_point[field])
                        if isinstance(data_point[field], dict)
                        else str(data_point[field])
                    )
                    encrypted[field] = self.fernet.encrypt(value.encode()).decode()
                except Exception as e:
                    logging.warning(f"Failed to encrypt field {field}: {e}")

        return encrypted

    def augment_training_data(
        self, dataset_id: str, agent_name: str, augmentation_factor: float = 2.0
    ) -> int:
        """Generate augmented training data using templates."""
        if agent_name not in self.augmentation_templates:
            logging.warning(f"No augmentation templates for agent {agent_name}")
            return 0

        # Get existing data
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT input_text, expected_output, context_data 
                FROM training_data_v2 
                WHERE dataset_id = ? AND validation_status = 'valid'
                AND quality_score > 0.6
                LIMIT 100
            """,
                (dataset_id,),
            )

            existing_data = cursor.fetchall()

        if not existing_data:
            return 0

        templates = self.augmentation_templates[agent_name]
        augmented_data = []
        target_count = int(len(existing_data) * augmentation_factor)

        for i in range(target_count):
            # Select random existing data point
            original = existing_data[i % len(existing_data)]

            # Select random template
            template = templates[i % len(templates)]

            # Generate augmented data
            augmented_point = self._apply_augmentation_template(
                template, original, agent_name
            )

            if augmented_point:
                augmented_data.append(augmented_point)

        # Add augmented data to dataset
        if augmented_data:
            results = self.add_data_to_dataset(dataset_id, augmented_data)
            return results["added"]

        return 0

    def _apply_augmentation_template(
        self, template: dict, original_data: tuple, agent_name: str
    ) -> dict | None:
        """Apply augmentation template to generate new training data."""
        input_text, expected_output, context_data = original_data

        try:
            template_type = template["type"]

            if template_type == "code_variation" and agent_name.endswith("-pro"):
                # Generate code variation
                alternatives = template.get("alternatives", [])
                if alternatives:
                    alternative = alternatives[hash(input_text) % len(alternatives)]
                    new_input = template["template"].format(
                        alternative=alternative, original_code=input_text
                    )

                    return {
                        "agent_name": agent_name,
                        "data_source": DataSource.SYNTHETIC_GENERATION.value,
                        "input_text": new_input,
                        "expected_output": "",  # To be filled by expert review
                        "context_data": {
                            "augmentation_type": template_type,
                            "original_input": input_text,
                            "template_used": template.get("template", ""),
                        },
                        "tags": ["augmented", "synthetic", template_type],
                    }

            elif template_type == "error_injection":
                # Generate error scenarios
                error_types = template.get("error_types", [])
                if error_types:
                    error_type = error_types[hash(input_text) % len(error_types)]
                    new_input = template["template"].format(
                        error_type=error_type, buggy_code=input_text
                    )

                    return {
                        "agent_name": agent_name,
                        "data_source": DataSource.SYNTHETIC_GENERATION.value,
                        "input_text": new_input,
                        "expected_output": f"Debug and fix the {error_type} in the provided code",
                        "context_data": {
                            "augmentation_type": template_type,
                            "error_type": error_type,
                            "original_input": input_text,
                        },
                        "tags": ["augmented", "debugging", error_type],
                    }

        except Exception as e:
            logging.warning(f"Failed to apply augmentation template: {e}")

        return None

    def get_dataset_quality_report(self, dataset_id: str) -> dict[str, Any]:
        """Generate comprehensive quality report for a dataset."""
        with sqlite3.connect(self.db_path) as conn:
            # Basic statistics
            cursor = conn.execute(
                """
                SELECT 
                    COUNT(*) as total_points,
                    COUNT(CASE WHEN validation_status = 'valid' THEN 1 END) as valid_points,
                    AVG(quality_score) as avg_quality,
                    MIN(quality_score) as min_quality,
                    MAX(quality_score) as max_quality,
                    COUNT(DISTINCT data_source) as unique_sources
                FROM training_data_v2 
                WHERE dataset_id = ?
            """,
                (dataset_id,),
            )

            stats = cursor.fetchone()

            # Quality distribution
            cursor = conn.execute(
                """
                SELECT quality_score FROM training_data_v2 
                WHERE dataset_id = ? AND quality_score > 0
            """,
                (dataset_id,),
            )

            quality_scores = [row[0] for row in cursor.fetchall()]

            # Data sources distribution
            cursor = conn.execute(
                """
                SELECT data_source, COUNT(*) as count
                FROM training_data_v2 
                WHERE dataset_id = ?
                GROUP BY data_source
            """,
                (dataset_id,),
            )

            source_distribution = dict(cursor.fetchall())

            # Validation errors
            cursor = conn.execute(
                """
                SELECT validation_errors FROM training_data_v2 
                WHERE dataset_id = ? AND validation_status = 'invalid'
            """,
                (dataset_id,),
            )

            validation_errors = []
            for row in cursor.fetchall():
                if row[0]:
                    errors = json.loads(row[0])
                    validation_errors.extend(errors)

            # Error distribution
            error_distribution = Counter(
                [error.get("rule_name", "Unknown") for error in validation_errors]
            )

        report = {
            "dataset_id": dataset_id,
            "basic_statistics": {
                "total_points": stats[0] or 0,
                "valid_points": stats[1] or 0,
                "validation_rate": (stats[1] or 0) / max(stats[0] or 1, 1),
                "average_quality": stats[2] or 0.0,
                "quality_range": [stats[3] or 0.0, stats[4] or 0.0],
                "unique_sources": stats[5] or 0,
            },
            "quality_distribution": {
                "excellent": len([s for s in quality_scores if s >= 0.9]),
                "good": len([s for s in quality_scores if 0.7 <= s < 0.9]),
                "acceptable": len([s for s in quality_scores if 0.5 <= s < 0.7]),
                "poor": len([s for s in quality_scores if 0.3 <= s < 0.5]),
                "unusable": len([s for s in quality_scores if s < 0.3]),
            },
            "source_distribution": source_distribution,
            "validation_issues": {
                "total_errors": len(validation_errors),
                "error_distribution": dict(error_distribution.most_common(5)),
            },
            "recommendations": self._generate_quality_recommendations(
                stats, quality_scores, validation_errors
            ),
            "generated_at": datetime.now().isoformat(),
        }

        return report

    def _generate_quality_recommendations(
        self, stats: tuple, quality_scores: list[float], validation_errors: list[dict]
    ) -> list[str]:
        """Generate recommendations for improving data quality."""
        recommendations = []

        total_points = stats[0] or 0
        valid_points = stats[1] or 0
        avg_quality = stats[2] or 0.0

        # Validation rate recommendations
        if total_points > 0:
            validation_rate = valid_points / total_points
            if validation_rate < 0.7:
                recommendations.append(
                    "Low validation rate detected. Review validation rules and improve data collection process."
                )

        # Quality score recommendations
        if avg_quality < 0.6:
            recommendations.append(
                "Average quality score is below threshold. Focus on collecting higher quality data."
            )

        if quality_scores:
            poor_quality_ratio = len([s for s in quality_scores if s < 0.5]) / len(
                quality_scores
            )
            if poor_quality_ratio > 0.3:
                recommendations.append(
                    "High ratio of poor quality data. Consider filtering criteria or data augmentation."
                )

        # Validation error recommendations
        error_types = Counter(
            [error.get("rule_name", "Unknown") for error in validation_errors]
        )
        for error_type, count in error_types.most_common(3):
            if count > total_points * 0.1:  # More than 10% of data has this error
                recommendations.append(
                    f"Common validation issue: {error_type}. Review data collection for this pattern."
                )

        # Data volume recommendations
        if total_points < 50:
            recommendations.append(
                "Dataset is small. Consider collecting more training data for better model performance."
            )
        elif total_points > 10000:
            recommendations.append(
                "Large dataset detected. Consider data sampling strategies for efficient training."
            )

        return recommendations

    def export_dataset(
        self, dataset_id: str, format: str = "json", privacy_filter: bool = True
    ) -> str:
        """Export dataset in specified format."""
        export_path = f"dataset_{dataset_id}.{format}"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT * FROM training_data_v2 
                WHERE dataset_id = ? AND validation_status = 'valid'
                ORDER BY quality_score DESC
            """,
                (dataset_id,),
            )

            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()

        # Convert to dictionaries
        data_points = []
        for row in rows:
            point = dict(zip(columns, row, strict=False))

            # Apply privacy filter if requested
            if (
                privacy_filter
                and point.get("privacy_level", 2) >= PrivacyLevel.CONFIDENTIAL.value
            ):
                point["input_text"] = "[REDACTED]"
                point["actual_output"] = "[REDACTED]"

            # Parse JSON fields
            for field in ["context_data", "validation_errors", "tags", "metadata"]:
                if point.get(field):
                    try:
                        point[field] = json.loads(point[field])
                    except json.JSONDecodeError:
                        pass

            data_points.append(point)

        # Export based on format
        if format == "json":
            with open(export_path, "w") as f:
                json.dump(
                    {
                        "dataset_id": dataset_id,
                        "export_date": datetime.now().isoformat(),
                        "total_points": len(data_points),
                        "data": data_points,
                    },
                    f,
                    indent=2,
                    default=str,
                )

        elif format == "csv":
            import csv

            if data_points:
                with open(export_path, "w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=data_points[0].keys())
                    writer.writeheader()
                    writer.writerows(data_points)

        return export_path


def main():
    """CLI interface for training data manager."""
    import argparse

    parser = argparse.ArgumentParser(description="Training Data Manager")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Create dataset command
    create_parser = subparsers.add_parser(
        "create-dataset", help="Create new training dataset"
    )
    create_parser.add_argument("--name", required=True, help="Dataset name")
    create_parser.add_argument("--agent", required=True, help="Agent name")
    create_parser.add_argument("--description", help="Dataset description")
    create_parser.add_argument("--tags", help="Comma-separated tags")

    # Quality report command
    quality_parser = subparsers.add_parser(
        "quality-report", help="Generate quality report"
    )
    quality_parser.add_argument("dataset_id", help="Dataset ID")

    # Augment command
    augment_parser = subparsers.add_parser("augment", help="Augment dataset")
    augment_parser.add_argument("dataset_id", help="Dataset ID")
    augment_parser.add_argument("--agent", required=True, help="Agent name")
    augment_parser.add_argument(
        "--factor", type=float, default=2.0, help="Augmentation factor"
    )

    # Export command
    export_parser = subparsers.add_parser("export", help="Export dataset")
    export_parser.add_argument("dataset_id", help="Dataset ID")
    export_parser.add_argument(
        "--format", choices=["json", "csv"], default="json", help="Export format"
    )
    export_parser.add_argument(
        "--privacy-filter", action="store_true", help="Apply privacy filtering"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Setup logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # Initialize training data curator
    curator = TrainingDataCurator()

    try:
        if args.command == "create-dataset":
            tags = args.tags.split(",") if args.tags else []
            dataset_id = curator.create_training_dataset(
                name=args.name,
                agent_name=args.agent,
                data_sources=[DataSource.USER_INTERACTION],
                description=args.description or "",
                tags=tags,
            )
            print(f"✅ Created dataset: {dataset_id}")

        elif args.command == "quality-report":
            report = curator.get_dataset_quality_report(args.dataset_id)
            print(json.dumps(report, indent=2, default=str))

        elif args.command == "augment":
            count = curator.augment_training_data(
                args.dataset_id, args.agent, args.factor
            )
            print(f"✅ Generated {count} augmented training examples")

        elif args.command == "export":
            export_path = curator.export_dataset(
                args.dataset_id, args.format, args.privacy_filter
            )
            print(f"✅ Dataset exported to: {export_path}")

    except Exception as e:
        print(f"❌ Error: {e}")
        logging.error(f"Training data manager error: {e}")


if __name__ == "__main__":
    main()
