import time
import json
from threading import Lock

class GreenCache:
    """Thread-safe In-Memory TTL Cache for Green Computing (Exp. 15).
    Reduces redundant database reads and network load.
    """
    def __init__(self, default_ttl: int = 120):
        self._cache = {}
        self._lock = Lock()
        self.default_ttl = default_ttl
        
        # Green Software Metrics
        self.metrics = {
            "db_reads": 0,
            "db_writes": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "bytes_transferred": 0,
            "conventional_db_reads_estimated": 0
        }
        
    def get(self, key: str):
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self.metrics["cache_misses"] += 1
                return None
            val, expire_at = entry
            if time.time() > expire_at:
                del self._cache[key]
                self.metrics["cache_misses"] += 1
                return None
            self.metrics["cache_hits"] += 1
            return val
            
    def set(self, key: str, value, ttl: int = None):
        with self._lock:
            expire_at = time.time() + (ttl or self.default_ttl)
            self._cache[key] = (value, expire_at)
            
    def invalidate(self, key_prefix: str = None):
        with self._lock:
            if key_prefix is None:
                self._cache.clear()
            else:
                keys_to_del = [k for k in self._cache if k.startswith(key_prefix)]
                for k in keys_to_del:
                    del self._cache[k]
                    
    def record_db_read(self, count: int = 1):
        with self._lock:
            self.metrics["db_reads"] += count
            self.metrics["conventional_db_reads_estimated"] += count
            
    def record_db_write(self, count: int = 1):
        with self._lock:
            self.metrics["db_writes"] += count
            
    def record_transfer(self, byte_count: int):
        with self._lock:
            self.metrics["bytes_transferred"] += byte_count
            
    def get_metrics(self) -> dict:
        with self._lock:
            hits = self.metrics["cache_hits"]
            misses = self.metrics["cache_misses"]
            total_requests = hits + misses
            hit_ratio = round((hits / total_requests * 100), 2) if total_requests > 0 else 0.0
            
            # Conventional reads without green caching = DB reads + cache hits (since hits would have been DB reads)
            conv_reads = self.metrics["db_reads"] + hits
            reads_avoided = hits
            # Est. carbon factor: ~0.00015 g CO2 per DB query, ~0.00001 g CO2 per KB transfer
            carbon_avoided_mg = round(reads_avoided * 0.15, 3)
            
            return {
                "db_reads": self.metrics["db_reads"],
                "db_writes": self.metrics["db_writes"],
                "cache_hits": hits,
                "cache_misses": misses,
                "cache_hit_ratio_percent": hit_ratio,
                "conventional_db_reads": conv_reads,
                "db_reads_avoided": reads_avoided,
                "bytes_transferred": self.metrics["bytes_transferred"],
                "carbon_saved_estimated_mg": carbon_avoided_mg,
                "active_cached_keys": len(self._cache)
            }

green_cache = GreenCache(default_ttl=120)
