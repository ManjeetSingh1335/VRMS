import os
import sys
import time
import json

# Ensure application package is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.models.entities import db, Vehicle, Booking
from app.services.vehicle_db import VehicleDB
from app.services.green_cache import green_cache

def run_green_software_benchmark():
    print("=" * 80)
    print("GREEN SOFTWARE COMPUTING BENCHMARK")
    print("  Vehicle Rental Management System (VRMS)")
    print("=" * 80)
    
    app = create_app()
    with app.app_context():
        # Ensure some vehicles exist
        vehicles = Vehicle.query.all()
        if not vehicles:
            print("No vehicles found in database. Run seed script first.")
            return

        iterations = 100
        print(f"\nSimulating {iterations} repeated search and lookup requests...\n")
        
        # 1. Conventional Approach (No Caching, Full Column Selection)
        print("[1/2] Executing Conventional Mode (Direct DB queries, full object hydration)...")
        conv_start_time = time.time()
        conv_db_reads = 0
        conv_bytes = 0
        
        for i in range(iterations):
            # Direct uncached queries
            for v in vehicles[:5]:
                veh = Vehicle.query.filter_by(Vehicle_ID=v.Vehicle_ID).first()
                conv_db_reads += 1
                serialized = json.dumps(veh.to_dict(full=True))
                conv_bytes += len(serialized.encode("utf-8"))
                
        conv_duration = time.time() - conv_start_time
        
        # 2. Green Optimized Approach (TTL In-Memory Cache + Selective Field Projection)
        print("[2/2] Executing Green Optimized Mode (In-memory TTL cache + selective projection)...")
        green_cache.invalidate()
        green_cache.metrics = {
            "db_reads": 0, "db_writes": 0, "cache_hits": 0,
            "cache_misses": 0, "bytes_transferred": 0, "conventional_db_reads_estimated": 0
        }
        
        green_start_time = time.time()
        green_bytes = 0
        
        for i in range(iterations):
            for v in vehicles[:5]:
                # Selective field projection & caching
                cached_data = green_cache.get(f"vehicle_proj:{v.Vehicle_ID}")
                if cached_data is None:
                    veh = Vehicle.query.filter_by(Vehicle_ID=v.Vehicle_ID).first()
                    green_cache.record_db_read(1)
                    cached_data = veh.to_dict(full=False) # Selective projection (saves ~45% bytes)
                    green_cache.set(f"vehicle_proj:{v.Vehicle_ID}", cached_data, ttl=60)
                
                serialized = json.dumps(cached_data)
                green_bytes += len(serialized.encode("utf-8"))
                
        green_duration = time.time() - green_start_time
        metrics = green_cache.get_metrics()
        
        # Compute improvements
        db_read_reduction = ((conv_db_reads - metrics["db_reads"]) / conv_db_reads) * 100
        time_reduction = ((conv_duration - green_duration) / conv_duration) * 100
        byte_reduction = ((conv_bytes - green_bytes) / conv_bytes) * 100
        carbon_conv_mg = round(conv_db_reads * 0.15 + (conv_bytes / 1024) * 0.01, 3)
        carbon_green_mg = round(metrics["db_reads"] * 0.15 + (green_bytes / 1024) * 0.01, 3)
        carbon_saved_mg = round(carbon_conv_mg - carbon_green_mg, 3)
        
        # Display Comparative Results
        print("\n" + "=" * 80)
        print("                  GREEN COMPUTING COMPARATIVE BENCHMARK")
        print("=" * 80)
        print(f"{'Metric':<30} | {'Conventional':<18} | {'Green Optimized':<18} | {'Improvement'}")
        print("-" * 80)
        print(f"{'Total DB Reads':<30} | {conv_db_reads:<18} | {metrics['db_reads']:<18} | {db_read_reduction:.1f}% reduction")
        print(f"{'Cache Hits':<30} | {'0 (0%)':<18} | {metrics['cache_hits']:<18} | {metrics['cache_hit_ratio_percent']:.1f}% hit ratio")
        print(f"{'Data Transferred (KB)':<30} | {conv_bytes / 1024:<18.2f} | {green_bytes / 1024:<18.2f} | {byte_reduction:.1f}% reduced")
        print(f"{'Execution Time (s)':<30} | {conv_duration:<18.3f} | {green_duration:<18.3f} | {time_reduction:.1f}% faster")
        print(f"{'Est. Carbon Footprint (mg)':<30} | {carbon_conv_mg:<18.3f} | {carbon_green_mg:<18.3f} | {carbon_saved_mg:.3f} mg CO2 saved")
        print("=" * 80)
        print(f"\nConclusion: Green architecture avoided {metrics['cache_hits']} redundant database hits,")
        print(f"reduced data transfer by {byte_reduction:.1f}%, and delivered a {time_reduction:.1f}% speedup.\n")

if __name__ == "__main__":
    run_green_software_benchmark()
