"""
Track content volume over time to detect true spikes.
True spike = platform volume (items/hour) exceeds baseline by configured multiplier.
"""

import sqlite3
from datetime import datetime, timedelta
from config import (
    SPIKE_BASELINE_HOURS,
    SPIKE_MULTIPLIER,
    SPIKE_MIN_BASELINE_ITEMS,
)


class SpikeTracker:
    """Detect volume spikes by comparing recent rate to historical baseline."""

    def __init__(self, db_name="fake_news.db"):
        self.db_name = db_name
        self._init_spikes_table()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_name, timeout=10)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def _init_spikes_table(self):
        """Create spikes table if it doesn't exist."""
        conn = self._get_conn()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS spikes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT,
                    title TEXT,
                    spike_rate REAL,
                    baseline_rate REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def get_baseline_volume(self, platform, hours=None):
        """
        Get average content volume (items/hour) for platform over last N hours.
        Returns 0 if insufficient data.
        """
        hours = hours or SPIKE_BASELINE_HOURS
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
            cursor.execute("""
                SELECT COUNT(*) FROM content_log
                WHERE platform = ? AND timestamp > ?
            """, (platform, cutoff))
            count = cursor.fetchone()[0]
            if count < SPIKE_MIN_BASELINE_ITEMS:
                return 0.0
            return count / hours
        finally:
            conn.close()

    def get_recent_volume(self, platform, hours=1):
        """Get items per hour for platform in the last N hours."""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
            cursor.execute("""
                SELECT COUNT(*) FROM content_log
                WHERE platform = ? AND timestamp > ?
            """, (platform, cutoff))
            count = cursor.fetchone()[0]
            return count / hours if hours > 0 else 0.0
        finally:
            conn.close()

    def is_spike(self, platform, recent_hours=1):
        """
        True spike = recent volume rate > (baseline * SPIKE_MULTIPLIER).
        Returns (is_spike: bool, recent_rate: float, baseline_rate: float).
        """
        baseline = self.get_baseline_volume(platform)
        recent_rate = self.get_recent_volume(platform, recent_hours)
        if baseline <= 0:
            return False, recent_rate, baseline
        threshold = baseline * SPIKE_MULTIPLIER
        return recent_rate > threshold, recent_rate, baseline

    def log_spike(self, platform, title, spike_rate, baseline_rate):
        """Persist spike event for audit and analysis."""
        conn = self._get_conn()
        try:
            conn.execute("""
                INSERT INTO spikes (platform, title, spike_rate, baseline_rate)
                VALUES (?, ?, ?, ?)
            """, (platform, (title or "")[:500], spike_rate, baseline_rate))
            conn.commit()
        except Exception as e:
            pass  # Non-fatal; don't break the listener
        finally:
            conn.close()
