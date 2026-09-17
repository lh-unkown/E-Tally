import json
import os
import time
import urllib.request
import urllib.error
from datetime import datetime
import database

# External Main System (BTOS / Port Operating System) API Configuration
MAIN_SYSTEM_API_URL = os.environ.get("MAIN_SYSTEM_API_URL", "").strip()
MAIN_SYSTEM_API_KEY = os.environ.get("MAIN_SYSTEM_API_KEY", "").strip()
MAX_RETRIES = 5

def process_outbox_queue():
    """Reads pending sync events from sync_outbox and posts them to the Main System API."""
    if not MAIN_SYSTEM_API_URL:
        # If API URL is not configured yet, retain queue in DB without erroring out
        return {"processed": 0, "status": "MAIN_SYSTEM_API_URL not set"}

    conn = database.get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, event_type, vin, payload_json, retry_count 
            FROM sync_outbox 
            WHERE status IN ('PENDING', 'FAILED') AND retry_count < ? 
            ORDER BY id ASC LIMIT 20
        """, (MAX_RETRIES,))
        
        rows = cursor.fetchall()
        processed = 0
        success_count = 0

        for row in rows:
            event_id = row["id"]
            event_type = row["event_type"]
            vin = row["vin"]
            payload_str = row["payload_json"]
            retry_count = row["retry_count"]

            headers = {
                "Content-Type": "application/json",
                "User-Agent": "HIPG-eTally-SyncEngine/1.0"
            }
            if MAIN_SYSTEM_API_KEY:
                headers["Authorization"] = f"Bearer {MAIN_SYSTEM_API_KEY}"

            endpoint = f"{MAIN_SYSTEM_API_URL.rstrip('/')}/tally-events"
            data_bytes = payload_str.encode("utf-8")
            req = urllib.request.Request(endpoint, data=data_bytes, headers=headers, method="POST")

            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if 200 <= resp.status < 300:
                        cursor.execute("""
                            UPDATE sync_outbox 
                            SET status = 'SENT', synced_at = ?, last_error = NULL 
                            WHERE id = ?
                        """, (now_str, event_id))
                        success_count += 1
                    else:
                        cursor.execute("""
                            UPDATE sync_outbox 
                            SET status = 'FAILED', retry_count = retry_count + 1, last_error = ? 
                            WHERE id = ?
                        """, (f"HTTP {resp.status}", event_id))
            except Exception as e:
                cursor.execute("""
                    UPDATE sync_outbox 
                    SET status = 'FAILED', retry_count = retry_count + 1, last_error = ? 
                    WHERE id = ?
                """, (str(e), event_id))

            processed += 1

        conn.commit()
        return {"processed": processed, "synced": success_count}
    finally:
        conn.close()

def import_vessel_manifest(data):
    """Processes inbound manifest push from Main TOS System into e-Tally database."""
    conn = database.get_db()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        vessel = data.get("vessel", {})
        chassis_list = data.get("chassis_list", [])

        vessel_id = vessel.get("id", f"VSL{datetime.now().strftime('%H%M%S')}")
        vessel_name = vessel.get("name", "UNKNOWN VESSEL").strip()
        voyage = str(vessel.get("voyage", "1")).strip()
        berth = vessel.get("berth_no", "Berth 1").strip()
        arrival = vessel.get("arrival_date", datetime.now().strftime("%Y/%m/%d"))
        units = len(chassis_list)

        # Upsert vessel
        cursor.execute("SELECT id FROM vessels WHERE id = ?", (vessel_id,))
        if cursor.fetchone():
            cursor.execute("""
                UPDATE vessels SET name = ?, voyage = ?, berth_no = ?, arrival_date = ?, total_units = ? WHERE id = ?
            """, (vessel_name, voyage, berth, arrival, units, vessel_id))
        else:
            cursor.execute("""
                INSERT INTO vessels (id, name, voyage, berth_no, arrival_date, total_units, status) VALUES (?,?,?,?,?,?,'BERTHED')
            """, (vessel_id, vessel_name, voyage, berth, arrival, units))

        # Upsert chassis
        added_count = 0
        for item in chassis_list:
            vin = item.get("vin", "").strip().upper()
            if not vin or len(vin) < 6:
                continue
            last_6 = vin[-6:]
            model = item.get("model", "UNKNOWN").strip().upper()
            used = item.get("brand_new_used", "USED").upper()
            color = item.get("color", "White")
            deck = item.get("deck", "Deck 1")
            yard = item.get("yard", "Yard A")
            row_lane = item.get("row_lane", "Block 1-Row 1")
            iid = item.get("iid", f"ROV#{datetime.now().strftime('%M%S')}-01099")

            cursor.execute("SELECT vin FROM chassis WHERE vin = ?", (vin,))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO chassis (vin, last_6, vessel_id, model, brand_new_used, iid, color, deck, yard, row_lane, tally_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'No Tally')
                """, (vin, last_6, vessel_id, model, used, iid, color, deck, yard, row_lane))
                added_count += 1

        cursor.execute("""
            INSERT INTO audit_trail (vin, work_point, user_id, user_role, timestamp, details)
            VALUES (?, 'Main System Import', 'BTOS Sync Engine', 'System Integration', ?, ?)
        """, (vessel_id, now_str, f"Inbound manifest sync from Main TOS API: {added_count} new chassis added for Vessel {vessel_name} ({voyage})."))

        conn.commit()
        return {"success": True, "message": f"Successfully imported manifest for '{vessel_name}'. Added {added_count} chassis.", "vessel_id": vessel_id, "chassis_added": added_count}
    finally:
        conn.close()

if __name__ == "__main__":
    print("Running e-Tally Sync Engine outbox worker...")
    res = process_outbox_queue()
    print("Sync process result:", res)
