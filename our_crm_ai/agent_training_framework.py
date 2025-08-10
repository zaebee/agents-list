#!/usr/bin/env python3
"""
Agent Training Framework - Comprehensive training system for 59+ specialized AI agents.

This module provides:
1. Training pipeline for all specialized agents
2. Performance optimization and fine-tuning
3. Continuous learning from real usage data
4. Training data collection and curation
5. Evaluation metrics and benchmarking
"""

import json
import time
import uuid
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import sqlite3
import statistics
from collections import defaultdict, deque
import threading
import pickle
import hashlib

# Import existing system components
from agent_selector import AGENT_KEYWORDS, suggest_agents
from pm_agent_gateway import PMAgentGateway, TaskComplexity
from backlog_analyzer import BacklogAnalyzer


class TrainingPhase(Enum):
    """Training phases for agents."""
    INITIAL = "initial"
    FINE_TUNING = "fine_tuning"
    SPECIALIZATION = "specialization"
    CONTINUOUS = "continuous"


class PerformanceMetric(Enum):
    """Performance metrics for agent evaluation."""
    ACCURACY = "accuracy"
    RESPONSE_TIME = "response_time"
    TASK_SUCCESS_RATE = "task_success_rate"
    USER_SATISFACTION = "user_satisfaction"
    DOMAIN_EXPERTISE = "domain_expertise"
    COLLABORATION_SCORE = "collaboration_score"


class FeedbackType(Enum):
    """Types of feedback for training."""
    USER_RATING = "user_rating"
    TASK_COMPLETION = "task_completion"
    ERROR_CORRECTION = "error_correction"
    PEER_REVIEW = "peer_review"
    AUTOMATED_METRIC = "automated_metric"


@dataclass
class TrainingSession:
    """Training session data structure."""
    session_id: str
    agent_name: str
    phase: TrainingPhase
    start_time: datetime
    end_time: Optional[datetime]
    training_data_count: int
    performance_before: Dict[str, float]
    performance_after: Dict[str, float]
    improvement_metrics: Dict[str, float]
    status: str
    notes: str


@dataclass
class AgentPerformanceData:
    """Agent performance tracking data."""
    agent_name: str
    metric_type: PerformanceMetric
    value: float
    timestamp: datetime
    task_context: str
    feedback_source: FeedbackType


@dataclass
class TrainingDatapoint:
    """Individual training data point."""
    datapoint_id: str
    agent_name: str
    input_text: str
    expected_output: str
    actual_output: Optional[str]
    performance_score: float
    context: Dict[str, Any]
    timestamp: datetime
    validated: bool


class TrainingDataCollector:
    """Collects and curates training data from real usage."""
    
    def __init__(self, db_path: str = "training_data.db"):
        """Initialize training data collector."""
        self.db_path = db_path
        self.setup_database()
        self.collection_buffer = defaultdict(list)
        self.buffer_size = 1000
        
    def setup_database(self):
        """Setup SQLite database for training data."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS training_data (
                    id TEXT PRIMARY KEY,
                    agent_name TEXT NOT NULL,
                    input_text TEXT NOT NULL,
                    expected_output TEXT,
                    actual_output TEXT,
                    performance_score REAL,
                    context TEXT,
                    timestamp TEXT,
                    validated INTEGER DEFAULT 0,
                    quality_score REAL DEFAULT 0.0
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id TEXT PRIMARY KEY,
                    agent_name TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    value REAL NOT NULL,
                    timestamp TEXT,
                    task_context TEXT,
                    feedback_source TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS feedback_data (
                    id TEXT PRIMARY KEY,
                    agent_name TEXT NOT NULL,
                    task_id TEXT,
                    feedback_type TEXT NOT NULL,
                    rating REAL,
                    comments TEXT,
                    timestamp TEXT,
                    user_id TEXT
                )
            """)
    
    def collect_task_interaction(self, agent_name: str, task_title: str, 
                               task_description: str, agent_response: str,
                               success_rating: float, user_feedback: str = ""):
        """Collect training data from task interactions."""
        datapoint = TrainingDatapoint(
            datapoint_id=str(uuid.uuid4()),
            agent_name=agent_name,
            input_text=f"Task: {task_title}\nDescription: {task_description}",
            expected_output="",  # To be filled by expert review
            actual_output=agent_response,
            performance_score=success_rating,
            context={
                "task_title": task_title,
                "user_feedback": user_feedback,
                "collection_method": "task_interaction"
            },
            timestamp=datetime.now(),
            validated=False
        )
        
        self._add_to_buffer(datapoint)
    
    def collect_pm_gateway_decisions(self, task_title: str, task_description: str,
                                   pm_recommendation: Dict, user_accepted: bool):
        """Collect training data from PM Gateway decisions."""
        datapoint = TrainingDatapoint(
            datapoint_id=str(uuid.uuid4()),
            agent_name="pm-agent-gateway",
            input_text=f"Title: {task_title}\nDescription: {task_description}",
            expected_output=json.dumps(pm_recommendation),
            actual_output=json.dumps(pm_recommendation),
            performance_score=1.0 if user_accepted else 0.3,
            context={
                "user_accepted": user_accepted,
                "recommendation_type": pm_recommendation.get('type', 'unknown'),
                "collection_method": "pm_gateway_decision"
            },
            timestamp=datetime.now(),
            validated=user_accepted  # User acceptance validates the decision
        )
        
        self._add_to_buffer(datapoint)
    
    def collect_agent_suggestions(self, task_description: str, suggestions: List[Dict],
                                user_selected: str, task_outcome: float):
        """Collect training data from agent suggestions."""
        for suggestion in suggestions:
            is_selected = suggestion['agent'] == user_selected
            datapoint = TrainingDatapoint(
                datapoint_id=str(uuid.uuid4()),
                agent_name="agent-selector",
                input_text=task_description,
                expected_output=user_selected,
                actual_output=suggestion['agent'],
                performance_score=task_outcome if is_selected else 0.2,
                context={
                    "confidence": suggestion['confidence'],
                    "matched_keywords": suggestion['matched_keywords'],
                    "was_selected": is_selected,
                    "final_task_outcome": task_outcome,
                    "collection_method": "agent_suggestion"
                },
                timestamp=datetime.now(),
                validated=is_selected and task_outcome > 0.7
            )
            
            self._add_to_buffer(datapoint)
    
    def _add_to_buffer(self, datapoint: TrainingDatapoint):
        """Add datapoint to collection buffer."""
        self.collection_buffer[datapoint.agent_name].append(datapoint)
        
        # Flush buffer if it's getting full
        if len(self.collection_buffer[datapoint.agent_name]) >= self.buffer_size:
            self._flush_buffer(datapoint.agent_name)
    
    def _flush_buffer(self, agent_name: str = None):
        """Flush collection buffer to database."""
        agents_to_flush = [agent_name] if agent_name else list(self.collection_buffer.keys())
        
        with sqlite3.connect(self.db_path) as conn:
            for agent in agents_to_flush:
                if agent in self.collection_buffer and self.collection_buffer[agent]:
                    for datapoint in self.collection_buffer[agent]:
                        conn.execute("""
                            INSERT OR REPLACE INTO training_data 
                            (id, agent_name, input_text, expected_output, actual_output,
                             performance_score, context, timestamp, validated, quality_score)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            datapoint.datapoint_id,
                            datapoint.agent_name,
                            datapoint.input_text,
                            datapoint.expected_output,
                            datapoint.actual_output,
                            datapoint.performance_score,
                            json.dumps(datapoint.context),
                            datapoint.timestamp.isoformat(),
                            int(datapoint.validated),
                            self._calculate_quality_score(datapoint)
                        ))
                    
                    self.collection_buffer[agent].clear()
    
    def _calculate_quality_score(self, datapoint: TrainingDatapoint) -> float:
        """Calculate quality score for training data."""
        score = 0.0
        
        # Base score from performance
        score += datapoint.performance_score * 0.4
        
        # Validation bonus
        if datapoint.validated:
            score += 0.3
        
        # Context richness
        context_keys = len(datapoint.context.keys())
        score += min(context_keys / 10, 0.2)
        
        # Data completeness
        if datapoint.expected_output:
            score += 0.1
        
        return min(score, 1.0)
    
    def get_training_data(self, agent_name: str, min_quality: float = 0.3,
                         limit: int = 1000) -> List[TrainingDatapoint]:
        """Retrieve training data for an agent."""
        self._flush_buffer(agent_name)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM training_data 
                WHERE agent_name = ? AND quality_score >= ?
                ORDER BY quality_score DESC, timestamp DESC
                LIMIT ?
            """, (agent_name, min_quality, limit))
            
            datapoints = []
            for row in cursor.fetchall():
                datapoints.append(TrainingDatapoint(
                    datapoint_id=row[0],
                    agent_name=row[1],
                    input_text=row[2],
                    expected_output=row[3] or "",
                    actual_output=row[4] or "",
                    performance_score=row[5] or 0.0,
                    context=json.loads(row[6]) if row[6] else {},
                    timestamp=datetime.fromisoformat(row[7]),
                    validated=bool(row[8])
                ))
            
            return datapoints


class PerformanceEvaluator:
    """Evaluates and tracks agent performance metrics."""
    
    def __init__(self, db_path: str = "training_data.db"):
        """Initialize performance evaluator."""
        self.db_path = db_path
        self.metric_history = defaultdict(lambda: defaultdict(deque))
        self.evaluation_cache = {}
        
    def record_performance(self, agent_name: str, metric: PerformanceMetric,
                         value: float, task_context: str = "",
                         feedback_source: FeedbackType = FeedbackType.AUTOMATED_METRIC):
        """Record a performance metric for an agent."""
        perf_data = AgentPerformanceData(
            agent_name=agent_name,
            metric_type=metric,
            value=value,
            timestamp=datetime.now(),
            task_context=task_context,
            feedback_source=feedback_source
        )
        
        # Store in memory for fast access
        self.metric_history[agent_name][metric.value].append(perf_data)
        
        # Keep only recent metrics in memory (last 1000)
        if len(self.metric_history[agent_name][metric.value]) > 1000:
            self.metric_history[agent_name][metric.value].popleft()
        
        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO performance_metrics 
                (id, agent_name, metric_type, value, timestamp, task_context, feedback_source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()),
                agent_name,
                metric.value,
                value,
                perf_data.timestamp.isoformat(),
                task_context,
                feedback_source.value
            ))
    
    def get_agent_performance_summary(self, agent_name: str, 
                                    days_back: int = 30) -> Dict[str, Dict[str, float]]:
        """Get comprehensive performance summary for an agent."""
        cutoff_date = datetime.now() - timedelta(days=days_back)
        summary = {}
        
        for metric_name, metric_data in self.metric_history[agent_name].items():
            recent_data = [
                data.value for data in metric_data 
                if data.timestamp >= cutoff_date
            ]
            
            if recent_data:
                summary[metric_name] = {
                    'current': recent_data[-1],
                    'average': statistics.mean(recent_data),
                    'median': statistics.median(recent_data),
                    'std_dev': statistics.stdev(recent_data) if len(recent_data) > 1 else 0.0,
                    'trend': self._calculate_trend(recent_data),
                    'sample_count': len(recent_data),
                    'min': min(recent_data),
                    'max': max(recent_data)
                }
        
        return summary
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend direction (-1 to 1, where 1 is strongly improving)."""
        if len(values) < 2:
            return 0.0
        
        # Simple linear trend calculation
        n = len(values)
        x = list(range(n))
        
        # Calculate correlation coefficient
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(values)
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        x_dev = sum((x[i] - x_mean) ** 2 for i in range(n))
        y_dev = sum((values[i] - y_mean) ** 2 for i in range(n))
        
        if x_dev == 0 or y_dev == 0:
            return 0.0
        
        correlation = numerator / (x_dev * y_dev) ** 0.5
        return correlation
    
    def compare_agents(self, metric: PerformanceMetric, 
                      agent_names: List[str] = None) -> Dict[str, float]:
        """Compare agents on a specific metric."""
        if agent_names is None:
            agent_names = list(self.metric_history.keys())
        
        comparison = {}
        for agent_name in agent_names:
            if agent_name in self.metric_history and metric.value in self.metric_history[agent_name]:
                recent_values = [
                    data.value for data in list(self.metric_history[agent_name][metric.value])[-10:]
                ]
                if recent_values:
                    comparison[agent_name] = statistics.mean(recent_values)
        
        return dict(sorted(comparison.items(), key=lambda x: x[1], reverse=True))
    
    def identify_training_needs(self, threshold_percentile: float = 0.25) -> Dict[str, List[str]]:
        """Identify agents that need additional training based on performance."""
        training_needs = defaultdict(list)
        
        for metric in PerformanceMetric:
            agent_scores = self.compare_agents(metric)
            if not agent_scores:
                continue
            
            scores = list(agent_scores.values())
            threshold = sorted(scores)[int(len(scores) * threshold_percentile)]
            
            for agent_name, score in agent_scores.items():
                if score <= threshold:
                    training_needs[agent_name].append(metric.value)
        
        return dict(training_needs)


class ContinuousLearningEngine:
    """Manages continuous learning and feedback integration."""
    
    def __init__(self, data_collector: TrainingDataCollector,
                 performance_evaluator: PerformanceEvaluator):
        """Initialize continuous learning engine."""
        self.data_collector = data_collector
        self.performance_evaluator = performance_evaluator
        self.feedback_processors = {}
        self.learning_schedule = {}
        self.active_learning_sessions = {}
        
    def register_feedback_processor(self, feedback_type: FeedbackType, processor):
        """Register a feedback processor for specific feedback types."""
        self.feedback_processors[feedback_type] = processor
    
    def process_user_feedback(self, agent_name: str, task_id: str,
                            feedback_type: FeedbackType, rating: float,
                            comments: str = "", user_id: str = ""):
        """Process user feedback for continuous learning."""
        
        # Store feedback
        with sqlite3.connect(self.data_collector.db_path) as conn:
            conn.execute("""
                INSERT INTO feedback_data 
                (id, agent_name, task_id, feedback_type, rating, comments, timestamp, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()),
                agent_name,
                task_id,
                feedback_type.value,
                rating,
                comments,
                datetime.now().isoformat(),
                user_id
            ))
        
        # Record performance metric
        self.performance_evaluator.record_performance(
            agent_name=agent_name,
            metric=PerformanceMetric.USER_SATISFACTION,
            value=rating,
            task_context=f"Task {task_id}",
            feedback_source=feedback_type
        )
        
        # Trigger retraining if performance drops
        self._check_retraining_triggers(agent_name)
    
    def _check_retraining_triggers(self, agent_name: str):
        """Check if agent needs retraining based on recent performance."""
        summary = self.performance_evaluator.get_agent_performance_summary(agent_name, days_back=7)
        
        retraining_needed = False
        
        # Check various trigger conditions
        for metric_name, stats in summary.items():
            # Significant performance drop
            if stats['trend'] < -0.5 and stats['sample_count'] >= 5:
                retraining_needed = True
                logging.info(f"Agent {agent_name} showing declining {metric_name}: trend {stats['trend']}")
            
            # Below threshold performance
            if metric_name == 'user_satisfaction' and stats['average'] < 0.6:
                retraining_needed = True
                logging.info(f"Agent {agent_name} user satisfaction below threshold: {stats['average']}")
        
        if retraining_needed:
            self._schedule_retraining(agent_name)
    
    def _schedule_retraining(self, agent_name: str, priority: str = "normal"):
        """Schedule agent for retraining."""
        if agent_name not in self.learning_schedule:
            self.learning_schedule[agent_name] = {
                'scheduled_time': datetime.now(),
                'priority': priority,
                'reason': 'performance_decline',
                'status': 'scheduled'
            }
            logging.info(f"Scheduled retraining for agent {agent_name}")
    
    def get_learning_insights(self, agent_name: str) -> Dict[str, Any]:
        """Generate learning insights for an agent."""
        
        # Get recent training data
        recent_data = self.data_collector.get_training_data(agent_name, limit=100)
        
        # Get performance trends
        performance_summary = self.performance_evaluator.get_agent_performance_summary(agent_name)
        
        # Analyze common failure patterns
        failure_patterns = self._analyze_failure_patterns(recent_data)
        
        # Get improvement recommendations
        recommendations = self._generate_improvement_recommendations(
            agent_name, performance_summary, failure_patterns
        )
        
        return {
            'agent_name': agent_name,
            'training_data_quality': self._assess_training_data_quality(recent_data),
            'performance_trends': performance_summary,
            'failure_patterns': failure_patterns,
            'improvement_recommendations': recommendations,
            'retraining_priority': self._calculate_retraining_priority(agent_name),
            'generated_at': datetime.now().isoformat()
        }
    
    def _analyze_failure_patterns(self, training_data: List[TrainingDatapoint]) -> Dict[str, Any]:
        """Analyze common patterns in failed tasks."""
        low_performance_data = [
            dp for dp in training_data 
            if dp.performance_score < 0.5
        ]
        
        if not low_performance_data:
            return {'patterns': [], 'count': 0}
        
        # Analyze input patterns
        common_words = defaultdict(int)
        context_patterns = defaultdict(int)
        
        for dp in low_performance_data:
            words = dp.input_text.lower().split()
            for word in words:
                if len(word) > 3:  # Skip short words
                    common_words[word] += 1
            
            for key, value in dp.context.items():
                if isinstance(value, str):
                    context_patterns[f"{key}:{value}"] += 1
        
        # Get most common patterns
        top_word_patterns = sorted(common_words.items(), key=lambda x: x[1], reverse=True)[:5]
        top_context_patterns = sorted(context_patterns.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            'patterns': {
                'common_failure_words': top_word_patterns,
                'context_patterns': top_context_patterns
            },
            'count': len(low_performance_data),
            'failure_rate': len(low_performance_data) / len(training_data) if training_data else 0
        }
    
    def _generate_improvement_recommendations(self, agent_name: str,
                                           performance_summary: Dict,
                                           failure_patterns: Dict) -> List[str]:
        """Generate specific improvement recommendations."""
        recommendations = []
        
        # Performance-based recommendations
        for metric_name, stats in performance_summary.items():
            if stats['trend'] < -0.3:
                recommendations.append(f"Focus on improving {metric_name} - showing decline trend")
            
            if metric_name == 'response_time' and stats['average'] > 5.0:
                recommendations.append("Optimize for faster response times")
            
            if metric_name == 'accuracy' and stats['average'] < 0.7:
                recommendations.append("Improve accuracy through additional domain-specific training")
        
        # Failure pattern recommendations
        if failure_patterns['count'] > 0:
            failure_rate = failure_patterns['failure_rate']
            if failure_rate > 0.3:
                recommendations.append("High failure rate detected - review task assignment criteria")
            
            if failure_patterns['patterns'].get('common_failure_words'):
                top_words = failure_patterns['patterns']['common_failure_words'][:2]
                words_str = ', '.join([word for word, count in top_words])
                recommendations.append(f"Focus training on tasks involving: {words_str}")
        
        # Agent-specific recommendations based on keywords
        if agent_name in AGENT_KEYWORDS:
            agent_keywords = AGENT_KEYWORDS[agent_name]
            recommendations.append(f"Strengthen expertise in: {', '.join(agent_keywords[:3])}")
        
        return recommendations
    
    def _assess_training_data_quality(self, training_data: List[TrainingDatapoint]) -> Dict[str, float]:
        """Assess quality of training data."""
        if not training_data:
            return {'overall': 0.0, 'validated_ratio': 0.0, 'completeness': 0.0}
        
        validated_count = sum(1 for dp in training_data if dp.validated)
        complete_count = sum(1 for dp in training_data if dp.expected_output)
        avg_quality = statistics.mean([self.data_collector._calculate_quality_score(dp) for dp in training_data])
        
        return {
            'overall': avg_quality,
            'validated_ratio': validated_count / len(training_data),
            'completeness': complete_count / len(training_data),
            'sample_count': len(training_data)
        }
    
    def _calculate_retraining_priority(self, agent_name: str) -> str:
        """Calculate retraining priority for an agent."""
        summary = self.performance_evaluator.get_agent_performance_summary(agent_name)
        
        if not summary:
            return "low"
        
        priority_score = 0
        
        # Check critical metrics
        for metric_name, stats in summary.items():
            if metric_name in ['accuracy', 'task_success_rate', 'user_satisfaction']:
                if stats['average'] < 0.5:
                    priority_score += 3
                elif stats['average'] < 0.7:
                    priority_score += 2
                elif stats['trend'] < -0.4:
                    priority_score += 2
        
        if priority_score >= 6:
            return "critical"
        elif priority_score >= 3:
            return "high"
        elif priority_score >= 1:
            return "medium"
        else:
            return "low"


class AgentTrainingPipeline:
    """Main training pipeline orchestrator."""
    
    def __init__(self, config_path: str = "training_config.json"):
        """Initialize training pipeline."""
        self.config = self._load_config(config_path)
        self.data_collector = TrainingDataCollector()
        self.performance_evaluator = PerformanceEvaluator()
        self.continuous_learning = ContinuousLearningEngine(
            self.data_collector, self.performance_evaluator
        )
        self.training_sessions = {}
        self.agent_metadata = self._load_agent_metadata()
        
    def _load_config(self, config_path: str) -> Dict:
        """Load training configuration."""
        default_config = {
            "training_batch_size": 100,
            "evaluation_frequency": 24,  # hours
            "min_training_data_quality": 0.3,
            "performance_threshold": 0.7,
            "retraining_cooldown": 48,  # hours
            "specialization_threshold": 0.8,
            "collaboration_weight": 0.2
        }
        
        try:
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        except FileNotFoundError:
            logging.info(f"Config file {config_path} not found, using defaults")
        
        return default_config
    
    def _load_agent_metadata(self) -> Dict[str, Dict]:
        """Load metadata for all agents."""
        metadata = {}
        
        for agent_name in AGENT_KEYWORDS.keys():
            metadata[agent_name] = {
                'keywords': AGENT_KEYWORDS[agent_name],
                'specialization_level': 0.5,  # Initial level
                'training_history': [],
                'last_trained': None,
                'performance_baseline': {}
            }
        
        # Add special agents
        special_agents = ['pm-agent-gateway', 'agent-selector', 'backlog-analyzer']
        for agent in special_agents:
            metadata[agent] = {
                'keywords': [],
                'specialization_level': 0.7,
                'training_history': [],
                'last_trained': None,
                'performance_baseline': {}
            }
        
        return metadata
    
    def start_training_session(self, agent_name: str, phase: TrainingPhase,
                             training_data_limit: int = None) -> str:
        """Start a new training session for an agent."""
        session_id = str(uuid.uuid4())
        
        # Get training data
        if training_data_limit is None:
            training_data_limit = self.config['training_batch_size']
        
        training_data = self.data_collector.get_training_data(
            agent_name, 
            min_quality=self.config['min_training_data_quality'],
            limit=training_data_limit
        )
        
        if not training_data:
            logging.warning(f"No quality training data available for {agent_name}")
            return None
        
        # Record baseline performance
        performance_before = self.performance_evaluator.get_agent_performance_summary(agent_name)
        
        # Create training session
        session = TrainingSession(
            session_id=session_id,
            agent_name=agent_name,
            phase=phase,
            start_time=datetime.now(),
            end_time=None,
            training_data_count=len(training_data),
            performance_before=performance_before,
            performance_after={},
            improvement_metrics={},
            status="running",
            notes=""
        )
        
        self.training_sessions[session_id] = session
        
        # Log training start
        logging.info(f"Started {phase.value} training session {session_id} for {agent_name} "
                   f"with {len(training_data)} datapoints")
        
        return session_id
    
    def complete_training_session(self, session_id: str, 
                                performance_metrics: Dict[str, float] = None,
                                notes: str = "") -> bool:
        """Complete a training session and record results."""
        if session_id not in self.training_sessions:
            logging.error(f"Training session {session_id} not found")
            return False
        
        session = self.training_sessions[session_id]
        session.end_time = datetime.now()
        session.status = "completed"
        session.notes = notes
        
        # Record performance after training
        if performance_metrics:
            for metric_name, value in performance_metrics.items():
                if metric_name in [m.value for m in PerformanceMetric]:
                    self.performance_evaluator.record_performance(
                        agent_name=session.agent_name,
                        metric=PerformanceMetric(metric_name),
                        value=value,
                        task_context=f"Training session {session_id}",
                        feedback_source=FeedbackType.AUTOMATED_METRIC
                    )
        
        session.performance_after = self.performance_evaluator.get_agent_performance_summary(
            session.agent_name, days_back=1
        )
        
        # Calculate improvement metrics
        session.improvement_metrics = self._calculate_improvement_metrics(
            session.performance_before, session.performance_after
        )
        
        # Update agent metadata
        self.agent_metadata[session.agent_name]['last_trained'] = datetime.now()
        self.agent_metadata[session.agent_name]['training_history'].append({
            'session_id': session_id,
            'phase': session.phase.value,
            'improvement': session.improvement_metrics,
            'timestamp': session.end_time.isoformat()
        })
        
        logging.info(f"Completed training session {session_id} for {session.agent_name}")
        return True
    
    def _calculate_improvement_metrics(self, before: Dict, after: Dict) -> Dict[str, float]:
        """Calculate improvement metrics between before and after performance."""
        improvements = {}
        
        for metric_name in before.keys():
            if metric_name in after:
                before_avg = before[metric_name].get('average', 0)
                after_avg = after[metric_name].get('average', 0)
                
                if before_avg > 0:
                    improvement = (after_avg - before_avg) / before_avg
                    improvements[metric_name] = improvement
        
        return improvements
    
    def run_comprehensive_training(self, agent_name: str) -> Dict[str, Any]:
        """Run comprehensive training pipeline for an agent."""
        results = {
            'agent_name': agent_name,
            'training_phases': [],
            'overall_improvement': {},
            'recommendations': [],
            'started_at': datetime.now().isoformat()
        }
        
        # Phase 1: Initial assessment and data collection
        logging.info(f"Starting comprehensive training for {agent_name}")
        
        # Collect recent performance data
        baseline_performance = self.performance_evaluator.get_agent_performance_summary(agent_name)
        results['baseline_performance'] = baseline_performance
        
        # Get learning insights
        insights = self.continuous_learning.get_learning_insights(agent_name)
        results['learning_insights'] = insights
        
        # Determine training phases needed
        training_phases = self._determine_training_phases(agent_name, insights)
        
        # Execute training phases
        for phase in training_phases:
            session_id = self.start_training_session(agent_name, phase)
            if session_id:
                # Simulate training process (in real implementation, this would call actual ML training)
                self._simulate_training_process(session_id, phase)
                
                # Complete session
                success = self.complete_training_session(session_id, notes=f"Automated {phase.value} training")
                
                if success:
                    results['training_phases'].append({
                        'phase': phase.value,
                        'session_id': session_id,
                        'success': success
                    })
        
        # Final assessment
        final_performance = self.performance_evaluator.get_agent_performance_summary(agent_name)
        results['final_performance'] = final_performance
        results['overall_improvement'] = self._calculate_improvement_metrics(
            baseline_performance, final_performance
        )
        
        results['completed_at'] = datetime.now().isoformat()
        logging.info(f"Completed comprehensive training for {agent_name}")
        
        return results
    
    def _determine_training_phases(self, agent_name: str, insights: Dict) -> List[TrainingPhase]:
        """Determine which training phases are needed for an agent."""
        phases = []
        
        # Check if agent has been trained before
        last_trained = self.agent_metadata[agent_name].get('last_trained')
        
        if last_trained is None:
            phases.append(TrainingPhase.INITIAL)
        
        # Check performance trends
        retraining_priority = insights.get('retraining_priority', 'low')
        
        if retraining_priority in ['high', 'critical']:
            phases.append(TrainingPhase.FINE_TUNING)
        
        # Check specialization level
        specialization_level = self.agent_metadata[agent_name].get('specialization_level', 0.5)
        
        if specialization_level < self.config['specialization_threshold']:
            phases.append(TrainingPhase.SPECIALIZATION)
        
        # Always include continuous learning phase
        phases.append(TrainingPhase.CONTINUOUS)
        
        return list(set(phases))  # Remove duplicates
    
    def _simulate_training_process(self, session_id: str, phase: TrainingPhase):
        """Simulate training process (placeholder for actual ML training)."""
        session = self.training_sessions[session_id]
        
        # Simulate training time based on phase and data size
        base_time = {
            TrainingPhase.INITIAL: 0.5,
            TrainingPhase.FINE_TUNING: 0.3,
            TrainingPhase.SPECIALIZATION: 0.4,
            TrainingPhase.CONTINUOUS: 0.1
        }
        
        training_time = base_time[phase] * (session.training_data_count / 100)
        time.sleep(min(training_time, 2.0))  # Cap at 2 seconds for demo
        
        # Simulate performance improvements
        improvement_factor = {
            TrainingPhase.INITIAL: 0.2,
            TrainingPhase.FINE_TUNING: 0.15,
            TrainingPhase.SPECIALIZATION: 0.1,
            TrainingPhase.CONTINUOUS: 0.05
        }[phase]
        
        # Record simulated performance improvements
        for metric in PerformanceMetric:
            current_perf = 0.6 + (hash(session.agent_name + metric.value) % 20) / 100
            improved_perf = min(current_perf + improvement_factor, 1.0)
            
            self.performance_evaluator.record_performance(
                agent_name=session.agent_name,
                metric=metric,
                value=improved_perf,
                task_context=f"Training session {session_id}",
                feedback_source=FeedbackType.AUTOMATED_METRIC
            )
    
    def train_all_agents(self, batch_size: int = 5) -> Dict[str, Any]:
        """Train all agents in the system."""
        all_agents = list(AGENT_KEYWORDS.keys()) + ['pm-agent-gateway', 'agent-selector']
        
        results = {
            'total_agents': len(all_agents),
            'trained_agents': [],
            'failed_agents': [],
            'training_summary': {},
            'started_at': datetime.now().isoformat()
        }
        
        # Process agents in batches
        for i in range(0, len(all_agents), batch_size):
            batch = all_agents[i:i + batch_size]
            
            logging.info(f"Training batch {i//batch_size + 1}: {', '.join(batch)}")
            
            for agent_name in batch:
                try:
                    agent_results = self.run_comprehensive_training(agent_name)
                    results['trained_agents'].append(agent_name)
                    results['training_summary'][agent_name] = agent_results
                    
                except Exception as e:
                    logging.error(f"Failed to train {agent_name}: {e}")
                    results['failed_agents'].append(agent_name)
        
        results['completed_at'] = datetime.now().isoformat()
        
        # Generate system-wide insights
        results['system_insights'] = self._generate_system_insights()
        
        return results
    
    def _generate_system_insights(self) -> Dict[str, Any]:
        """Generate insights across the entire agent system."""
        insights = {
            'top_performers': {},
            'training_needs': {},
            'collaboration_opportunities': {},
            'system_health': {}
        }
        
        # Identify top performers for each metric
        for metric in PerformanceMetric:
            top_agents = self.performance_evaluator.compare_agents(metric)
            insights['top_performers'][metric.value] = dict(list(top_agents.items())[:5])
        
        # Identify training needs
        insights['training_needs'] = self.performance_evaluator.identify_training_needs()
        
        # Calculate system health score
        all_agents = list(AGENT_KEYWORDS.keys())
        health_scores = []
        
        for agent_name in all_agents:
            agent_summary = self.performance_evaluator.get_agent_performance_summary(agent_name)
            if agent_summary:
                avg_scores = [stats['average'] for stats in agent_summary.values()]
                if avg_scores:
                    health_scores.append(statistics.mean(avg_scores))
        
        insights['system_health'] = {
            'overall_score': statistics.mean(health_scores) if health_scores else 0.5,
            'healthy_agents': len([s for s in health_scores if s > 0.7]),
            'total_evaluated': len(health_scores)
        }
        
        return insights
    
    def get_training_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive data for training dashboard."""
        
        # Recent training sessions
        recent_sessions = [
            session for session in self.training_sessions.values()
            if session.start_time >= datetime.now() - timedelta(days=7)
        ]
        
        # System performance trends
        all_agents = list(AGENT_KEYWORDS.keys())[:10]  # Sample for demo
        performance_trends = {}
        
        for agent_name in all_agents:
            performance_trends[agent_name] = self.performance_evaluator.get_agent_performance_summary(
                agent_name, days_back=30
            )
        
        # Training recommendations
        training_needs = self.performance_evaluator.identify_training_needs()
        
        return {
            'summary': {
                'total_agents': len(all_agents),
                'active_training_sessions': len([s for s in recent_sessions if s.status == 'running']),
                'completed_sessions_7d': len([s for s in recent_sessions if s.status == 'completed']),
                'average_improvement': self._calculate_average_improvement(recent_sessions)
            },
            'recent_training_sessions': [asdict(session) for session in recent_sessions[-10:]],
            'performance_trends': performance_trends,
            'training_recommendations': training_needs,
            'system_insights': self._generate_system_insights(),
            'generated_at': datetime.now().isoformat()
        }
    
    def _calculate_average_improvement(self, sessions: List[TrainingSession]) -> float:
        """Calculate average improvement across training sessions."""
        improvements = []
        
        for session in sessions:
            if session.improvement_metrics and session.status == 'completed':
                session_improvements = list(session.improvement_metrics.values())
                if session_improvements:
                    improvements.extend(session_improvements)
        
        return statistics.mean(improvements) if improvements else 0.0


def main():
    """CLI interface for agent training framework."""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Agent Training Framework")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Train command
    train_parser = subparsers.add_parser('train', help='Train specific agent or all agents')
    train_parser.add_argument('--agent', help='Agent name to train (or "all" for all agents)')
    train_parser.add_argument('--phase', choices=[p.value for p in TrainingPhase], help='Training phase')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show training status and performance')
    status_parser.add_argument('--agent', help='Specific agent to show status for')
    
    # Dashboard command
    dashboard_parser = subparsers.add_parser('dashboard', help='Show training dashboard data')
    
    # Collect command
    collect_parser = subparsers.add_parser('collect', help='Collect training data from task')
    collect_parser.add_argument('--agent', required=True, help='Agent name')
    collect_parser.add_argument('--task-title', required=True, help='Task title')
    collect_parser.add_argument('--task-description', required=True, help='Task description') 
    collect_parser.add_argument('--response', required=True, help='Agent response')
    collect_parser.add_argument('--rating', type=float, required=True, help='Success rating (0-1)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Initialize training pipeline
    pipeline = AgentTrainingPipeline()
    
    try:
        if args.command == 'train':
            if args.agent == 'all':
                print("🎯 Training all agents in the system...")
                results = pipeline.train_all_agents()
                
                print(f"\n📊 Training Results:")
                print(f"Total agents: {results['total_agents']}")
                print(f"Successfully trained: {len(results['trained_agents'])}")
                print(f"Failed: {len(results['failed_agents'])}")
                
                if results['failed_agents']:
                    print(f"Failed agents: {', '.join(results['failed_agents'])}")
                
                print(f"System health score: {results['system_insights']['system_health']['overall_score']:.2f}")
                
            elif args.agent:
                print(f"🎯 Training agent: {args.agent}")
                results = pipeline.run_comprehensive_training(args.agent)
                
                print(f"\n📊 Training Results for {args.agent}:")
                print(f"Training phases completed: {len(results['training_phases'])}")
                
                if results['overall_improvement']:
                    print("Performance improvements:")
                    for metric, improvement in results['overall_improvement'].items():
                        print(f"  {metric}: {improvement:+.2%}")
                
            else:
                print("Error: Please specify --agent <agent_name> or --agent all")
        
        elif args.command == 'status':
            if args.agent:
                insights = pipeline.continuous_learning.get_learning_insights(args.agent)
                performance = pipeline.performance_evaluator.get_agent_performance_summary(args.agent)
                
                print(f"\n📊 Status for {args.agent}:")
                print(f"Retraining priority: {insights['retraining_priority']}")
                print(f"Training data quality: {insights['training_data_quality']['overall']:.2f}")
                
                if performance:
                    print("\nPerformance metrics:")
                    for metric, stats in performance.items():
                        print(f"  {metric}: {stats['average']:.2f} (trend: {stats['trend']:+.2f})")
                
                if insights['improvement_recommendations']:
                    print("\nRecommendations:")
                    for rec in insights['improvement_recommendations']:
                        print(f"  • {rec}")
            else:
                # Show system-wide status
                dashboard_data = pipeline.get_training_dashboard_data()
                summary = dashboard_data['summary']
                
                print(f"\n📊 System Training Status:")
                print(f"Total agents: {summary['total_agents']}")
                print(f"Active training sessions: {summary['active_training_sessions']}")
                print(f"Completed sessions (7d): {summary['completed_sessions_7d']}")
                print(f"Average improvement: {summary['average_improvement']:+.2%}")
                
                system_health = dashboard_data['system_insights']['system_health']
                print(f"\nSystem health: {system_health['overall_score']:.2f}")
                print(f"Healthy agents: {system_health['healthy_agents']}/{system_health['total_evaluated']}")
        
        elif args.command == 'dashboard':
            dashboard_data = pipeline.get_training_dashboard_data()
            print(json.dumps(dashboard_data, indent=2, default=str))
        
        elif args.command == 'collect':
            pipeline.data_collector.collect_task_interaction(
                args.agent, args.task_title, args.task_description,
                args.response, args.rating
            )
            print(f"✅ Training data collected for {args.agent}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        logging.error(f"Training framework error: {e}")


if __name__ == "__main__":
    main()